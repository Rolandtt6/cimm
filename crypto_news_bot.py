#!/usr/bin/env python3
"""
Crypto Insider MM — AI Powered News Bot
=======================================
သတင်းတွေကို Fetch လုပ်ပြီး Gemini AI နဲ့ မြန်မာလို အနှစ်ချုပ်ပေးသည်
"""

import requests
import feedparser
import time
import json
import os
import hashlib
import google.generativeai as genai
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────
BOT_TOKEN  = os.environ.get('BOT_TOKEN')
GEMINI_KEY = os.environ.get('AQ.Ab8RN6LUCkqw1Hfbt8TMGNSVI8hqkN2EKVuGrqDHfeVqAZkZTw') # [Api ထည့်ရန်]
CHANNEL_ID = "-1003896067498"
SENT_FILE  = "sent_news.json"

# Gemini AI Setup
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# ── RSS SOURCES ───────────────────────────────────────
RSS_SOURCES = [
    {"name": "CoinTelegraph", "url": "https://cointelegraph.com/rss", "emoji": "📰"},
    {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "emoji": "📊"},
    {"name": "Decrypt", "url": "https://decrypt.co/feed", "emoji": "🔓"},
    {"name": "The Block", "url": "https://www.theblock.co/rss.xml", "emoji": "⛓️"},
    {"name": "BeInCrypto", "url": "https://beincrypto.com/feed/", "emoji": "🌐"},
    {"name": "Bitcoin Mag", "url": "https://bitcoinmagazine.com/feed", "emoji": "₿"},
]

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
    """Gemini AI ကိုသုံးပြီး သတင်းကို မြန်မာလို အနှစ်ချုပ်ခိုင်းခြင်း"""
    if not model:
        return None
    
    prompt = f"Summarize this crypto news title in Burmese (professional and catchy for social media): {title}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"  ❌ AI Error: {e}")
        return None

def send_msg(text):
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN not found!")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=15)
        return r.status_code == 200
    except: return False

def fetch_and_post():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching news...")
    sent = load_sent()
    new_count = 0

    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:3]: # RSS တစ်ခုချင်းစီမှ နောက်ဆုံး ၃ ခုယူမည်
                title = entry.get("title","").strip()
                nid = hashlib.md5(title.encode()).hexdigest()[:12]
                
                if nid in sent: continue

                # AI မြန်မာလို အနှစ်ချုပ်ယူခြင်း
                burmese_summary = get_ai_summary(title)
                
                msg = (
                    f"{source['emoji']} <b>{source['name']}</b>\n\n"
                    f"🇲🇲 <b>{burmese_summary if burmese_summary else title}</b>\n\n"
                    f"🔗 <a href='{entry.link}'>Read Full Article</a>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"📡 Crypto Insider MM"
                )
                
                if send_msg(msg):
                    sent.add(nid)
                    new_count += 1
                    time.sleep(2) # Rate limit ရှောင်ရန်
        except Exception as e:
            print(f"  ❌ {source['name']} fetch error: {e}")
            continue

    save_sent(sent)
    print(f"  Done. {new_count} new articles posted.")

def post_market_overview():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=bitcoin,ethereum,binancecoin,solana,ripple"
        coins = requests.get(url, timeout=10).json()
        lines = [f"📊 <b>Market Overview</b>\n"]
        for c in coins:
            chg = c.get("price_change_percentage_24h") or 0
            arrow = "🟢" if chg >= 0 else "🔴"
            lines.append(f"{arrow} {c['symbol'].upper()}: ${c['current_price']:,} ({chg:+.1f}%)")
        send_msg("\n".join(lines))
    except: pass

# ── MAIN ──────────────────────────────────────────────
def main():
    print("🚀 Bot Execution Started")
    
    # ၁။ သတင်းများ AI နဲ့ အနှစ်ချုပ်ပြီး တင်ခြင်း
    fetch_and_post()
    
    # ၂။ အချိန်အလိုက် Market Overview တင်ခြင်း (ဥပမာ- ၄ နာရီတစ်ခါ)
    current_hour = datetime.now().hour
    if current_hour % 4 == 0:
        post_market_overview()
        
    print("🏁 Bot Execution Finished")

if __name__ == "__main__":
    main()
