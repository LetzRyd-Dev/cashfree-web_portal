"""
run_pipeline.py
===============
Orchestrator for the Ola sync pipeline.

Runs the four stages in sequence:
  1. fetch_ola_statement  → login + download
  2. parse_ola_statement  → normalize columns
  3. load_to_postgres     → upsert into DB
  4. notify               → Slack / console

A failure in any stage writes a Failed row to ola_import_log and sends an
alert, then exits non-zero so Task Scheduler / cron notices.

Usage
-----
    python run_pipeline.py

    # Dry-run parse/load only (skip Playwright — useful when you already have a file):
    python run_pipeline.py --file path/to/already_downloaded.xlsx
"""

import argparse
import os
import sys
import traceback
import time
from datetime import date, datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

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

# ── Local imports (after env is loaded) ───────────────────────────────────────
from fetch_ola_statement import (
    fetch_ola_statement,
    get_current_week_dates,
)
from parse_ola_statement import parse_statement
from load_to_postgres import load_to_postgres
from notify import notify_success, notify_failure


def main():
    parser = argparse.ArgumentParser(description="Ola sync pipeline orchestrator")
    parser.add_argument(
        "--file", "-f",
        default=None,
        help="Skip the fetch stage and use this already-downloaded file instead."
    )
    args = parser.parse_args()

    from_date, to_date = get_current_week_dates()
    week_start: date = from_date.date()
    week_end:   date = to_date.date()

    print("=" * 60)
    print(f"Ola Sync Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current Week Window: {week_start} -> {week_end}")
    print("=" * 60)

    max_attempts = 2 if not args.file else 1
    recovered_flag = False

    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            print(f"\n[PIPELINE] 🔄 RETRY ATTEMPT {attempt}/{max_attempts}...")
            recovered_flag = True

        # ── Stage 1: Fetch (skip if --file given) ─────────────────────────
        if args.file:
            downloaded_file = args.file
            print(f"[PIPELINE] Skipping fetch — using file: {downloaded_file}")
        else:
            print(f"\n── STAGE 1: Fetch (Attempt {attempt}) ──")
            try:
                downloaded_file = fetch_ola_statement(logger=print)
                print(f"[PIPELINE] ✓ Fetch done: {downloaded_file}")
            except Exception as e:
                err = str(e)
                # DEFERRED means the email export was submitted — not a real failure
                if err.startswith("DEFERRED:"):
                    print(f"[PIPELINE] ⚠️  {err}")
                    print(f"[PIPELINE] Email export submitted — skipping pipeline. Next cron will pick up the file.")
                    sys.exit(0)
                print(f"[PIPELINE] ✗ Fetch failed on attempt {attempt}: {err}")
                traceback.print_exc()
                if attempt == max_attempts:
                    notify_failure(week_start, week_end, err, stage="fetch", retry_status="Max retries reached")
                    sys.exit(1)
                else:
                    notify_failure(week_start, week_end, err, stage="fetch", retry_status=f"Retrying (Attempt {attempt + 1}/{max_attempts})")
                    time.sleep(10)
                    continue

        # ── Stage 2: Parse ────────────────────────────────────────────────
        print(f"\n── STAGE 2: Parse (Attempt {attempt}) ──")
        try:
            raw_df, incentive_df, summary_df = parse_statement(downloaded_file, week_start=week_start, week_end=week_end)
            print(f"[PIPELINE] ✓ Parse done: {len(raw_df)} raw rows, {len(incentive_df)} incentive rows, {len(summary_df)} summary rows")
            break
        except Exception as e:
            err = str(e)
            print(f"[PIPELINE] ✗ Parse failed on attempt {attempt}: {err}")
            traceback.print_exc()
            if attempt == max_attempts:
                notify_failure(week_start, week_end, err, stage="parse", retry_status="Max retries reached")
                sys.exit(1)
            else:
                notify_failure(week_start, week_end, err, stage="parse", retry_status=f"Retrying (Attempt {attempt + 1}/{max_attempts})")
                time.sleep(10)
                continue

    # ── Stage 3: Load ─────────────────────────────────────────────────────────
    print("\n── STAGE 3: Load ──")
    try:
        stats = load_to_postgres(
            raw_df=raw_df,
            incentive_df=incentive_df,
            summary_df=summary_df,
            week_start=week_start,
            week_end=week_end,
            logger=print,
        )
        print(f"[PIPELINE] ✓ Load done: {stats}")
    except Exception as e:
        err = str(e)
        print(f"[PIPELINE] ✗ Load failed: {err}")
        traceback.print_exc()
        notify_failure(week_start, week_end, err, stage="load")
        sys.exit(1)

    # ── Stage 4: Notify ───────────────────────────────────────────────────────
    print("\n── STAGE 4: Notify ──")
    notify_success(week_start, week_end, stats, recovered=recovered_flag)

    print("\n" + "=" * 60)
    print(f"[PIPELINE] ✓ ALL STAGES COMPLETE")
    print("=" * 60)



if __name__ == "__main__":
    main()
