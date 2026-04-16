#!/usr/bin/env python3
import os
import requests
import feedparser
import time
import json
import hashlib
from datetime import datetime
from google import genai

# ── CONFIG ────────────────────────────────────────────
# GitHub Secrets မှ Variable နာမည်များကိုသာ အသုံးပြုထားပါသည်
BOT_TOKEN  = os.environ.get('BOT_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
CHANNEL_ID = "-1003896067498"
SENT_FILE  = "sent_news.json"

# Gemini AI Client Setup
client = None
if GEMINI_KEY:
    try:
        client = genai.Client(api_key=GEMINI_KEY)
    except Exception as e:
        print(f"❌ AI Setup Error: {e}")

# ... (ကျန်သော function များသည် မူလအတိုင်း မှန်ကန်ပါသည်) ...

def send_msg(text):
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN not found! Please check GitHub Secrets.")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            print(f"✅ Posted successfully")
            return True
        else:
            print(f"❌ Telegram Error: {r.text}")
            return False
    except Exception as e:
        print(f"❌ Network Error: {e}")
        return False

# ... (ကျန်သော code များသည် အဆင်ပြေပါသည်) ...

def fetch_and_post():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching news...")
    sent = load_sent()
    
    rss_sources = [
        {"name": "CoinTelegraph", "url": "https://cointelegraph.com/rss", "emoji": "📰"},
        {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "emoji": "📊"},
        {"name": "Decrypt", "url": "https://decrypt.co/feed", "emoji": "🔓"},
        {"name": "The Block", "url": "https://www.theblock.co/rss.xml", "emoji": "⛓️"}
    ]

    new_count = 0
    for source in rss_sources:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:3]:
                title = entry.get("title","").strip()
                nid = hashlib.md5(title.encode()).hexdigest()[:12]
                
                if nid in sent: continue

                burmese_summary = get_ai_summary(title)
                
                msg = (
                    f"{source['emoji']} <b>{source['name']}</b>\n\n"
                    f"🇲🇲 <b>{burmese_summary if burmese_summary else title}</b>\n\n"
                    f"🔗 <a href='{entry.link}'>မူရင်းဖတ်ရန်</a>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"📡 Crypto Insider MM"
                )
                
                if send_msg(msg):
                    sent.add(nid)
                    new_count += 1
                    time.sleep(2) 
        except Exception as e:
            print(f"❌ {source['name']} fetch error: {e}")
            continue

    save_sent(sent)
    print(f"🏁 Done. {new_count} new articles posted.")

def main():
    print("🚀 Bot Execution Started")
    fetch_and_post()
    print("🏁 Bot Execution Finished")

if __name__ == "__main__":
    main()
