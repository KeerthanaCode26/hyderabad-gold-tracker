# 🪙 Gold Price Tracker

Automatically tracks 24K and 22K gold prices for Hyderabad every 12 hours and sends an update straight to Telegram — no server required, powered entirely by GitHub Actions.

## What it does

- Scrapes live gold rates from [goodreturns.in](https://www.goodreturns.in/gold-rates/hyderabad.html)
- Compares today's price against the last recorded price
- Sends a Telegram message on **every run** — whether the price rose, dropped, or stayed flat
- Includes the last 5 days of price history in each update
- Runs on a schedule (every 12 hours) via GitHub Actions — nothing to keep running on your own machine

## Prerequisites

- A GitHub account
- A Telegram account
- Python 3.10+ (only needed if you want to run it locally, not required for the automated version)

## Setup

### 1. Fork or clone this repository

```bash
git clone https://github.com/<your-username>/hyderabad-gold-tracker.git
cd hyderabad-gold-tracker
```

### 2. Create a Telegram bot

1. Open Telegram and search for **[@BotFather](https://t.me/BotFather)**
2. Send `/newbot` and follow the prompts (choose a name and a username ending in `bot`)
3. BotFather will give you a **token** that looks like `123456789:ABCdefGHIjklMNOpqrSTUvwxyz`
4. Save this — it's your `TELEGRAM_TOKEN`

### 3. Get your chat ID

**For personal alerts (just you):**
1. Search for your new bot on Telegram and hit **Start**
2. Send it any message (e.g. "hi")
3. Open this URL in your browser, replacing `<TOKEN>` with your bot token:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
4. Look for `"chat":{"id": ...}` in the response — that number is your `TELEGRAM_CHAT_ID`

**For a group (multiple people getting alerts):**
1. Create a Telegram group and add your bot to it
2. Send any message in the group
3. Fetch the same `getUpdates` URL as above
4. Look for the group's `chat.id` — it will be a **negative number** (e.g. `-1001234567890`)
5. Use that as your `TELEGRAM_CHAT_ID`

### 4. Add your secrets to GitHub

In your repository on GitHub:

1. Go to **Settings → Secrets and variables → Actions**
2. Click **New repository secret** and add:
   - `TELEGRAM_TOKEN` → your bot token from step 2
   - `TELEGRAM_CHAT_ID` → your chat ID from step 3

Your credentials are never stored in code — GitHub injects them as environment variables only when the workflow runs.

### 5. Enable Actions and test it

1. Go to the **Actions** tab of your repo
2. Click **Check Gold Price** in the left sidebar
3. Click **Run workflow → Run workflow** to trigger it manually
4. Check your Telegram — you should receive a price update within about 15-20 seconds

If everything works, the workflow will now run automatically every 12 hours (`00:00` and `12:00` UTC) with no further action needed from you.

## Running locally (optional)

```bash
pip install requests beautifulsoup4

export TELEGRAM_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"

python gold_tracker.py
```

## Project structure

```
hyderabad-gold-tracker/
├── gold_tracker.py              # Main script: scrape, compare, notify
├── last_price.txt               # Auto-updated baseline price (committed by the workflow)
├── .github/
│   └── workflows/
│       └── run_tracker.yaml     # GitHub Actions schedule + job definition
└── README.md
```

## Using a different currency (not India/INR)

This project scrapes goodreturns.in, which is India-specific and reports prices in INR. If you're outside India, or just want a more stable data source than HTML scraping, consider using **[GoldAPI.io](https://www.goldapi.io/)** instead — a JSON REST API for real-time and historical gold, silver, platinum, and palladium prices, supporting USD, EUR, GBP, AUD, INR, and many other currencies.

Example call:

```python
import requests

headers = {"x-access-token": "YOUR_GOLDAPI_KEY"}
response = requests.get("https://www.goldapi.io/api/XAU/USD", headers=headers)
data = response.json()
print(data["price"])  # price per troy ounce in USD
```

Swapping to GoldAPI.io means you'd:
- Sign up at [goldapi.io](https://www.goldapi.io/) for a free API key
- Replace `get_gold_prices()` in `gold_tracker.py` with a call to the endpoint above, using your target currency code (e.g. `USD`, `EUR`, `GBP`) instead of scraping HTML
- Convert from price-per-ounce to price-per-gram if needed (1 troy ounce ≈ 31.1035 grams)
- Add `GOLDAPI_KEY` as a new GitHub Secret alongside your Telegram credentials

## Notes

- This project scrapes a public website's HTML, which is inherently a bit fragile — if goodreturns.in changes their page layout, the scraper may need updating.
- Gold rates shown are indicative and do not include GST, making charges, or other levies. 

## License

Feel free to fork, modify, and adapt this for your own city or use case.
