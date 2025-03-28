# 🏛️ Senator Stock Tracker & Analytics Bot

## 📌 Overview

This project is a comprehensive web scraper and Discord bot designed to:
- Fetch and analyze stock transaction filings by U.S. Senators from [efdsearch.senate.gov](https://efdsearch.senate.gov).
- Store filings and transactions in a database for further analytics.
- Provide interactive analytics and insights directly via Discord through advanced slash commands.

---

## ⚙️ Tech Stack
- 🐍 **Python**
- 💬 **Discord.py**
- 🌐 **BeautifulSoup4, Requests, urllib3** for web scraping
- 📈 **yfinance** for financial data
- 🛢️ **SQLite** Database

---

## 📂 Project Structure
```
📁 senate-filings/
├── 📄 .env
├── 📄 .env.example
├── 📄 discord_bot.py
├── 📄 filings.db
├── 📄 main.py
├── 📄 requirements.txt
├── 📁 bot_modules/
│   ├── bot_db.py
│   ├── bot_embed.py
│   ├── bot_ui.py
│   └── bot_utilis.py
├── 📁 cogs/
│   ├── slash_feedback.py
│   ├── slash_leaderboard.py
│   ├── slash_party.py
│   ├── slash_senator.py
│   ├── slash_senatorlist.py
│   └── slash_subscribe.py
├── 📁 debug/
│   ├── analytics.log
│   ├── main.log
│   └── matched_transactions.log
└── 📁 modules/
    ├── analytics_party.py
    ├── analytics_senators.py
    ├── analytics_txmatch.py
    ├── config.py
    ├── db_helper.py
    ├── logger.py
    ├── notify_system.py
    ├── scraper_filings.py
    ├── scraper_transactions.py
    ├── session_utilis.py
    ├── utilis.py
    └── 📁 resources/
        └── ignore_tickers.txt
```

---

## 🚀 Features

- **Automated Scraping**:
  - Regularly scrapes senator filings and transactions.
  - Extensive logging and robust database management.
  - Captures unique transactions and stores them persistently.

- **Advanced Analytics**:
  - Transaction matching (buy ➡️ sell).
  - Generates detailed analytics per senator and per political party.
  - Extensive data points including transaction counts, profits, and accuracy metrics.

- **Interactive Discord Integration**:
  - ✅ Slash commands with autocomplete and pagination.
  - 📊 Rich embed analytics with interactive navigation.

---

## 🤖 Discord Slash Commands

- `/senator <name>`: Displays 4-page detailed analytics for a senator.
- `/senatorlist`: Paginated list of all senators.
- `/party <Democratic|Republican>`: Aggregated analytics for the selected political party.
- `/leaderboard <criteria>`: View top 10 senators by chosen criteria.
- `/subscribe`: Information on subscription options for premium analytics.
- `/feedback`: User feedback collection via pop-up modal.

---

## 🔧 Setup & Installation

1. **Clone the Repository:**
   ```bash
   git clone your-repo-url
   cd senate-filings
   ```

2. **Set Up Environment:**
   ```bash
   python -m venv env
   source env/bin/activate  # Linux/Mac
   .\env\Scripts\activate   # Windows

   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Rename `.env.example` to `.env` and fill in your details.

4. **Database Initialization:**
   The database (`filings.db`) initializes automatically on the first run.

5. **Run Scripts:**
   - **Scraper:**
     ```bash
     python main.py
     ```

   - **Discord Bot:**
     ```bash
     python discord_bot.py
     ```

---

## 🌟 Example `.env` Configuration

```env
DISCORD_WEBHOOK_NOTIFICATION_FREE=your_webhook_url
DISCORD_BOT_TOKEN=your_bot_token
DB_NAME=filings.db
SCRIPT_FREQUENCY_SECONDS=10800
...
```

---

## 🎯 Future Improvements
- Web dashboard for analytics visualization.
- Enhanced historical data comparisons.
- More advanced filtering and user personalization features.

---

## 📬 Contributions
Contributions, bug reports, and feature requests are welcome!

---

🌟 **Happy tracking & analytics!** 🌟

