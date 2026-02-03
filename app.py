import os, re, random
from flask import Flask, render_template_string, jsonify, request
import google.generativeai as genai

app = Flask(__name__)

# --- 1. 核心參數與模型鎖定 (依據清單校準) ---
API_KEY = "AIzaSyBEO5jqly5qFnjCGgzcs68O0iavJMrXl7k"
genai.configure(api_key=API_KEY)
# 使用指定的穩定大腦
MODEL = genai.GenerativeModel('gemini-2.5-flash') 

# --- 2. 曉臻助教 6 項核心提示規則 (SOP) ---
SYSTEM_PROMPT = """
你是一位資深理化老師。人設：助教曉臻，馬拉松選手 (PB 92分)，語氣溫馨專業。

教學規則：
1. 【開場】：隨機產出 10-20 秒運動健康內容 (如：拉筋、跑步益處)。
2. 【珍珠邏輯】：解釋莫耳數相關公式時，必須使用手搖飲珍珠邏輯。
3. 【導航】：腳本開頭必須說：『各位同學，請翻到第 X 頁。』。
4. 【口語轉譯】：LaTeX 公式如 $n = \\frac{m}{M}$ 必須在配音稿中轉成自然中文口語。
5. 【視覺規範】：全黑文字、白色背景、翩翩體 (HanziPen SC)。
"""

# --- 3. 手機與平板適配介面 (含蘋果防反黑補丁) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light">
    <title>Lyu-Science-Cloud</title>
    <style>
        body { 
            background-color: white !important; color: black !important; 
            font-family: 'HanziPen SC', '翩翩體', sans-serif; 
            margin: 0; padding: 20px;
        }
        /* 平板與手機雙模顯示 */
        .container { display: flex; flex-direction: column; max-width: 1200px; margin: auto; }
        @media (min-width: 768px) { .container { flex-direction: row; gap: 20px; } }
        .pdf-box { flex: 1; border: 1px solid #ddd; padding: 10px; background: white; }
        .guide-box { flex: 1; padding: 20px; background: #fdfdfd; border-radius: 10px; }
        .latex-text { font-weight: bold; color: black; }
    </style>
</head>
<body>
    <h1>🏃‍♀️ 曉臻助教：理化雲端馬拉松</h1>
    <div class="container">
        <div class="pdf-box">
            <h3>📖 教材頁面 (data/二下第一章.pdf)</h3>
            <div id="page-display">【正在讀取第 {{ page_num }} 頁...】</div>
        </div>
        <div class="guide-box">
            <h3>🗣️ 曉臻老師導讀</h3>
            <div id="script-content">{{ script_content }}</div>
            <hr>
            <button onclick="changePage(1)">下一頁</button>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, page_num=1, script