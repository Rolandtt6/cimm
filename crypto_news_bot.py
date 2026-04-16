#!/usr/bin/env python3
"""
Crypto Insider MM — Telegram News Bot
======================================
သတင်းတွေ auto fetch ပြီး Telegram channel မှာ post လုပ်ပေးတယ်

SETUP:
  pip install requests feedparser schedule

RUN:
  python crypto_news_bot.py
"""

import requests
import feedparser
import schedule
import time
import json
import os
import hashlib
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────
BOT_TOKEN  = "8745293910:AAHOvztDgGjIxTVRywY9j1-ENlflXr749Tg"
CHANNEL_ID = "-1003896067498"      # Crypto Insider MM
SENT_FILE  = "sent_news.json"      # duplicate check file

# ── RSS SOURCES ───────────────────────────────────────
RSS_SOURCES = [
    {"name": "CoinTelegraph", "url": "https://cointelegraph.com/rss",                          "emoji": "📰"},
    {"name": "CoinDesk",      "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",        "emoji": "📊"},
    {"name": "Decrypt",       "url": "https://decrypt.co/feed",                                "emoji": "🔓"},
    {"name": "The Block",     "url": "https://www.theblock.co/rss.xml",                        "emoji": "⛓️"},
    {"name": "BeInCrypto",    "url": "https://beincrypto.com/feed/",                           "emoji": "🌐"},
    {"name": "Bitcoin Mag",   "url": "https://bitcoinmagazine.com/feed",                       "emoji": "₿"},
]

# ── KEYWORDS (ဒီ keyword ပါတဲ့ သတင်းကို Breaking news အနေနဲ့ ပြမယ်) ──
BREAKING_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "xrp", "ripple",
    "solana", "sol", "etf", "sec", "fed", "crash", "surge",
    "hack", "liquidat", "ath", "all-time high", "rally"
]

# ── SENT HISTORY (duplicate ကင်းအောင်) ──────────────
def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent)[-500:], f)  # နောက်ဆုံး 500 ခုသာ သိမ်း

def news_id(title):
    return hashlib.md5(title.encode()).hexdigest()[:12]

# ── TELEGRAM SEND ─────────────────────────────────────
def send_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print(f"  ✅ Sent: {text[:60]}...")
            return True
        else:
            print(f"  ❌ Error {r.status_code}: {r.text[:100]}")
            return False
    except Exception as e:
        print(f"  ❌ Network error: {e}")
        return False

# ── SENTIMENT ─────────────────────────────────────────
def get_sentiment(title):
    t = title.lower()
    bull = ["surge","soar","rally","gain","bull","rise","record","pump","approve","etf","breakout","ath","launch","adoption","high"]
    bear = ["crash","drop","fall","bear","dump","fear","hack","ban","plunge","collapse","scam","liquidat","warn","risk","low"]
    for w in bull:
        if w in t:
            return "📈 Bullish"
    for w in bear:
        if w in t:
            return "📉 Bearish"
    return "📊 Neutral"

def is_breaking(title):
    t = title.lower()
    return any(kw in t for kw in BREAKING_KEYWORDS)

# ── FORMAT NEWS MESSAGE ───────────────────────────────
def format_news(item, source):
    sentiment = get_sentiment(item.get("title",""))
    breaking  = "🚨 BREAKING NEWS\n\n" if is_breaking(item.get("title","")) else ""
    title     = item.get("title","").strip()
    link      = item.get("link","").strip()
    pub_date  = item.get("published","")

    # Format time
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(pub_date)
        time_str = dt.strftime("%b %d, %H:%M UTC")
    except:
        time_str = pub_date[:16] if pub_date else ""

    msg = (
        f"{breaking}"
        f"{source['emoji']} <b>{source['name']}</b>  |  {sentiment}\n\n"
        f"<b>{title}</b>\n\n"
        f"🔗 <a href='{link}'>Read Full Article</a>\n\n"
        f"⏰ {time_str}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📡 Crypto Insider MM"
    )
    return msg

# ── FETCH & POST NEWS ─────────────────────────────────
def fetch_and_post():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Fetching news...")
    sent = load_sent()
    new_count = 0

    for source in RSS_SOURCES:
        try:
            print(f"  Fetching {source['name']}...")
            feed = feedparser.parse(source["url"])
            entries = feed.entries[:5]  # နောက်ဆုံး ၅ ခုပဲ စစ်မယ်

            for entry in entries:
                title = entry.get("title","").strip()
                if not title:
                    continue

                nid = news_id(title)
                if nid in sent:
                    continue  # duplicate — skip

                msg = format_news(entry, source)
                success = send_msg(msg)

                if success:
                    sent.add(nid)
                    new_count += 1
                    time.sleep(2)  # rate limit ကာကွယ်

        except Exception as e:
            print(f"  ❌ {source['name']} error: {e}")

    save_sent(sent)
    print(f"  Done. {new_count} new articles posted.")

# ── MARKET OVERVIEW ──────────────────────────────────
def post_market_overview():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=bitcoin,ethereum,binancecoin,solana,ripple&order=market_cap_desc&sparkline=false&price_change_percentage=24h"
        r = requests.get(url, timeout=10)
        coins = r.json()

        g = requests.get("https://api.coingecko.com/api/v3/global", timeout=10).json()
        mcap = g["data"]["total_market_cap"]["usd"]
        vol  = g["data"]["total_volume"]["usd"]

        def fmt_price(p):
            if p >= 1000: return "$" + "{:,.0f}".format(p)
            if p >= 1:    return "$" + "{:.2f}".format(p)
            return "$" + "{:.4f}".format(p)

        def fmt_big(v):
            if v >= 1e12: return "${:.2f}T".format(v/1e12)
            if v >= 1e9:  return "${:.2f}B".format(v/1e9)
            return "${:.0f}M".format(v/1e6)

        lines = []
        for c in coins:
            chg = c.get("price_change_percentage_24h") or 0
            arrow = "🟢" if chg >= 0 else "🔴"
            lines.append("{} <b>{}</b> : {}  ({:+.1f}%)".format(
                arrow, c["symbol"].upper(), fmt_price(c["current_price"]), chg))

        fg_r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=8).json()
        fg_v = fg_r["data"][0]["value"]
        fg_l = fg_r["data"][0]["value_classification"]

        msg = (
            "📊 <b>Crypto Market Overview</b>\n\n" +
            "\n".join(lines) +
            "\n\n"
            "📈 Market Cap: <b>" + fmt_big(mcap) + "</b>\n"
            "💹 24h Volume: <b>" + fmt_big(vol) + "</b>\n\n"
            "⚡ Fear &amp; Greed: <b>" + fg_v + " — " + fg_l + "</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📡 Crypto Insider MM"
        )
        send_msg(msg)
        print("  ✅ Market overview posted")
    except Exception as e:
        print("  ❌ Market overview error: " + str(e))

# ── FEAR & GREED DAILY REPORT ─────────────────────────
def post_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=2", timeout=8)
        data = r.json()
        cur  = data["data"][0]
        prev = data["data"][1]
        v    = int(cur["value"])
        lbl  = cur["value_classification"]

        emoji = "😱" if v < 25 else "😨" if v < 45 else "😐" if v < 55 else "😏" if v < 75 else "🤑"
        bar_filled = int(v / 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)

        msg = (
            f"📊 <b>Crypto Fear &amp; Greed Index</b>\n\n"
            f"{emoji} <b>{v} — {lbl}</b>\n\n"
            f"[{bar}] {v}/100\n\n"
            f"Yesterday: {prev['value']} ({prev['value_classification']})\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📡 Crypto Insider MM | {datetime.now().strftime('%b %d, %Y')}"
        )
        send_msg(msg)
        print("  ✅ Fear & Greed posted")
    except Exception as e:
        print(f"  ❌ Fear & Greed error: {e}")

# ── STARTUP MESSAGE ───────────────────────────────────
def post_startup():
    msg = (
        f"🤖 <b>Crypto Insider MM Bot — Online</b>\n\n"
        f"✅ News auto-fetch: Every 1 hour\n"
        f"✅ Fear &amp; Greed: Daily 9:00 AM\n"
        f"✅ Sources: CoinTelegraph · CoinDesk · Decrypt · The Block · BeInCrypto · Bitcoin Magazine\n\n"
        f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📡 Crypto Insider MM"
    )
    send_msg(msg)

# ── SCHEDULE ──────────────────────────────────────────
def run():
    print("=" * 50)
    print("  Crypto Insider MM — Telegram News Bot")
    print("=" * 50)
    print(f"  Channel: {CHANNEL_ID}")
    print(f"  Sources: {len(RSS_SOURCES)}")
    print()

    # Startup message ပို့
    post_startup()

    # ချက်ချင်း ပထမဆုံး fetch
    post_market_overview()
    fetch_and_post()

    # Schedule
    schedule.every(1).hours.do(fetch_and_post)
    schedule.every(4).hours.do(post_market_overview)
    schedule.every().day.at("09:05").do(post_market_overview)
    schedule.every().day.at("09:00").do(post_fear_greed) # နေ့တိုင်း မနက် ၉နာရီ

    print("\nBot running... (Ctrl+C to stop)")
    print("Next fetch in 1 hour\n")

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    run()
