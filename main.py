from fastapi import FastAPI, Request, HTTPException
from linebot import WebhookHandler, LineBotApi
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import google.generativeai as genai

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# 環境変数
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

genai.configure(api_key=GEMINI_API_KEY)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


def generate_report_with_gemini(keyword: str) -> str:
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        prompt = f"""
        「{keyword}」について以下の内容を含む簡潔なレポートを作成してください：
        1. 概要（100文字程度）
        2. 主な特徴や重要なポイント（3-5点）
        3. 興味深い事実（2-3点）
        4. 関連するキーワード（3-5個）

        レポートは日本語で、全体で400-600文字程度にまとめてください。
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"レポート生成エラー: {str(e)}"


@app.post("/api/webhook")
async def webhook(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()

    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_message = event.message.text
    try:
        report = generate_report_with_gemini(user_message)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=report)
        )
    except Exception as e:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"エラー: {str(e)}")
        )
