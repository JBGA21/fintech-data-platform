import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")

if not API_KEY:
    raise ValueError("FMP_API_KEY is not configured")


SYMBOLS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
]

OUTPUT_DIR = Path("data/raw/fmp")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Number of calendar days to reprocess
# This gives us a small lookback window in case
# historical records are corrected.
LOOKBACK_DAYS = 7

# ---------------------------------------------------------
# Functions
# ---------------------------------------------------------

def fetch_historical_prices(symbol: str, from_date: str, to_date: str) -> list:
    """
    Retrieve historical EOD prices for a company
    within a specific date range from FMP.
    """

    url = (
        "https://financialmodelingprep.com/"
        "stable/historical-price-eod/full"
    )

    params = {
        "symbol": symbol,
        "from": from_date,
        "to": to_date,
        "apikey": API_KEY,
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def save_raw_data(symbol: str, data: list, from_date: str, to_date: str) -> Path:
    """
    Save raw API response as JSON.
    """

    ingestion_timestamp = datetime.now(timezone.utc)

    output_file = (
        OUTPUT_DIR
        / (
            f"{symbol}_"
            f"{from_date}_{to_date}_"
            f"{ingestion_timestamp:%Y%m%dT%H%M%SZ}.json"
        )
    )

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    return output_file

# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    today = datetime.now(timezone.utc).date()

    from_date = today - timedelta(days=LOOKBACK_DAYS)

    to_date = today

    print(
        f"Ingestion window: "
        f"{from_date} → {to_date}"
    )

    for symbol in SYMBOLS:

        print(f"Starting ingestion for {symbol}...")

        try:
            data = fetch_historical_prices(
                symbol,
                str(from_date),
                str(to_date)
            )

            output_file = save_raw_data(
                symbol,
                data,
                str(from_date),
                str(to_date)
            )

            print(
                f"{symbol}: "
                f"{len(data)} records "
                f"→ {output_file}"
            )

        except requests.RequestException as error:

            print(
                f"{symbol}: "
                f"API request failed: {error}"
            )

        except Exception as error:

            print(
                f"{symbol}: "
                f"unexpected error: {error}"
            )

if __name__ == "__main__":
    main()
