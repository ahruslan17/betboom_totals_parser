# BetBoom Totals Parser

A Python-based automated scraper and data collector for basketball match totals and odds from the BetBoom sports betting website. The project fetches basketball match schedules, dynamically monitors match total odds over time, and saves the data for further analysis.

This repository includes:
- Match list parsing (`parse_matches.py`)
- Periodic total odds scraping (`parse_totals.py`)
- Orchestration and scheduling (`main.py`)
- Docker-based deployment support

---

## Table of Contents

- [Project Overview](#project-overview)  
- [Features](#features)  
- [Technologies](#technologies)  
- [Installation](#installation)  
- [Usage](#usage)  
- [Project Structure](#project-structure)  
- [Details on Core Modules](#details-on-core-modules)  
- [Docker Usage](#docker-usage)  
- [Future Improvements](#future-improvements)  
- [License](#license)  

---

## Project Overview

This project automates the scraping of basketball match data and their respective betting totals (over/under odds) from the BetBoom website. It:

- Periodically fetches new basketball matches and their URLs.  
- For each match, scrapes total odds in specified time intervals during the match.  
- Saves match info and collected odds into CSV files in a structured `data/` folder.  
- Supports asynchronous execution for efficient scraping.  
- Can run continuously and schedule tasks every hour via an async main loop.  
- Supports containerization with Docker for easy deployment.

This project is designed to support sports data analysts, bettors, or developers building predictive models or analysis pipelines based on live odds data.

---

## Features

- **Basketball match list parsing:** Extracts upcoming basketball matches, their scheduled start times, and URLs from BetBoom.  
- **Dynamic odds scraping:** Scrapes live total betting odds for each quarter of a match in regular intervals.  
- **Asynchronous architecture:** Uses Python `asyncio` and `playwright` for efficient browser automation and scraping.  
- **Automated scheduling:** The main script can run continuously and trigger parsing tasks hourly.  
- **Robust CSV storage:** Stores all collected data into CSV files with structured naming based on match URLs.  
- **Docker-ready:** Dockerfile and docker-compose.yml included for containerized deployment.

---

## Technologies

- Python 3.10+  
- [Playwright](https://playwright.dev/python/) for headless browser automation  
- Asyncio for asynchronous tasks  
- Pandas for data storage in CSV format  
- Docker for containerization  

---

## Installation

1. Clone this repository:

```
    git clone https://github.com/ahruslan17/betboom_totals_parser.git  
    cd betboom_totals_parser/parser
```

2. Create and activate a Python virtual environment (recommended):

```
    python -m venv venv  
    source venv/bin/activate  # Linux/macOS  
    venv\Scripts\activate     # Windows
```


3. Install required dependencies:

```
    pip install -r requirements.txt
```

4. Install Playwright browsers:

```
    python -m playwright install
```

---

## Usage

### 1. Running the main scheduler

Run the main script to start parsing new basketball matches every hour and launch scraping tasks for totals:

```
    python main.py
```

The script will:

- Parse new matches and save them in data/matches.csv.  
- For matches not yet processed (status == "None"), it will start scraping total odds in the background for a default duration of 80 minutes per match.

---

### 2. Parsing basketball matches only

To just parse the basketball matches and update the CSV:

```
    python parse_matches.py
```

---

### 3. Scraping totals for a specific match and time window

Run:

```
    python parse_totals.py --url <match_url> --start "YYYY-MM-DD HH:MM:SS" --end "YYYY-MM-DD HH:MM:SS"
```

Example:

    python parse_totals.py --url "https://betboom.ru/sport/basketball/..." --start "2025-07-21 12:00:00" --end "2025-07-21 13:20:00"

The script will scrape the total odds every 60 seconds within the specified UTC time window, saving results to a CSV in data/.

---

## Project Structure

    parser/
    ├── data/                       # Folder to store CSV data files
    ├── docker-compose.yml          # Docker Compose configuration
    ├── Dockerfile                  # Docker image build configuration
    ├── main.py                     # Main scheduler and orchestrator script
    ├── parse_matches.py            # Script to parse basketball matches and save URLs/schedule
    ├── parse_totals.py             # Script to scrape total odds data from a match URL
    ├── requirements.txt            # Python dependencies list
    └── __pycache__/                # Python cache files (auto-generated)

---

## Example Data Tables

### Matches CSV (`data/matches.csv`)

| title               | url                                                      | schedule           | status         |
|---------------------|----------------------------------------------------------|--------------------|----------------|
| Team A vs Team B    | https://betboom.ru/sport/basketball/31/20277/2387762    | 2025-07-21 19:30:00 | None           |
| Team C vs Team D    | https://betboom.ru/sport/basketball/31/20278/2387763    | 2025-07-21 21:00:00 | ProcessCreated |

- **title**: Match title (teams playing)  
- **url**: Link to the match page on BetBoom  
- **schedule**: Scheduled match start time in UTC (YYYY-MM-DD HH:MM:SS)  
- **status**: Processing status (`None` = not started, `ProcessCreated` = scraping started)

---

### Totals CSV (e.g., `data/31-20277-2387762.csv`)

| timestamp           | url                                                      | quarter     | totals                                   |
|---------------------|----------------------------------------------------------|-------------|------------------------------------------|
| 2025-07-21 19:31:00 | https://betboom.ru/sport/basketball/31/20277/2387762    | 1-я четверть | 182.5: <1.85, >1.95 \| 183: <1.90, >1.90 |
| 2025-07-21 19:32:00 | https://betboom.ru/sport/basketball/31/20277/2387762    | 1-я четверть | 182.5: <1.84, >1.96 \| 183: <1.88, >1.92 |

- **timestamp**: When the data was scraped (UTC)  
- **url**: Match URL  
- **quarter**: Quarter name (e.g., "1-я четверть")  
- **totals**: Totals odds for different values, format: `total: <less_coef, >more_coef`

---

## Details on Core Modules

### main.py

- Runs an infinite loop every hour.  
- Calls parse_basketball_matches() to fetch new matches.  
- Reads data/matches.csv and starts scraping totals for matches with status "None" by launching subprocesses running parse_totals.py.  
- Updates match status to "ProcessCreated" once scraping task starts.

---

### parse_matches.py

- Uses Playwright to navigate https://betboom.ru/.  
- Clicks on basketball section, scrapes list of matches, titles, scheduled start times, and URLs.  
- Parses Russian schedule times like "сегодня 19:30", "завтра 20:00", and converts to UTC datetime strings.  
- Appends new matches into data/matches.csv.

---

### parse_totals.py

- Takes a match URL and start/end UTC time arguments.  
- Runs a loop every 60 seconds during that time window.  
- Opens match URL with Playwright, clicks on the "Тотал" tab, and parses total odds for the current quarter.  
- Extracts odds for "less" and "more" totals with their coefficients.  
- Saves data with timestamp and quarter info into a CSV file in data/.

---

## Docker Usage

Build and run the containerized version of the scraper for consistent environment and easy deployment:

    docker build -t betboom_totals_parser .  
    docker run -it --rm betboom_totals_parser

Or use docker-compose:

    docker-compose up

The Docker setup installs dependencies, sets up Playwright browsers, and runs the main async loop.

---

## Future Improvements

- Add retries and error handling improvements for network errors and dynamic page changes.  
- Support additional sports or bet types.  
- Integrate database storage (e.g., PostgreSQL) instead of CSV files.  
- Add more flexible scheduling options and config files.  
- Implement advanced data analysis or visualization modules.

---

## License

This project is released under the Apache 2.0 Licence.

---
