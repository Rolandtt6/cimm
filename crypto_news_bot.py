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
BOT_TOKEN  = os.environ.get('BOT_TOKEN')
GEMINI_KEY = os.environ.get('AQ.Ab8RN6LUCkqw1Hfbt8TMGNSVI8hqkN2EKVuGrqDHfeVqAZkZTw')
CHANNEL_ID = "-1003896067498"
SENT_FILE  = "sent_news.json"

# Gemini AI Client Setup (New Version)
client = None
if GEMINI_KEY:
    try:
        client = genai.Client(api_key=GEMINI_KEY)
    except Exception as e:
        print(f"❌ AI Setup Error: {e}")

# ── FUNCTIONS ─────────────────────────────────────────
def load_sent():
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r") as f:
                return set(json.load(f))
        except: return set()
    return set()

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent)[-500:], f)

def get_ai_summary(title):
    """Gemini AI ဖြင့် မြန်မာလို အနှစ်ချုပ်ခိုင်းခြင်း"""
    if not client:
        return None
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"Summarize this crypto news title in Burmese (professional and catchy for a news channel): {title}"
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ AI Processing Error: {e}")
        return None

def send_msg(text):
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN not found!")
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
