import os
import re
from flask import Flask, render_template_string, jsonify
import google.generativeai as genai

app = Flask(__name__)

# --- 1. 核心參數與正版模型鎖定 ---
API_KEY = "AIzaSyBEO5jqly5qFnjCGgzcs68O0iavJMrXl7k"
genai.configure(api_key=API_KEY)
# 使用呂老師指定的正版大腦與特種產線 [cite: 2026-02-03]
BRAIN = genai.GenerativeModel('gemini-2.5-flash')
PRO_BRAIN = genai.GenerativeModel('gemini-2.5-pro')
BANANA_SPECIAL = genai.GenerativeModel('nano-banana-pro-preview')

# --- 2. 曉臻助教產線 6 項 API 核心指令 (SOP) [cite: 2026-02-03] ---
SYSTEM_PROMPT = """
你是一位資深理化老師。請閱讀講義 PDF 並產出教學內容。
人設：助教曉臻，馬拉松選手 (PB 92分)，語氣溫馨穩定 [cite: 2026-02-01]。

規範：
1. 視覺：背景全白、文字全黑、字體『HanziPen SC』(翩翩體) [cite: 2026-02-03]。
2. 開場：隨機 10-20 秒運動健康內容 [cite: 2026-02-03]。
3. 數學：嚴格使用 LaTeX。如 $n = \\frac{m}{M}$ 必須轉成中文口語『莫耳數等於質量除以分子量』。
4. 導航：必須說『各位同學，請翻到第 X 頁』 [cite: 2026-02-03]。
5. 設備：加入 color-scheme: light 防止蘋果手機黑底 [cite: 2026-02-03]。
"""

# --- 3. 雲端展示介面 (適配平板與手機) [cite: 2026-02-03] ---
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
            padding: 20px; line-height: 1.6;
        }
        .latex-area { background: white; padding: 10px; border-radius: 5px; }
        /* 手機與平板雙模顯示 [cite: 2026-02-03] */
        .container { display: flex; flex-direction: column; }
        @media (min-width: 768px) { .container { flex-direction: row; } }
    </style>
</head>
<body>
    <div class="container">
        <div id="pdf-viewer">【這裡顯示 PDF 頁面】</div>
        <div id="guide-content">
            <h2>🏃‍♀️ 曉臻助教馬拉松導讀</h2>
            <div id="script">載入中...</div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

# 測試：二下第一章第 13 頁質量守恆
@app.route('/api/guide/13')
def get_guide_page_13():
    # 這裡會產出包含 LaTeX 轉口語的腳本
    # $$CaCl_{2} + Na_{2}CO_{3} \rightarrow CaCO_{3} + 2NaCl$$
    spoken_text = "各位同學，請翻到第 13 頁。這是一個漂亮的沉澱反應，氯化鈣加上碳酸鈉，會產生白色的碳酸鈣沉澱喔！"
    return jsonify({"script": spoken_text})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))