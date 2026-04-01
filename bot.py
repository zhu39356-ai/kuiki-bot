import os
import requests
from flask import Flask, request, Response
import google.generativeai as genai
from telegram import Update, Bot
import asyncio
import json

TG_TOKEN = os.environ.get("TG_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_KEY")
GS_URL = os.environ.get("GS_URL")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

app = Flask(__name__)
bot = Bot(token=TG_TOKEN)

SYSTEM_PROMPT = """你是「小葵」，一個專屬於博奕平台客服團隊的 AI 助手。
你的工作是幫助客服人員快速解決工作上遇到的問題。
回覆風格：繁體中文，條理清晰，步驟用①②③列出，話術範本用【範本】標記，簡潔專業像資深同事。"""

def ask_gemini(question):
    try:
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}",
            json={"contents": [{"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\n用戶問題：" + question}]}]},
            timeout=30
        )
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "⚠️ 小葵暫時無法回答，請稍後再試"

def query_user(uid):
    try:
        res = requests.get(f"{GS_URL}?userId={uid}", timeout=10)
        data = res.json()
        if not data.get("found") or not data.get("records"):
            return f"❌ 查無此用戶：{uid}\n請確認ID是否正確"
        records = data["records"]
        msg = f"✅ 用戶 {uid} 的活動記錄：\n\n"
        for r in records:
            msg += f"🎁 {r.get('activity','未知活動')}\n"
            if r.get('date'): msg += f"   登記日期：{r.get('date')}\n"
            if r.get('status'): msg += f"   狀態：{r.get('status')}\n"
            msg += "\n"
        return msg
    except:
        return "⚠️ 查詢失敗，請稍後再試"

@app.route(f"/{TG_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" not in data:
        return "ok"
    
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")
    
    if text == "/start":
        reply = "你好！我是小葵🌻，你的專屬客服助手！\n\n直接輸入問題我就會回答，例如：\n• 主播投訴怎麼處理？\n• 週補貼活動規則是什麼？\n• 用戶態度很差怎麼應對？\n\n輸入 /查詢 用戶ID 可以查詢用戶活動狀態"
    elif text.startswith("/查詢"):
        parts = text.split()
        if len(parts) < 2:
            reply = "請輸入用戶ID，例如：/查詢 U123456"
        else:
            reply = query_user(parts[1])
    else:
        reply = ask_gemini(text)
    
    asyncio.run(bot.send_message(chat_id=chat_id, text=reply))
    return "ok"

@app.route("/set_webhook")
def set_webhook():
    asyncio.run(bot.set_webhook(f"{WEBHOOK_URL}/{TG_TOKEN}"))
    return "Webhook set!"

@app.route("/")
def index():
    return "小葵機器人運行中 🌻"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
```

同時更新 `requirements.txt`：
```
python-telegram-bot==20.7
requests==2.31.0
flask==3.0.0
