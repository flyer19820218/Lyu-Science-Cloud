import os, re, random
from flask import Flask, render_template_string, jsonify, send_from_directory
import google.generativeai as genai

app = Flask(__name__)

# --- 1. 核心參數與模型鎖定 (依據 image_b8ddb9.png) ---
API_KEY = "AIzaSyBEO5jqly5qFnjCGgzcs68O0iavJMrXl7k"
genai.configure(api_key=API_KEY)
MODEL = genai.GenerativeModel('gemini-2.5-flash') 

# --- 2. 曉臻助教 6 項核心指令 (SOP) [cite: 2026-02-03] ---
SYSTEM_PROMPT = """
你是一位資深理化老師。人設：助教曉臻，馬拉松選手 (PB 92分)。
視覺規範：背景全白、文字全黑、字體『HanziPen SC』 [cite: 2026-02-03]。

教學腳本規範：
1. 【熱身】：隨機 10-20 秒運動健康內容開場 [cite: 2026-02-03]。
2. 【導航】：開頭必說：『各位同學，請翻到第 X 頁。』 [cite: 2026-02-03]。
3. 【口語】：LaTeX 公式如 $n = \\frac{m}{M}$ 需轉為自然中文口語 [cite: 2026-02-03]。
4. 【設備】：加入 color-scheme: light 防止蘋果手機黑底 [cite: 2026-02-03]。
"""

# --- 3. 雲端發布介面 (適配雙模顯示) [cite: 2026-02-03] ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light">
    <style>
        body { 
            background-color: white !important; color: black !important; 
            font-family: 'HanziPen SC', '翩翩體', sans-serif; 
            margin: 0; padding: 20px;
        }
        .container { display: flex; flex-direction: column; max-width: 1200px; margin: auto; }
        @media (min-width: 768px) { .container { flex-direction: row; gap: 20px; } }
        .pdf-viewer { flex: 2; border: 1px solid #eee; background: white; text-align: center; }
        .guide-box { flex: 1; padding: 20px; background: #fafafa; border-radius: 12px; }
        img { max-width: 100%; height: auto; }
    </style>
</head>
<body>
    <h1>🏃‍♀️ Lyu-Science-Cloud：二下第一章</h1>
    <div class="container">
        <div class="pdf-viewer" id="page-img">
            <img src="/data/page_13.png" alt="講義第 13 頁">
        </div>
        <div class="guide-box">
            <h3>🗣️ 曉臻老師導讀</h3>
            <div id="script-content">{{ script_content }}</div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    # 修正語法錯誤，確保 script_content 正常顯示
    return render_template_string(HTML_TEMPLATE, script_content="準備好了嗎？請點擊頁碼，讓曉臻老師帶你熱身跑起來！")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))