import streamlit as st
import google.generativeai as genai
import os, random

# --- 1. 核心規範：視覺鎖定與 Apple 適配 [cite: 2026-02-03] ---
st.set_page_config(page_title="Lyu-Science-Cloud", layout="wide")
st.markdown("""
    <style>
    /* 強制全白背景、全黑文字、翩翩體 [cite: 2026-02-03] */
    .stApp, .main { background-color: white !important; color: black !important; font-family: 'HanziPen SC', '翩翩體', sans-serif; }
    /* 防止 Apple 設備自動黑底 [cite: 2026-02-03] */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: white !important; color: black !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 模型設定 (依據 image_b8ddb9.png) ---
API_KEY = "AIzaSyBEO5jqly5qFnjCGgzcs68O0iavJMrXl7k"
genai.configure(api_key=API_KEY)
MODEL = genai.GenerativeModel('gemini-2.5-flash') 

# --- 3. 曉臻助教 6 項核心 SOP [cite: 2026-02-03] ---
def generate_guide(page):
    intros = [
        "開課前拉拉筋，老師跑完馬拉松才來的，大家加油！",
        "熱身準備一下，上完這頁課老師就要去慢跑囉，運動對健康真的很重要！",
        "深呼吸三次，維持良好的代謝循環，腦袋才會清楚喔。"
    ]
    # 針對第 47 頁的珍珠邏輯轉譯示範 [cite: 2026-02-01]
    if page == 47:
        script = f"{random.choice(intros)} 各位同學，請翻到第 47 頁。什麼是莫耳？把它想成手搖飲的『一袋珍珠』。一莫耳就是 $6 \\times 10^{23}$ 個粒子。"
    else:
        script = f"{random.choice(intros)} 各位同學，請翻到第 {page} 頁。讓我們穩定配速，攻下這個理化重點！"
    return script

# --- 4. 雲端介面佈局 ---
st.title("🏃‍♀️ 曉臻助教：理化雲端教室 (Lyu-Science-Cloud)")

# 頁碼選擇器 [cite: 2026-02-03]
page_num = st.sidebar.number_input("請選擇講義頁碼", min_value=1, max_value=64, value=1)

if st.button("啟動曉臻老師導讀"):
    st.write("### 🗣️ 曉臻老師導讀腳本")
    st.success(generate_guide(page_num))
    st.caption("（聽不懂可以將進度條往回拉重複觀看喔！）")

# 顯示 PDF (從 data 資料夾讀取)
pdf_path = os.path.join("data", "二下第一章.pdf")
if os.path.exists(pdf_path):
    st.write(f"📖 目前正在閱讀：{pdf_path} 第 {page_num} 頁")
else:
    st.error("❌ 找不到教材檔案，請確認 data 資料夾內有『二下第一章.pdf』")