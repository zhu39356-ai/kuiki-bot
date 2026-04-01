import os
import requests
from flask import Flask, request

TG_TOKEN = os.environ.get("TG_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_KEY")
GS_URL = os.environ.get("GS_URL")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

app = Flask(__name__)

SYSTEM_BASE = """你是「小葵」，一个专属于博彩平台客服团队的贴心助手。

【小葵的个性】
你是一位有5年经验的资深客服姐姐，天秤座，做事公平公正、善于沟通。
你亲切温暖但做事俐落，不管多复杂的问题都不慌张。
你说话有条理，遇到问题会给清晰的步骤，偶尔用🌻表情但不过度。
你像同事身边最可靠的伙伴，口头禅是「交给小葵就好🌻」

【回复规则】
- 步骤用①②③列出
- 话术范本用【范本】标记，方便直接复制使用
- 简洁专业，不废话
- 语气像在跟同事说话，不像冷冰冰的机器人"""

def get_knowledge():
    try:
        res = requests.get(GS_URL + "?action=getKnowledge", timeout=10)
        data = res.json()
        if isinstance(data, list) and len(data) > 0:
            kb = "\n\n".join([f"【{k.get('title','')}】\n{k.get('content','')}" for k in data])
            return SYSTEM_BASE + "\n\n以下是你的知识库，回答时优先参考这些内容：\n\n" + kb
    except:
        pass
    return SYSTEM_BASE

def send_message(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10
    )

def ask_gemini(question):
    try:
        system = get_knowledge()
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-04-17:generateContent?key={GEMINI_KEY}",
            json={"contents": [{"role": "user", "parts": [{"text": system + "\n\n用户问题：" + question}]}]},
            timeout=30
        )
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return "小葵暂时无法回答，请稍后再试 😊"

def query_user(uid):
    try:
        res = requests.get(f"{GS_URL}?userId={uid}", timeout=10)
        data = res.json()
        if not data.get("found") or not data.get("records"):
            return f"查无此用户：{uid}\n请确认ID是否正确，或此用户尚未登记任何活动"
        records = data["records"]
        msg = f"用户 {uid} 的活动记录：\n\n"
        for r in records:
            msg += f"活动：{r.get('activity','未知活动')}\n"
            if r.get('date'):
                msg += f"登记日期：{r.get('date')}\n"
            if r.get('status'):
                msg += f"状态：{r.get('status')}\n"
            if r.get('amount'):
                msg += f"申请金额：{r.get('amount')}\n"
            msg += "\n"
        return msg
    except:
        return "查询失败，请稍后再试"

@app.route(f"/{TG_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data or "message" not in data:
        return "ok"

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    if text == "/start":
        reply = (
            "你好！我是小葵🌻\n\n"
            "有什么问题尽管问我，例如：\n"
            "• 主播投诉怎么处理？\n"
            "• 周补贴活动规则是什么？\n"
            "• 用户态度很差怎么应对？\n\n"
            "查询用户活动：\n"
            "/query 用户ID\n"
            "例如：/query U123456\n\n"
            "交给小葵就好🌻"
        )
    elif text.startswith("/query"):
        parts = text.split()
        if len(parts) < 2:
            reply = "请输入用户ID，例如：/query U123456"
        else:
            reply = query_user(parts[1])
    elif text.startswith("/"):
        reply = "直接输入问题就好，不需要指令 😊"
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
    return "小葵机器人运行中 🌻"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
