#!/usr/bin/env python3
"""
Crypto Insider MM — Telegram News Bot (GitHub Actions Optimized)
============================================================
သတင်းတွေ auto fetch ပြီး Telegram channel မှာ post လုပ်ပေးတယ်
GitHub Actions အတွက် while loop ဖြုတ်ထားပြီး Secret Token သုံးထားတယ်
"""

import requests
import feedparser
import time
import json
import os
import hashlib
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────
# GitHub Settings > Secrets and variables > Actions ထဲမှာ BOT_TOKEN ထည့်ထားပေးရမယ်
BOT_TOKEN  = os.environ.get('BOT_TOKEN') 
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

BREAKING_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "xrp", "ripple",
    "solana", "sol", "etf", "sec", "fed", "crash", "surge",
    "hack", "liquidat", "ath", "all-time high", "rally"
]

# ── SENT HISTORY ──────────────────────────────────────
def load_sent():
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent)[-500:], f)

def news_id(title):
    return hashlib.md5(title.encode()).hexdigest()[:12]

# ── TELEGRAM SEND ─────────────────────────────────────
def send_msg(text):
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN not found in environment variables!")
        return False
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            print(f"  ✅ Sent: {text[:50]}...")
            return True
        else:
            print(f"  ❌ Error {r.status_code}: {r.text[:100]}")
            return False
    except Exception as e:
        print(f"  ❌ Network error: {e}")
        return False

# ── UTILS ─────────────────────────────────────────────
def get_sentiment(title):
    t = title.lower()
    bull = ["surge","soar","rally","gain","bull","rise","record","pump","approve","etf","breakout","ath","launch","adoption","high"]
    bear = ["crash","drop","fall","bear","dump","fear","hack","ban","plunge","collapse","scam","liquidat","warn","risk","low"]
    for w in bull:
        if w in t: return "📈 Bullish"
    for w in bear:
        if w in t: return "📉 Bearish"
    return "📊 Neutral"

def is_breaking(title):
    return any(kw in title.lower() for kw in BREAKING_KEYWORDS)

def format_news(item, source):
    sentiment = get_sentiment(item.get("title",""))
    breaking  = "🚨 BREAKING NEWS\n\n" if is_breaking(item.get("title","")) else ""
    title     = item.get("title","").strip()
    link      = item.get("link","").strip()
    pub_date  = item.get("published","")

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

# ── FETCH & POST ──────────────────────────────────────
def fetch_and_post():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Fetching news...")
    sent = load_sent()
    new_count = 0

    for source in RSS_SOURCES:
        try:
            print(f"  Fetching {source['name']}...")
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:5]:
                title = entry.get("title","").strip()
                if not title: continue
                
                nid = news_id(title)
                if nid in sent: continue

                msg = format_news(entry, source)
                if send_msg(msg):
                    sent.add(nid)
                    new_count += 1
                    time.sleep(1)
        except Exception as e:
            print(f"  ❌ {source['name']} error: {e}")

    save_sent(sent)
    print(f"  Done. {new_count} new articles posted.")

# ── MARKET & FEAR/GREED ──────────────────────────────
def post_market_overview():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=bitcoin,ethereum,binancecoin,solana,ripple&order=market_cap_desc"
        coins = requests.get(url, timeout=10).json()
        
        lines = []
        for c in coins:
            chg = c.get("price_change_percentage_24h") or 0
            arrow = "🟢" if chg >= 0 else "🔴"
            lines.append(f"{arrow} <b>{c['symbol'].upper()}</b>: ${c['current_price']:,} ({chg:+.1f}%)")

        msg = (
            "📊 <b>Market Overview</b>\n\n" + "\n".join(lines) + 
            "\n\n━━━━━━━━━━━━━━━━━━\n📡 Crypto Insider MM"
        )
        send_msg(msg)
    except Exception as e:
        print(f"  ❌ Market error: {e}")

def post_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=8).json()
        v = r["data"][0]["value"]
        l = r["data"][0]["value_classification"]
        msg = f"📊 <b>Fear & Greed Index: {v} - {l}</b>\n━━━━━━━━━━━━━━━━━━\n📡 Crypto Insider MM"
        send_msg(msg)
    except Exception as e:
        print(f"  ❌ F&G error: {e}")

# ── MAIN EXECUTION ────────────────────────────────────
def main():
    print("🚀 Bot Execution Started")
    
    # ၁။ သတင်းအသစ်များတင်ခြင်း
    fetch_and_post()
    
    # ၂။ အချိန်အလိုက် Market Overview တင်ခြင်း (ဥပမာ- ၄ နာရီတစ်ခါ)
    current_hour = datetime.now().hour
    if current_hour % 4 == 0:
        post_market_overview()
        
    # ၃။ နေ့စဉ် Fear & Greed (မြန်မာစံတော်ချိန် မနက် ၉ နာရီ = UTC 2:30 AM ခန့်)
    if current_hour == 2:
        post_fear_greed()
        
    print("🏁 Bot Execution Finished")

if __name__ == "__main__":
    main()
