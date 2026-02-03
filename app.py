import os
import re
from flask import Flask, render_template, jsonify
import google.generativeai as genai

app = Flask(__name__)

# --- 1. 核心參數與模型設定 (依據清單鎖定) ---
API_KEY = "AIzaSyBEO5jqly5qFnjCGgzcs68O0iavJMrXl7k"
genai.configure(api_key=API_KEY)
# 使用呂老師指定的穩定大腦 [cite: 2026-02-03]
MODEL = genai.GenerativeModel('gemini-2.5-pro')

# --- 2. 曉臻助教產線 6 項 API 核心指令 (SOP) [cite: 2026-02-03] ---
SYSTEM_PROMPT = """
你是一位資深理化老師。請閱讀教材 PDF 並產出教學腳本。
人設鎖定：助教曉臻，馬拉松選手 (PB 92分)，語氣溫馨專業 [cite: 2026-02-01]。

導讀規範：
1. 【開場】：隨機產出 10-20 秒運動健康內容 (如：拉筋、慢跑益處) [cite: 2026-02-03]。
2. 【導航】：必須包含『各位同學，請翻到第 X 頁』 [cite: 2026-02-03]。
3. 【口語化】：LaTeX 公式如 $n = \\frac{m}{M}$ 需轉為『莫耳數等於質量除以分子量』 [cite: 2026-02-03]。
4. 【風格】：全黑文字、白色背景、翩翩體思維。
"""

@app.route('/')
def index():
    # 這裡加入蘋果設備防反黑與手機適配的 HTML [cite: 2026-02-03]
    return """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="color-scheme" content="light">
        <title>Lyu-Science-Cloud</title>
        <style>
            body { 
                background-color: white; color: black; 
                font-family: 'HanziPen SC', '翩翩體', sans-serif; 
                margin: 20px;
            }
            .page-container { border: 1px solid #eee; padding: 15px; }
            /* 平板與手機雙模顯示 [cite: 2026-02-03] */
            @media (min-width: 768px) { .main { display: flex; } }
        </style>
    </head>
    <body>
        <h1>🏃‍♀️ 曉臻助教：理化馬拉松雲端教室</h1>
        <div id="content"></div>
    </body>
    </html>
    """

# 這裡是生成每一頁導讀的 API [cite: 2026-02-03]
@app.route('/generate_guide/<int:page_num>')
def generate_guide(page_num):
    # 此處會呼叫 Gemini 讀取 PDF 內容並生成曉臻腳本
    # 範例輸出：
    guide_text = f"曉臻：『開課前拉拉筋！老師跑完馬拉松才來的。各位同學，請翻到第 {page_num} 頁...』"
    return jsonify({"script": guide_text})

if __name__ == "__main__":
    app.run(debug=True, port=5000)