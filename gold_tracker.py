import os
import re
import sys
import requests
from bs4 import BeautifulSoup

# 1. Configuration & Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PRICE_FILE = "last_price.txt"

# Dynamic city setup
city_name = "hyderabad"
URL = f"https://www.goodreturns.in/gold-rates/{city_name}.html"


def clean_price(raw_price):
    """'₹16,375(-22)' -> 16375.0"""
    raw_price = raw_price.split("(")[0]
    digits = re.sub(r"[^\d.]", "", raw_price)
    return float(digits) if digits else None


def get_gold_prices():
    """
    Returns (price_24k, price_22k) for 1 gram, or (None, None) on failure.

    Table layout on goodreturns.in (as of Aug 2026):
      Table 0 = "Today Gold Price Per Gram" -> columns: Gram | 24K | 22K | 18K
      Row for 1 gram has cells[0] text == "1"
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table")
        if table is None:
            print("Could not find the price table on the page.")
            return None, None

        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 3 and cells[0].get_text(strip=True) == "1":
                price_24k = clean_price(cells[1].get_text(strip=True))
                price_22k = clean_price(cells[2].get_text(strip=True))
                if price_24k is not None and price_22k is not None:
                    return price_24k, price_22k

        print("Could not isolate '1 Gram' data row inside webpage rows.")
        return None, None

    except Exception as e:
        print(f"Scraping failed for {city_name}: {e}")
        return None, None


def get_last_n_days(n=5):
    """
    Returns a list of (date_str, price_24k, price_22k) for the last n days,
    most recent first, pulled from the "Gold Rate for Last 10 Days" table.

    Table layout: Table 1 -> columns: Date | 24K | 22K
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        tables = soup.find_all("table")
        if len(tables) < 2:
            print("Could not find the historical (last 10 days) table on the page.")
            return []

        history_table = tables[1]
        rows = history_table.find_all("tr")

        results = []
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 3:
                continue
            date_text = cells[0].get_text(strip=True)
            if date_text.lower() == "date":  # skip header row
                continue
            price_24k = clean_price(cells[1].get_text(strip=True))
            price_22k = clean_price(cells[2].get_text(strip=True))
            if price_24k is not None and price_22k is not None:
                results.append((date_text, price_24k, price_22k))
            if len(results) >= n:
                break

        return results

    except Exception as e:
        print(f"Fetching history failed for {city_name}: {e}")
        return []


def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram tokens missing locally. Skipping notification dispatch.")
        return
    # NOTE: fixed API URL below (was previously pointing at telegram.org, not the Bot API)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, json=payload)


def main():
    price_24k, price_22k = get_gold_prices()
    if not price_24k or not price_22k:
        sys.exit("Price extraction failed.")

    print(
        f"Current {city_name.capitalize()} Gold Price -> "
        f"24K: ₹{price_24k}/g | 22K: ₹{price_22k}/g"
    )

    # Last 5 days history
    history = get_last_n_days(5)
    if history:
        print(f"\nLast {len(history)} days ({city_name.capitalize()}):")
        for date_text, h24, h22 in history:
            print(f"  {date_text}: 24K ₹{h24}/g | 22K ₹{h22}/g")
    else:
        print("Could not retrieve 5-day history.")

    # Historical price data comparison checks (based on 22K, as before)
    last_price = None
    if os.path.exists(PRICE_FILE):
        with open(PRICE_FILE, "r") as f:
            try:
                last_price = float(f.read().strip())
            except ValueError:
                pass

    if last_price is not None:
        if price_22k < last_price:
            drop = round(last_price - price_22k, 2)
            msg = (
                f"📉 {city_name.capitalize()} Gold Price Dropped!\n"
                f"Old (22K): ₹{last_price}/g\n"
                f"New (22K): ₹{price_22k}/g\n"
                f"Saved: ₹{drop}/g!\n\n"
                f"24K: ₹{price_24k}/g\n"
            )
            if history:
                msg += f"\nLast {len(history)} days:\n"
                for date_text, h24, h22 in history:
                    msg += f"{date_text}: 24K ₹{h24}/g | 22K ₹{h22}/g\n"
            send_telegram(msg)
            print("Alert triggered and dispatched successfully.")
        else:
            print(f"No drop detected. Current (₹{price_22k}) >= Previous (₹{last_price})")
    else:
        print(f"First run on this machine. Saved initial reference rate: ₹{price_22k}")

    # Write current 22K price state to historical text baseline tracking file
    with open(PRICE_FILE, "w") as f:
        f.write(str(price_22k))


if __name__ == "__main__":
    main()