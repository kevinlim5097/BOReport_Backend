from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import gspread
from google.oauth2.service_account import Credentials
import os
import json

app = Flask(__name__)
CORS(app)

# === Telegram 配置（从环境变量读取，若无则写死测试用值）===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "your-telegram-bot-token")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "your-telegram-chat-id")

# === Google Sheets 配置 ===
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "Daily Reports")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# === Google 凭证：自动切换模式 ===
if os.getenv("GOOGLE_CREDENTIALS_JSON"):
    # 云端模式：从环境变量读取
    google_creds = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
    creds = Credentials.from_service_account_info(google_creds, scopes=SCOPES)
else:
    # 本地模式：直接读取文件
    creds = Credentials.from_service_account_file('backend/service_account.json', scopes=SCOPES)

# === 连接 Google Sheets ===
gs_client = gspread.authorize(creds)
sheet = gs_client.open(SPREADSHEET_NAME).sheet1  # 使用第一个工作表

@app.route("/submit-report", methods=["POST"])
def submit_report():
    print("=== 收到请求 ===")
    print(request.json)

    payload = request.json
    data = payload.get("data")
    summary_text = payload.get("summaryText")

    if not data or not summary_text:
        return jsonify({"error": "Invalid payload"}), 400

    # === 1. 发送到 Telegram ===
    try:
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(telegram_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": summary_text})
    except Exception as e:
        return jsonify({"error": f"Failed to send Telegram message: {str(e)}"}), 500

    # === 2. 写入 Google Sheets ===
    try:
        sheet.append_row([
            data.get("location"),
            data.get("date"),
            data.get("closingPerson"),
            data.get("sales"),
            data.get("credit"),
            data.get("debit"),
            data.get("tng"),
            data.get("bankAtm"),
            data.get("cash"),
            data.get("breadSell"),
            data.get("breadLeft"),
            data.get("breadLeftCollected"),
            data.get("eggTart"),
            data.get("birthdayCake")
        ])
    except Exception as e:
        return jsonify({"error": f"Failed to write to Google Sheets: {str(e)}"}), 500

    return jsonify({"status": "ok", "message": "Report sent to Telegram & Google Sheets"})

@app.route("/")
def home():
    return "Flask backend is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
