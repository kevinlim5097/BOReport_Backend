from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__, template_folder="templates")
CORS(app)

# === Telegram 配置 ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "your-local-token")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "your-local-chat-id")

# === Google Sheets 配置 ===
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "Daily Reports")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# === 自动切换 Google 认证模式 ===
if os.getenv("GOOGLE_CREDS_JSON"):  # Render 模式
    print("Using GOOGLE_CREDS_JSON from environment")
    google_creds = json.loads(os.getenv("GOOGLE_CREDS_JSON"))
    creds = Credentials.from_service_account_info(google_creds, scopes=SCOPES)
else:  # 本地模式
    print("Using backend/service_account.json from local file")
    creds = Credentials.from_service_account_file('backend/service_account.json', scopes=SCOPES)

# === 初始化 Google Sheets 客户端 ===
gs_client = gspread.authorize(creds)
sheet = gs_client.open(SPREADSHEET_NAME).sheet1

# === 前端页面 ===
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/summary")
def summary():
    return render_template("summary.html")

# === 提交报告接口 ===
@app.route("/submit-report", methods=["POST"])
def submit_report():
    payload = request.json
    data = payload.get("data")
    summary_text = payload.get("summaryText")

    if not data or not summary_text:
        return jsonify({"error": "Invalid payload"}), 400

    # 1. 发送到 Telegram
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(telegram_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": summary_text})

    # 2. 写入 Google Sheets
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
