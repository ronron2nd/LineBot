from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler as LineWebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import date

# .env ファイル読み込み（ローカル開発用、Vercel では環境変数を設定）
load_dotenv()

app = Flask(__name__)

# 環境変数の取得
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# LINE・Gemini API の初期化
genai.configure(api_key=GEMINI_API_KEY)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
line_handler = LineWebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/")
def index():
    return "LINE BOT is running!"

@app.route("/api/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@app.route("/broadcast", methods=["POST"])
def broadcast():
    today = date.today()
    today_str = today.strftime("%-m月%-d日")  # 例: 5月24日

    try:
        # Gemini で雑学を生成
        model = genai.GenerativeModel('gemini-2.0-flash-exp')  # 高精度モデルに変更も可
        prompt = f"""
        今日は{today_str}です。この日に関する日本の雑学・記念日・歴史的な出来事・文化などを親しみやすく簡潔に紹介してください。
        
        ・最初に「{today_str}は〜の日です」などと主題を明確に書いてください。
        ・前置きや余談は書かないでください。
        ・読みやすく簡単な日本語で、200文字程度にまとめてください。
        """
        response = model.generate_content(prompt)
        trivia_text = response.text.strip()

        # 挨拶メッセージを先頭に追加
        greeting = f"おはようございます！\n今日は{today_str}です！\n\n"
        full_message = greeting + trivia_text

        # LINE に一斉送信
        line_bot_api.broadcast(TextSendMessage(text=full_message))
        return "Trivia with greeting broadcasted", 200

    except Exception as e:
        return f"Error: {str(e)}", 500


@line_handler.add(MessageEvent, message=TextMessage)
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

# Vercel に Flask アプリケーションを明示的に渡す
app = app
