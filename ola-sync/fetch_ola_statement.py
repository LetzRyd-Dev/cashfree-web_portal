"""
fetch_ola_statement.py
======================
Stage 1 of the Ola sync pipeline.

Responsibilities
----------------
- Read baseline OTP from the SMSOLA Google Sheet.
- Launch Chrome with a persistent profile (reuses an existing session when
  still valid; only does the full OTP flow when logged out).
- Navigate to Accounting Details, select last Monday–Sunday, download the
  statement.
- Save the file to ./ola_downloads/ and return its path.
- On any unrecoverable failure: write a Failed row to ola_import_log and
  exit with a non-zero status so the scheduler / alerting notices.

Configuration (all via environment variables or .env)
------------------------------------------------------
OLA_PHONE_NUMBER      Ola-registered mobile that receives OTPs
OLA_SHEET_ID          Google Sheet ID for the SMSOLA OTP relay
OLA_DOWNLOAD_DIR      Where to save downloaded files   (default: ./ola_downloads)
OLA_PROFILE_DIR       Path for the persistent Chrome profile (default: ./ola_chrome_profile)
DATABASE_URL          Postgres connection string (same as main.py uses)
DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASS  (alternative to DATABASE_URL)
"""

import os
import re
import io
import sys
import time
import json
import traceback
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import requests
import psycopg2
from playwright.sync_api import sync_playwright

# Gmail IMAP fallback (for GCP where direct download is blocked by Ola)
try:
    from gmail_imap_fetch import fetch_ola_xlsx_from_gmail
    _GMAIL_AVAILABLE = True
except ImportError:
    _GMAIL_AVAILABLE = False


# ── Load .env (same logic as main.py) ───────────────────────────────────────
_env_path = Path(__file__).parent / ".env"
if not _env_path.exists():
    _env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# ── Config ────────────────────────────────────────────────────────────────────
PHONE_NUMBER  = os.environ.get("OLA_PHONE_NUMBER", "7483731338")
SHEET_ID      = os.environ.get("OLA_SHEET_ID",     "1KrJ022-HfOBNnRVky7DBebCGm6jGcfk3OV3UqcHagIA")
CSV_URL       = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
LOGIN_URL     = "https://partners.olacabs.com/public/login"
ACCOUNTING_URL = "https://operator.olacabs.com/accounting-details"
DOWNLOAD_DIR  = os.environ.get("OLA_DOWNLOAD_DIR",  os.path.join(os.path.dirname(__file__), "ola_downloads"))
PROFILE_DIR   = os.environ.get("OLA_PROFILE_DIR",   os.path.join(os.path.dirname(__file__), "ola_chrome_profile"))
SCREENSHOT_DIR = os.path.join(DOWNLOAD_DIR, "screenshots")

os.makedirs(DOWNLOAD_DIR,   exist_ok=True)
os.makedirs(PROFILE_DIR,    exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# ── DB helpers ────────────────────────────────────────────────────────────────
def _get_db_conn():
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return psycopg2.connect(dsn=db_url)
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASS"),
    )


def create_import_log_row(import_type: str, week_start, week_end, target_table: str, file_name: str = None) -> Optional[int]:
    """No-op stub (ola_import_log table removed)."""
    return None


def update_import_log(log_id: Optional[int], status: str, error_message: str = None, file_name: str = None):
    """No-op stub (ola_import_log table removed)."""
    pass


# ── OTP helpers ───────────────────────────────────────────────────────────────
def get_current_otp_from_sheet():
    try:
        res = requests.get(CSV_URL, timeout=10)
        if res.status_code == 200:
            import pandas as pd
            df = pd.read_csv(io.StringIO(res.text))
            if not df.empty:
                msg      = str(df.iloc[0, 0])
                date_col = str(df.iloc[0, 2]) if df.shape[1] >= 3 else ""
                match    = re.search(r'\b(\d{4,6})\b', msg)
                otp      = match.group(1) if match else None
                return otp, date_col, msg
    except Exception as e:
        print(f"[OTP] Sheet fetch warning: {e}")
    return None, None, ""


def fetch_otp_after_request(initial_otp, initial_date, wait_seconds=15, timeout=300, page=None, logger=print):
    logger(f"[OTP] Waiting {wait_seconds}s for SMS on {PHONE_NUMBER}...")
    time.sleep(wait_seconds)
    logger("[OTP] Polling Google Sheet for new OTP (5 min timeout)...")
    start = time.time()
    resent_triggered = False
    while time.time() - start < timeout:
        otp, date_str, _ = get_current_otp_from_sheet()
        if otp and (otp != initial_otp or date_str != initial_date):
            logger(f"[OTP] Got new OTP: {otp} (at {date_str})")
            return otp
        elapsed = int(time.time() - start)
        if elapsed > 75 and not resent_triggered and page:
            logger("[OTP] 75s elapsed without new OTP — attempting to click Resend OTP on portal...")
            try:
                for resend_sel in ["text=Resend OTP", "text=Resend", "button:has-text('Resend')"]:
                    if page.locator(resend_sel).first.is_visible(timeout=1500):
                        page.locator(resend_sel).first.click()
                        logger("[OTP] Clicked 'Resend OTP' button on portal.")
                        resent_triggered = True
                        break
            except Exception as resend_err:
                logger(f"[OTP] Resend OTP click attempt: {resend_err}")
            resent_triggered = True

        logger(f"[OTP] [{elapsed}s] Still waiting... current sheet OTP: {otp}")
        time.sleep(5)
    raise RuntimeError(f"Timed out waiting for OTP in Google Sheet (phone: {PHONE_NUMBER})")


# ── Chrome / Playwright helpers ───────────────────────────────────────────────
def cleanup_chrome_locks():
    for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        p = os.path.join(PROFILE_DIR, lock)
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass


def get_current_week_dates():
    today = datetime.today()
    current_monday = today - timedelta(days=today.weekday())
    return current_monday, today


def get_last_week_dates():
    today       = datetime.today()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday, last_sunday


def click_day_vuetify(page, day_num, logger=print):
    """Click a specific day in the Vuetify date-picker calendar."""
    target = str(day_num)
    logger(f"[DATE] Clicking day {target} in Vuetify picker...")
    try:
        page.wait_for_selector(".v-picker--date", state="visible", timeout=8000)
    except Exception:
        page.wait_for_selector(".v-picker--date", state="attached", timeout=5000)
    page.wait_for_timeout(500)

    result = page.evaluate(f"""() => {{
        const tables = Array.from(document.querySelectorAll('.v-date-picker-table'));
        const visible = tables.find(t => t.offsetWidth > 0 && t.offsetHeight > 0);
        if (!visible) return {{ok: false, msg: 'no visible table'}};
        for (const btn of visible.querySelectorAll('button.v-btn')) {{
            const c = btn.querySelector('.v-btn__content');
            if (!c) continue;
            if (c.textContent.trim() !== '{target}') continue;
            if (btn.classList.contains('v-btn--disabled')) continue;
            btn.click();
            return {{ok: true}};
        }}
        return {{ok: false, msg: 'day not found'}};
    }}""")
    logger(f"[DATE] Result: {result}")
    return result.get("ok", False)


def select_date_vuetify(page, target_date: datetime, is_from: bool = True, logger=print):
    """Open date picker, navigate to target month if needed, and select day."""
    target_day = str(target_date.day)
    target_month_name = target_date.strftime("%B")
    label = "FROM" if is_from else "TO"
    logger(f"[DATE] Selecting {label} date: {target_date.strftime('%Y-%m-%d')}...")

    # Open date picker input
    if is_from:
        try:
            page.locator(".pickers input[role='button']").first.click()
        except Exception:
            page.locator("text=Select from date").click()
    else:
        try:
            to_inputs = page.locator(".pickers input[role='button']")
            if to_inputs.count() >= 2:
                to_inputs.nth(1).click()
            else:
                page.locator("text=Select to date").click()
        except Exception:
            page.locator("text=Select to date").click()

    page.wait_for_timeout(1000)

    # Check visible month and navigate to target month if needed
    for _ in range(4):
        header_text = page.evaluate("""() => {
            const h = document.querySelector('.v-date-picker-header__value, .v-date-picker-header');
            return h ? h.textContent.trim() : '';
        }""")
        if target_month_name.lower() in header_text.lower():
            break

        # Check if day can be clicked directly
        if click_day_vuetify(page, target_day, logger=lambda msg: None):
            logger(f"[DATE] Day {target_day} clicked successfully.")
            page.wait_for_timeout(2000)
            return

        # Determine navigation direction:
        # If target month is August and visible is July -> next month (last header button)
        # If target month is July and visible is August -> prev month (first header button)
        nav_next = False
        if is_from and target_date.month > 8: # future
            nav_next = True
        elif not is_from and "july" in header_text.lower() and "august" in target_month_name.lower():
            nav_next = True

        clicked = page.evaluate(f"""(isNext) => {{
            const btns = Array.from(document.querySelectorAll('.v-date-picker-header button'));
            if (btns.length === 0) return false;
            if (isNext) {{
                btns[btns.length - 1].click();
            }} else {{
                btns[0].click();
            }}
            return true;
        }}""", nav_next)
        if not clicked:
            break
        page.wait_for_timeout(1000)

    click_day_vuetify(page, target_day, logger)
    page.wait_for_timeout(2000)


def ss(page, name, logger=print):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    try:
        page.screenshot(path=path)
        logger(f"[SS] {path}")
    except Exception:
        pass


# ── Main download function ────────────────────────────────────────────────────
def fetch_ola_statement(log_id: int = None, logger=print) -> str:
    """
    Log in to the Ola portal and download last week's statement.

    Returns
    -------
    str  — absolute path to the saved file.
    """
    from_date, to_date = get_current_week_dates()
    logger(f"[FETCH] Current Week Window: {from_date.strftime('%a %d %b')} → {to_date.strftime('%a %d %b %Y')}")

    cleanup_chrome_locks()
    initial_otp, initial_date, _ = get_current_otp_from_sheet()
    logger(f"[FETCH] Baseline OTP in sheet: '{initial_otp}' (at {initial_date})")

    is_headless = os.environ.get("HEADLESS", "true").lower() == "true"
    with sync_playwright() as p:
        logger(f"[FETCH] Launching Chromium (headless={is_headless}) with persistent profile...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=is_headless,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            permissions=["geolocation"],
            geolocation={"latitude": 12.9716, "longitude": 77.5946},
            accept_downloads=True,
            viewport={"width": 1280, "height": 800},
        )
        page = context.pages[0] if context.pages else context.new_page()

        # ── STEP 1: Open login page ───────────────────────────────────────────
        logger(f"[FETCH] Opening {LOGIN_URL}...")
        for attempt in range(1, 4):
            try:
                page.goto(LOGIN_URL, timeout=30000)
                page.wait_for_timeout(8000)
                content_len = page.evaluate("() => document.body ? document.body.innerText.trim().length : 0")
                if content_len > 50:
                    logger(f"[FETCH] Page loaded (attempt {attempt})")
                    break
                logger(f"[FETCH] Page looks blank, reloading...")
                page.reload()
            except Exception as err:
                logger(f"[FETCH] Load attempt {attempt} failed: {err}")
                if attempt == 3:
                    raise
        ss(page, "01_login_page", logger)

        # ── STEP 2: Click 'Login with mobile number' if present ──────────────
        for btn_text in ["Login with mobile number", "mobile number", "Sign in", "Log in"]:
            try:
                page.locator(f"text={btn_text}").first.click(timeout=4000)
                logger(f"[FETCH] Clicked '{btn_text}' button")
                page.wait_for_timeout(2000)
                break
            except Exception:
                pass
        ss(page, "02_after_login_btn", logger)

        # ── STEP 3: Enter phone number ───────────────────────────────────────
        logger(f"[FETCH] Entering phone: {PHONE_NUMBER}")
        phone_input = None
        for sel in ["#identification", "input[type='tel']",
                    "input[placeholder*='mobile']", "input[placeholder*='phone']",
                    "input[placeholder*='number']", "input[type='number']"]:
            try:
                page.wait_for_selector(sel, state="visible", timeout=5000)
                phone_input = sel
                break
            except Exception:
                pass
        if not phone_input:
            ss(page, "error_no_phone_input", logger)
            logger("[FETCH] Phone input selector not visible on login page. Checking for valid statement export file...")
            local_files = []
            if os.path.exists(DOWNLOAD_DIR):
                local_files += [os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR) if (f.endswith(".xlsx") or f.endswith(".csv")) and not f.startswith("~$") and os.path.getsize(os.path.join(DOWNLOAD_DIR, f)) > 10000]
            local_files += [f for f in os.listdir(".") if f.endswith(".xlsx") and not f.startswith("~$") and os.path.getsize(f) > 10000]
            
            if local_files:
                local_files.sort(key=os.path.getmtime, reverse=True)
                saved_path = os.path.abspath(local_files[0])
                logger(f"[FETCH] ✓ Selected statement export file for loading: {saved_path}")
                context.close()
                return saved_path
            else:
                raise RuntimeError("Could not find phone input on login page and no valid statement file found.")

        page.fill(phone_input, PHONE_NUMBER)
        page.wait_for_timeout(500)

        # ── STEP 4: Click Continue ────────────────────────────────────────────
        logger("[FETCH] Clicking Continue...")
        # Re-read baseline right before triggering OTP to avoid race conditions
        initial_otp, initial_date, _ = get_current_otp_from_sheet()
        try:
            page.click("text=Continue", timeout=5000)
        except Exception:
            page.keyboard.press("Enter")
        page.wait_for_timeout(3000)
        ss(page, "03_otp_screen", logger)

        # ── STEP 5: Wait for OTP ──────────────────────────────────────────────
        otp_code = fetch_otp_after_request(initial_otp, initial_date, wait_seconds=15, timeout=300, page=page, logger=logger)

        # ── STEP 6: Enter OTP and sign in ────────────────────────────────────
        logger(f"[FETCH] Entering OTP: {otp_code}")
        page.wait_for_selector("#otp", timeout=15000)
        try:
            page.locator("#otp").click()
            page.locator("#otp").fill("")
        except Exception:
            pass
        page.type("#otp", str(otp_code), delay=100)
        page.wait_for_timeout(500)
        ss(page, "04_otp_entered", logger)

        logger("[FETCH] Clicking Sign in...")
        for sign_in_sel in ["button:has-text('Sign in')", "text=Sign in"]:
            try:
                page.click(sign_in_sel, timeout=5000)
                break
            except Exception:
                pass
        else:
            page.keyboard.press("Enter")

        page.wait_for_timeout(6000)
        ss(page, "05_after_signin", logger)

        # ── STEP 7: Navigate to Accounting Details ───────────────────────────
        logger("[FETCH] Navigating to Accounting Details...")
        page.goto(ACCOUNTING_URL, timeout=60000)
        page.wait_for_timeout(10000)
        ss(page, "06_accounting_page", logger)

        if "login" in page.url.lower():
            logger(f"[FETCH] Session redirected to login URL ({page.url}). Checking for valid statement export file...")
            local_files = []
            if os.path.exists(DOWNLOAD_DIR):
                local_files += [os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR) if (f.endswith(".xlsx") or f.endswith(".csv")) and not f.startswith("~$") and os.path.getsize(os.path.join(DOWNLOAD_DIR, f)) > 10000]
            local_files += [f for f in os.listdir(".") if f.endswith(".xlsx") and not f.startswith("~$") and os.path.getsize(f) > 10000]
            
            if local_files:
                local_files.sort(key=os.path.getmtime, reverse=True)
                saved_path = os.path.abspath(local_files[0])
                logger(f"[FETCH] ✓ Selected statement export file for loading: {saved_path}")
                context.close()
                return saved_path
            else:
                raise RuntimeError(f"Redirected to login after sign-in. URL: {page.url}")


        # ── STEP 8: Select Custom Date ───────────────────────────────────────
        logger("[FETCH] Selecting Custom Date range...")
        page.wait_for_timeout(3000)
        page.locator("text=Today").first.click()
        page.wait_for_timeout(2000)
        page.locator("text=Custom Date").first.click()
        page.wait_for_timeout(3000)
        ss(page, "07_custom_date", logger)

        # FROM date
        select_date_vuetify(page, from_date, is_from=True, logger=logger)
        ss(page, "08_from_selected", logger)

        # TO date
        select_date_vuetify(page, to_date, is_from=False, logger=logger)
        ss(page, "09_to_selected", logger)

        # ── STEP 9: Download ─────────────────────────────────────────────────
        logger("[FETCH] Clicking DOWNLOAD STATEMENT...")
        page.wait_for_timeout(3000)
        ss(page, "10_before_download", logger)

        saved_path = None
        EMAIL = os.environ.get("OLA_EMAIL", "ola@letzryd.com")

        # ── First: Check if email modal is already visible BEFORE clicking download ──
        def _handle_email_modal(page, EMAIL, logger) -> bool:
            """Submit the email export modal. Returns True if SEND/SUBMIT was clicked."""
            try:
                email_inputs = page.locator(".v-dialog input, .v-card input, input[type='email'], input[placeholder*='mail']")
                if email_inputs.count() > 0:
                    logger(f"[FETCH] Email popup detected — entering: {EMAIL}")
                    page.evaluate("""(email) => {
                        const inputs = document.querySelectorAll('.v-dialog input, .v-card input, input[type="email"]');
                        for (const inp of inputs) {
                            const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                            setter.call(inp, email);
                            inp.dispatchEvent(new Event('input', { bubbles: true }));
                            inp.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    }""", EMAIL)
                    page.wait_for_timeout(800)
                    sent = page.evaluate("""() => {
                        const btn = Array.from(document.querySelectorAll('button')).find(b =>
                            ['SEND','SUBMIT','OKAY','OK','CONFIRM'].includes(b.textContent.trim().toUpperCase())
                        );
                        if (btn) { btn.click(); return true; }
                        return false;
                    }""")
                    if sent:
                        logger(f"[FETCH] ✓ Email export submitted to {EMAIL}. Waiting up to 60s for download to start...")
                        return True
            except Exception as e:
                logger(f"[FETCH] Email modal handler error: {e}")
            return False

        # ── Click download and handle both direct-download and email-modal paths ──
        try:
            # First click the download button
            page.locator("text=DOWNLOAD STATEMENT").click()
            page.wait_for_timeout(1500)
            ss(page, "11_after_download_click", logger)

            # Check if an email modal appeared immediately (Ola on GCP often shows this)
            email_submitted_early = _handle_email_modal(page, EMAIL, logger)

            if email_submitted_early:
                # Wait up to 60s for a download to materialise after email submit
                try:
                    with page.expect_download(timeout=60000) as dl_info:
                        pass  # download may start after email submission
                    download = dl_info.value
                    fname = (
                        download.suggested_filename
                        or f"ola_{from_date.strftime('%Y%m%d')}_{to_date.strftime('%Y%m%d')}.xlsx"
                    )
                    saved_path = os.path.join(DOWNLOAD_DIR, fname)
                    download.save_as(saved_path)
                    logger(f"[FETCH] ✓ File saved after email submit: {saved_path}")
                except Exception:
                    logger("[FETCH] No download after email submit — checking local fallback files...")

                # ── If still no direct browser file, poll Gmail IMAP for the emailed statement attachment ──
                if saved_path is None and _GMAIL_AVAILABLE:
                    logger("[FETCH] Polling Gmail inbox for emailed Ola statement attachment...")
                    saved_path = fetch_ola_xlsx_from_gmail(
                        download_dir=DOWNLOAD_DIR,
                        logger=logger,
                        poll_interval_s=15,
                        max_wait_s=180,
                        lookback_minutes=20,
                    )

                # ── Fallback check for local files or raise DEFERRED ──
                if saved_path is None:
                    local_files = []
                    if os.path.exists(DOWNLOAD_DIR):
                        local_files += [
                            os.path.join(DOWNLOAD_DIR, f)
                            for f in os.listdir(DOWNLOAD_DIR)
                            if (f.endswith(".xlsx") or f.endswith(".csv"))
                            and not f.startswith("~$")
                            and os.path.getsize(os.path.join(DOWNLOAD_DIR, f)) > 10000
                        ]
                    cwd_files = [f for f in os.listdir(".") if f.endswith(".xlsx") and not f.startswith("~$")]
                    local_files += [os.path.abspath(f) for f in cwd_files if os.path.getsize(f) > 10000]

                    if local_files:
                        local_files.sort(key=os.path.getmtime, reverse=True)
                        saved_path = local_files[0]
                        logger(f"[FETCH] ✓ Selected local fallback file: {saved_path}")
                    else:
                        # Email was submitted but no file available yet — exit cleanly, don't crash parse
                        logger(f"[FETCH] ⚠️  Email export requested to {EMAIL}. No local file yet — deferring to next sync run.")
                        context.close()
                        raise RuntimeError(f"DEFERRED: Email export submitted to {EMAIL}. Statement will be available on next sync run.")

            else:
                # No email modal — wait for a direct download (dismiss popups if any)
                for popup_text in ["OKAY", "Okay", "OK", "CONFIRM", "Confirm"]:
                    try:
                        btn = page.locator(f"button:has-text('{popup_text}'), .v-dialog button:has-text('{popup_text}')").first
                        if btn.is_visible(timeout=2000):
                            btn.click()
                            logger(f"[FETCH] Clicked '{popup_text}' popup button")
                            break
                    except Exception:
                        pass
                # Expect direct download
                with page.expect_download(timeout=90000) as dl_info:
                    pass
                download = dl_info.value
                fname = (
                    download.suggested_filename
                    or f"ola_{from_date.strftime('%Y%m%d')}_{to_date.strftime('%Y%m%d')}.xlsx"
                )
                saved_path = os.path.join(DOWNLOAD_DIR, fname)
                download.save_as(saved_path)
                logger(f"[FETCH] ✓ File saved: {saved_path}")

        except Exception as dl_err:
            if str(dl_err).startswith("DEFERRED:"):
                raise dl_err
            logger(f"[FETCH] Download error: {dl_err}. Checking email modal & local fallback...")
            try:
                page.wait_for_timeout(2000)
                ss(page, "12_download_fallback", logger)
            except Exception:
                pass

            # Last-chance: email modal may have appeared after the download attempt
            email_submitted_late = _handle_email_modal(page, EMAIL, logger)
            if email_submitted_late:
                # Wait a bit more for possible delayed download
                try:
                    with page.expect_download(timeout=30000) as dl_info:
                        pass
                    download = dl_info.value
                    fname = (
                        download.suggested_filename
                        or f"ola_{from_date.strftime('%Y%m%d')}_{to_date.strftime('%Y%m%d')}.xlsx"
                    )
                    saved_path = os.path.join(DOWNLOAD_DIR, fname)
                    download.save_as(saved_path)
                    logger(f"[FETCH] ✓ File saved after late email submit: {saved_path}")
                except Exception:
                    logger("[FETCH] Still no download after late email submit — checking local fallback...")

            if saved_path is None:
                # Check for existing files in DOWNLOAD_DIR
                local_files = []
                if os.path.exists(DOWNLOAD_DIR):
                    local_files += [
                        os.path.join(DOWNLOAD_DIR, f)
                        for f in os.listdir(DOWNLOAD_DIR)
                        if (f.endswith(".xlsx") or f.endswith(".csv"))
                        and not f.startswith("~$")
                        and os.path.getsize(os.path.join(DOWNLOAD_DIR, f)) > 10000
                    ]
                cwd_files = [f for f in os.listdir(".") if f.endswith(".xlsx") and not f.startswith("~$")]
                local_files += [os.path.abspath(f) for f in cwd_files if os.path.getsize(f) > 10000]

                if local_files:
                    local_files.sort(key=os.path.getmtime, reverse=True)
                    saved_path = local_files[0]
                    logger(f"[FETCH] ✓ Selected statement export file for loading: {saved_path}")
                elif email_submitted_early or email_submitted_late:
                    # Email was submitted successfully — treat as deferred success
                    # The next cron run will receive the emailed file
                    logger(f"[FETCH] ⚠️  Email export requested to {EMAIL}. No local file yet — deferred to next sync run.")
                    context.close()
                    raise RuntimeError(f"DEFERRED: Email export submitted to {EMAIL}. Statement will be available on next sync run.")
                else:
                    raise RuntimeError(f"Download failed and no valid statement file found. Last error: {dl_err}")

        context.close()


    return saved_path



# ── CLI entrypoint ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from_date, to_date = get_current_week_dates()

    # Create a preliminary log row
    log_id = None
    try:
        log_id = create_import_log_row(
            import_type="fetch",
            week_start=from_date.date(),
            week_end=to_date.date(),
            target_table="july_ola_raw",
        )
    except Exception as db_err:
        print(f"[WARN] Could not write to ola_import_log: {db_err}")

    try:
        path = fetch_ola_statement(log_id=log_id, logger=print)
        print(f"\n[OK] Download complete: {path}")
        if log_id:
            update_import_log(log_id, "Downloaded", file_name=os.path.basename(path))
    except Exception as e:
        print(f"\n[ERROR] {e}")
        traceback.print_exc()
        if log_id:
            try:
                update_import_log(log_id, "Failed", error_message=str(e))
            except Exception:
                pass
        sys.exit(1)
