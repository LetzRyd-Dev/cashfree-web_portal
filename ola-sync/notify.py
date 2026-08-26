"""
notify.py
=========
Stage 4 of the Ola sync pipeline — send alerts on success or failure.

Currently supports:
- Slack webhook  (set OLA_SLACK_WEBHOOK in .env)
- Console print  (always on, good default)

If OLA_SLACK_WEBHOOK is not set, Slack notifications are silently skipped and
the pipeline still completes successfully.
"""

import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

import requests

# ── Load .env ──────────────────────────────────────────────────────────────────
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

SLACK_WEBHOOK = os.environ.get("OLA_SLACK_WEBHOOK", "")
SMTP_HOST     = os.environ.get("SMTP_HOST",     "smtp.gmail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER     = os.environ.get("SMTP_USER",     "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
ALERT_TO      = os.environ.get("ALERT_TO_EMAIL", "")



def _send_email(subject: str, body: str):
    """Send an SMTP email alert."""
    if not SMTP_USER or not SMTP_PASSWORD or not ALERT_TO:
        print("[NOTIFY] Email credentials missing — skipping SMTP email alert.")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = ALERT_TO
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [ALERT_TO], msg.as_string())
        print(f"[NOTIFY] ✓ Email alert sent to {ALERT_TO}: '{subject}'")
    except Exception as e:
        print(f"[NOTIFY] SMTP email sending failed: {e}")


def _post_slack(text: str):
    """Post a plain-text message to the configured Slack webhook."""
    if not SLACK_WEBHOOK:
        return
    try:
        resp = requests.post(
            SLACK_WEBHOOK,
            data=json.dumps({"text": text}),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code != 200:
            print(f"[NOTIFY] Slack returned {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[NOTIFY] Slack post failed: {e}")


def notify_success(week_start, week_end, stats: dict, recovered: bool = False):
    """
    Send a success notification.
    If recovered=True, sends an SMTP recovery email confirming that the pipeline retried and succeeded.
    If recovered=False (1st try success), email is skipped to avoid inbox clutter.
    """
    ws = str(week_start) if week_start else "?"
    we = str(week_end)   if week_end   else "?"
    msg = (
        f"✅ Ola Sync Complete — Week {ws} → {we}\n"
        f"Raw: {stats.get('inserted_raw', 0)} inserted, {stats.get('updated_raw', 0)} updated\n"
        f"Incentive: {stats.get('inserted_incentive', 0)} inserted, {stats.get('updated_incentive', 0)} updated\n"
        f"Weekly Summary: {stats.get('inserted_summary', 0)} inserted, {stats.get('updated_summary', 0)} updated"
    )
    print(f"[NOTIFY] {msg}")
    _post_slack(msg)

    # Smart email rule: Only send success email if previous failure occurred and was recovered
    if recovered:
        email_subject = f"✅ [RECOVERED] Ola Sync Pipeline Succeeded after Retry (Week {ws} → {we})"
        email_body = (
            f"Hello Team,\n\n"
            f"The Ola Sync Pipeline encountered an initial issue, retried, and HAS SUCCESSFULLY RECOVERED!\n\n"
            f"Details:\n"
            f"• Statement Window: {ws} → {we}\n"
            f"• Raw Records: {stats.get('inserted_raw', 0)} inserted, {stats.get('updated_raw', 0)} updated\n"
            f"• Incentive Records: {stats.get('inserted_incentive', 0)} inserted, {stats.get('updated_incentive', 0)} updated\n"
            f"• Weekly Summary Records: {stats.get('inserted_summary', 0)} inserted, {stats.get('updated_summary', 0)} updated\n\n"
            f"Database tables have been updated successfully.\n\n"
            f"LetzRyd Automation Worker"
        )
        _send_email(email_subject, email_body)


def notify_failure(week_start, week_end, error: str, stage: str = "", retry_status: str = ""):
    """
    Send a failure alert via console, Slack, and immediate SMTP email.
    """
    ws = str(week_start) if week_start else "?"
    we = str(week_end)   if week_end   else "?"
    msg = (
        f"🚨 Ola Sync FAILED (stage: {stage or 'unknown'}) — Week {ws} → {we}\n"
        f"Error: {error[:500]}\n"
        f"Status: {retry_status or 'Action needed'}"
    )
    print(f"[NOTIFY] {msg}")
    _post_slack(msg)

    email_subject = f"🚨 [ALERT] Ola Sync Pipeline FAILED at Stage '{stage or 'unknown'}'"
    email_body = (
        f"Hello Team,\n\n"
        f"The Ola Sync Pipeline encountered an error during execution:\n\n"
        f"• Stage Failed: {stage or 'unknown'}\n"
        f"• Statement Window: {ws} → {we}\n"
        f"• Error Message: {error}\n"
        f"• Retry Status: {retry_status or 'Retrying / Max retries reached'}\n\n"
        f"Please check Cloud Run / worker logs if manual intervention is needed.\n\n"
        f"LetzRyd Automation Worker"
    )
    _send_email(email_subject, email_body)

