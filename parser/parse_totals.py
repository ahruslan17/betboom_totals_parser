import asyncio
from playwright.async_api import async_playwright
import re
import pandas as pd
from datetime import datetime, timezone
import argparse
import os

# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("--url", required=True, help="Match URL")
parser.add_argument(
    "--start", required=True, help="Start time (UTC) (YYYY-MM-DD HH:MM:SS)"
)
parser.add_argument("--end", required=True, help="End time (UTC) (YYYY-MM-DD HH:MM:SS)")
args = parser.parse_args()

URL = args.url
START_TIME_UTC_STR = args.start
END_TIME_UTC_STR = args.end


# Function to create filename from URL (keep only digits, join with hyphens)
def url_to_filename(url: str) -> str:
    import re

    parts = re.findall(r"\d+", url)
    return "-".join(parts) + ".csv"


# File path — in data folder with filename based on URL
CSV_DIR = "data"
os.makedirs(CSV_DIR, exist_ok=True)
CSV_PATH = os.path.join(CSV_DIR, url_to_filename(URL))


async def parse_totals_once():
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "url": URL,
        "quarter": None,
        "totals": None,
    }
    success = False

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(URL)

            total_tab = await page.wait_for_selector(
                'button:has-text("Тотал")', timeout=7000
            )
            await total_tab.click()
            await page.wait_for_timeout(4000)

            divs = await page.query_selector_all("div")
            for div in divs:
                txt = (await div.inner_text()).strip()
                lines = [line.strip() for line in txt.split("\n") if line.strip()]

                if not lines:
                    continue

                if re.fullmatch(r"\d+-я четверть: Тотал", lines[0]):
                    quarter_name = lines[0].split(":")[0]
                    row["quarter"] = quarter_name

                    results = []
                    data = lines[1:]
                    i = 0
                    while i + 4 < len(data):
                        if (
                            data[i].lower() == "меньше"
                            and data[i + 3].lower() == "больше"
                        ):
                            less_coef = data[i + 1]
                            total = data[i + 2]
                            more_coef = data[i + 4]
                            results.append(f"{total}: <{less_coef}, >{more_coef}")
                            i += 5
                        else:
                            i += 1

                    row["totals"] = (
                        " | ".join(results) if results else "No coefficients"
                    )
                    success = True
                    break

            await browser.close()

        if not success:
            row["quarter"] = "not found"
            row["totals"] = "No suitable block found"

    except Exception as e:
        row["quarter"] = "error"
        row["totals"] = f"Error: {str(e).strip().splitlines()[0]}"

    return row


async def run_parsing_between_times(start_time_str, end_time_str, interval_sec=60):
    # Input strings are UTC
    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )

    print(f"⏳ Waiting for start at {start_time} (UTC)...")
    while datetime.now(timezone.utc) < start_time:
        await asyncio.sleep(1)

    print(
        f"⏱️ Parsing started from {start_time} to {end_time} every {interval_sec} seconds...\n"
    )

    while datetime.now(timezone.utc) <= end_time:
        row = await parse_totals_once()
        print(f"[{row['timestamp']}] ✅ Saving: {row['totals'][:80]}...")

        try:
            df = pd.DataFrame([row])
            df.to_csv(
                CSV_PATH,
                mode="a",
                index=False,
                header=not os.path.exists(CSV_PATH),
                encoding="utf-8",
            )
        except Exception as write_err:
            print("⚠️ Error writing to CSV:", write_err)

        await asyncio.sleep(interval_sec)

    print(
        f"🏁 Finished at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} (UTC)."
    )


if __name__ == "__main__":
    asyncio.run(
        run_parsing_between_times(START_TIME_UTC_STR, END_TIME_UTC_STR, interval_sec=60)
    )
