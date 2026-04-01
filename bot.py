import os
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
import asyncio

TG_TOKEN = os.environ.get("TG_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_KEY")
GS_URL = os.environ.get("GS_URL")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

app = Flask(__name__)
application = Application.builder().token(TG_TOKEN).build()

SYSTEM_PROMPT = """你是「小葵」，一個專屬於博奕平台客服團隊的 AI 助手。
你的工作是幫助客服人員快速解決工作上遇到的問題。
回覆風格：繁體中文，條理清晰，步驟用①②③列出，話術範本用【範本】標記，簡潔專業像資深同事。"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "你好！我是小葵🌻，你的專屬客服助手！\n\n"
        "直接輸入問題我就會回答，例如：\n"
        "• 主播投訴怎麼處理？\n"
        "• 週補貼活動規則是什麼？\n"
        "• 用戶態度很差怎麼應對？\n\n"
        "輸入 /查詢 用戶ID 可以查詢用戶活動狀態"
    )

async def query_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("請輸入用戶ID，例如：/查詢 U123456")
        return
    uid = context.args[0]
    await update.message.reply_text("🔍 查詢中...")
    try:
        res = requests.get(f"{GS_URL}?userId={uid}", timeout=10)
        data = res.json()
        if not data.get("found") or not data.get("records"):
            await update.message.reply_text(f"❌ 查無此用戶：{uid}")
            return
        records = data["records"]
        msg = f"✅ 用戶 {uid} 的活動記錄：\n\n"
        for r in records:
            msg += f"🎁 {r.get('activity','未知活動')}\n"
            if r.get('date'): msg += f"   登記日期：{r.get('date')}\n"
            if r.get('status'): msg += f"   狀態：{r.get('status')}\n"
            msg += "\n"
        await update.message.reply_text(msg)
    except:
        await update.message.reply_text("⚠️ 查詢失敗，請稍後再試")

async def ask_kuiki(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    await update.message.reply_text("🌻 小葵思考中...")
    try:
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}",
            json={"contents": [{"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\n用戶問題：" + question}]}]},
            timeout=30
        )
        data = res.json()
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        await update.message.reply_text(reply)
    except:
        await update.message.reply_text("⚠️ 小葵暫時無法回答，請稍後再試")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("查詢", query_user))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_kuiki))

@app.route(f"/{TG_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), application.bot)
    asyncio.run(application.process_update(update))
    return "ok"

@app.route("/")
def index():
    return "小葵機器人運行中 🌻"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    asyncio.run(application.bot.set_webhook(f"{WEBHOOK_URL}/{TG_TOKEN}"))
    app.run(host="0.0.0.0", port=port)
