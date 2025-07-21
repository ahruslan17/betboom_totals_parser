import asyncio
import csv
import os
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import re

# ====== CONSTANTS ======
URL_MAIN = "https://betboom.ru/"
SELECTOR_BASKETBALL_BUTTON = 'button[data-at-title="Баскетбол"]'
SELECTOR_MATCH_CARD = "div[class^='Ur2bE-']"
SELECTOR_TIME_IN_CARD = "time[class^='dHlnp-']"
SELECTOR_TEAM_NAMES = "span[class^='rzys6-']"
SELECTOR_PAGE_HEADER = "header"

CSV_FILE = "data/matches.csv"
FIELDNAMES = ["title", "url", "schedule", "status"]


def log(msg: str):
    print(f"[{datetime.now()}] {msg}")


def parse_schedule_text(text: str) -> str:
    text = text.lower().strip()

    if text.startswith("сегодня"):
        time_part = re.search(r"\d{1,2}:\d{2}", text)
        if time_part:
            dt = datetime.now().replace(
                hour=int(time_part.group().split(":")[0]),
                minute=int(time_part.group().split(":")[1]),
                second=0,
                microsecond=0,
            )
            return dt.strftime("%Y-%m-%d %H:%M:%S")

    elif text.startswith("завтра"):
        time_part = re.search(r"\d{1,2}:\d{2}", text)
        if time_part:
            dt = datetime.now() + timedelta(days=1)
            dt = dt.replace(
                hour=int(time_part.group().split(":")[0]),
                minute=int(time_part.group().split(":")[1]),
                second=0,
                microsecond=0,
            )
            return dt.strftime("%Y-%m-%d %H:%M:%S")

    else:
        months = {
            "января": 1,
            "февраля": 2,
            "марта": 3,
            "апреля": 4,
            "мая": 5,
            "июня": 6,
            "июля": 7,
            "августа": 8,
            "сентября": 9,
            "октября": 10,
            "ноября": 11,
            "декабря": 12,
        }
        match = re.search(r"(\d{1,2}) (\w+)(?: в)? (\d{2}:\d{2})", text)
        if match:
            day = int(match.group(1))
            month_str = match.group(2)
            time_part = match.group(3)
            hour, minute = map(int, time_part.split(":"))

            month = months.get(month_str)
            year = datetime.now().year
            if month:
                dt = datetime(year, month, day, hour, minute)
                return dt.strftime("%Y-%m-%d %H:%M:%S")

    return "unknown"


def load_existing_urls():
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)

    if not os.path.exists(CSV_FILE):
        return set()

    with open(CSV_FILE, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return set(row["url"] for row in reader if "url" in row)


def append_new_matches(new_matches):
    existing_urls = load_existing_urls()
    to_add = [m for m in new_matches if m["url"] not in existing_urls]

    if not to_add:
        log("No new matches to add.")
        return

    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        for match in to_add:
            writer.writerow(match)

    log(f"Added new matches: {len(to_add)}")


async def parse_match_card_basic(card):
    team_spans = await card.query_selector_all(SELECTOR_TEAM_NAMES)
    teams = [await span.inner_text() for span in team_spans]
    title = " vs ".join(t.strip() for t in teams) if teams else "unknown"

    time_elem = await card.query_selector(SELECTOR_TIME_IN_CARD)
    raw_schedule = await time_elem.inner_text() if time_elem else "unknown"
    schedule = parse_schedule_text(raw_schedule)

    return title, schedule


async def parse_basketball_matches():
    matches = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        log(f"Opening {URL_MAIN}")
        await page.goto(URL_MAIN)
        await page.wait_for_selector(SELECTOR_BASKETBALL_BUTTON, timeout=20000)

        try:
            await page.click(SELECTOR_BASKETBALL_BUTTON)
            await page.wait_for_selector(SELECTOR_MATCH_CARD, timeout=20000)
            await asyncio.sleep(2)
        except Exception as e:
            log(f"Error clicking basketball button: {e}")
            return

        log("Start parsing match cards...")

        i = 0
        while True:
            match_cards = await page.query_selector_all(SELECTOR_MATCH_CARD)
            if i >= len(match_cards):
                break

            try:
                card = match_cards[i]
                title, schedule = await parse_match_card_basic(card)

                await card.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                await card.click()
                await page.wait_for_selector(SELECTOR_PAGE_HEADER, timeout=15000)
                await asyncio.sleep(2)

                current_url = page.url
                status = "None"

                log(f"[{i+1}] {title} | {schedule} | {current_url} | status: {status}")

                matches.append(
                    {
                        "title": title,
                        "url": current_url,
                        "schedule": schedule,
                        "status": status,
                    }
                )

                # Go back to main page and reopen basketball section
                await page.go_back()
                await page.wait_for_selector(SELECTOR_BASKETBALL_BUTTON, timeout=20000)
                await page.click(SELECTOR_BASKETBALL_BUTTON)
                await page.wait_for_selector(SELECTOR_MATCH_CARD, timeout=20000)
                await asyncio.sleep(2)

            except Exception as e:
                log(f"[{i+1}] Error while parsing card: {e}")

            i += 1

        await browser.close()
        append_new_matches(matches)


if __name__ == "__main__":
    asyncio.run(parse_basketball_matches())
