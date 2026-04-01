import os
import requests
from flask import Flask, request
import asyncio

TG_TOKEN = os.environ.get("TG_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_KEY")
GS_URL = os.environ.get("GS_URL")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

app = Flask(__name__)

SYSTEM_PROMPT = """你是「小葵」，一個專屬於博奕平台客服團隊的 AI 助手。
你的工作是幫助客服人員快速解決工作上遇到的問題。
回覆風格：繁體中文，條理清晰，步驟用①②③列出，話術範本用【範本】標記，簡潔專業像資深同事。"""

def send_message(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10
    )

def ask_gemini(question):
    try:
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}",
            json={"contents": [{"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\n用戶問題：" + question}]}]},
            timeout=30
        )
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
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
    if not data or "message" not in data:
        return "ok"
    
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")
    
    if text == "/start":
        reply = (
            "你好！我是小葵🌻，你的專屬客服助手！\n\n"
            "直接輸入問題我就會回答，例如：\n"
            "• 主播投訴怎麼處理？\n"
            "• 週補貼活動規則是什麼？\n"
            "• 用戶態度很差怎麼應對？\n\n"
            "輸入 /query 用戶ID 可以查詢用戶活動狀態\n"
            "例如：/query U123456"
        )
    elif text.startswith("/query"):
        parts = text.split()
        if len(parts) < 2:
            reply = "請輸入用戶ID，例如：/query U123456"
        else:
            reply = query_user(parts[1])
    elif text.startswith("/"):
        reply = "未知指令，直接輸入問題就好 😊"
    else:
        reply = ask_gemini(text)
    
    send_message(chat_id, reply)
    return "ok"

@app.route("/set_webhook")
def set_webhook():
    url = f"{WEBHOOK_URL}/{TG_TOKEN}"
    res = requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/setWebhook",
        json={"url": url}
    )
    return f"Webhook set: {res.json()}"

@app.route("/")
def index():
    return "小葵機器人運行中 🌻"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

