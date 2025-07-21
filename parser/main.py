import csv
import os
import asyncio
import subprocess
from datetime import datetime, timedelta, timezone

from parse_matches import parse_basketball_matches

MATCHES_CSV = "data/matches.csv"
DEFAULT_DURATION_MINUTES = 80
# MSK_TZ = timezone(timedelta(hours=3))  # MSK = UTC+3


async def process_matches():
    print(f"[{datetime.now()}] Start processing matches...")

    try:
        await parse_basketball_matches()
        print(f"[{datetime.now()}] Successfully parsed new matches.")
    except Exception as e:
        print(f"[{datetime.now()}] Error while parsing matches: {e}")
        return

    try:
        with open(MATCHES_CSV, newline="", encoding="utf-8") as f:
            matches = list(csv.DictReader(f))
        print(f"[{datetime.now()}] Loaded {len(matches)} matches.")
    except FileNotFoundError:
        print(f"[{datetime.now()}] CSV file {MATCHES_CSV} not found.")
        return

    updated = False
    for match in matches:
        if match.get("status", "False") == "None":
            url = match["url"]
            start_time_str = match["schedule"]

            try:
                dt_start_utc = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                dt_start_utc_with_offset = dt_start_utc - timedelta(minutes=10)
                dt_end_utc = dt_start_utc + timedelta(minutes=DEFAULT_DURATION_MINUTES)

                command = [
                    "python",
                    "parse_totals.py",
                    "--url",
                    url,
                    "--start",
                    dt_start_utc_with_offset.strftime("%Y-%m-%d %H:%M:%S"),
                    "--end",
                    dt_end_utc.strftime("%Y-%m-%d %H:%M:%S"),
                ]

                subprocess.Popen(command)
                print(f"[{datetime.now()}] Process created: {url}")
                print(
                    f"[{datetime.now()}] Start: {dt_start_utc_with_offset}, End: {dt_end_utc}"
                )

                match["status"] = "ProcessCreated"
                updated = True

            except Exception as e:
                print(f"[{datetime.now()}] Error processing match {url}: {e}")

    if updated:
        try:
            with open(MATCHES_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=matches[0].keys())
                writer.writeheader()
                writer.writerows(matches)
            print(f"[{datetime.now()}] CSV file updated.")
        except Exception as e:
            print(f"[{datetime.now()}] Failed to update CSV file: {e}")
    else:
        print(f"[{datetime.now()}] No matches were updated.")


async def main_loop():
    while True:
        await process_matches()
        print(f"[{datetime.now()}] Sleeping for 1 hour...\n")
        await asyncio.sleep(3600)


if __name__ == "__main__":
    print("Start")
    asyncio.run(main_loop())
