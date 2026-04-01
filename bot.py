import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

TG_TOKEN = os.environ.get("TG_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_KEY")
GS_URL = os.environ.get("GS_URL")

SYSTEM_PROMPT = """你是「小葵」，一個專屬於博奕平台客服團隊的 AI 助手。
你的工作是幫助客服人員快速解決工作上遇到的問題。
回覆風格：繁體中文，條理清晰，步驟用①②③列出，話術範本用【範本】標記，簡潔專業像資深同事。"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "你好！我是小葵🌻，你的專屬客服助手！\n\n"
        "你可以直接問我問題，例如：\n"
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
    await update.message.reply_text(f"🔍 查詢中...")
    try:
        res = requests.get(f"{GS_URL}?userId={uid}", timeout=10)
        data = res.json()
        if not data.get("found") or not data.get("records"):
            await update.message.reply_text(f"❌ 查無此用戶：{uid}\n請確認ID是否正確，或此用戶尚未登記任何活動")
            return
        records = data["records"]
        msg = f"✅ 用戶 {uid} 的活動記錄：\n\n"
        for r in records:
            msg += f"🎁 {r.get('activity','未知活動')}\n"
            if r.get('date'): msg += f"   登記日期：{r.get('date')}\n"
            if r.get('status'): msg += f"   狀態：{r.get('status')}\n"
            if r.get('amount'): msg += f"   申請金額：{r.get('amount')}\n"
            msg += "\n"
        await update.message.reply_text(msg)
    except Exception as e:
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
    except Exception as e:
        await update.message.reply_text("⚠️ 小葵暫時無法回答，請稍後再試")

def main():
    app = Application.builder().token(TG_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("查詢", query_user))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_kuiki))
