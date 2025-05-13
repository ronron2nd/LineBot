from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

genai.configure(api_key=GEMINI_API_KEY)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/")
def index():
    return "LINE BOT is running!"  # ← これが `/` にアクセスしたときの表示

@app.route("/api/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        prompt = f"""
        「{user_message}」について以下の内容を含む簡潔なレポートを作成してください：
        1. 概要（100文字程度）
        2. 主な特徴や重要なポイント（3-5点）
        3. 興味深い事実（2-3点）
        4. 関連するキーワード（3-5個）

        レポートは日本語で、全体で400-600文字程度にまとめてください。
        """
        response = model.generate_content(prompt)
        reply_text = response.text
    except Exception as e:
        reply_text = f"エラー: {str(e)}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# Flaskアプリとして認識させるために必要（Vercel）
app = app
