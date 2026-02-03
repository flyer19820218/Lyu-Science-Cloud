import streamlit as st
import google.generativeai as genai
import os, asyncio, edge_tts, re, base64, io, random
from PIL import Image

# --- 零件檢查 ---
try:
    import fitz
except ImportError:
    st.error("❌ 零件缺失！請確保 requirements.txt 已加入 pymupdf 與 edge-tts。")
    st.stop()

# --- 1. 核心規範：視覺鎖定與 Apple 適配 (深度白晝協議) ---
st.set_page_config(page_title="Lyu-Science-Cloud", layout="wide")

st.markdown("""
    <style>
    /* 全黑文字、白色背景、翩翩體鎖定 */
    html, body, .stApp, [data-testid="stAppViewContainer"], .stMain {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif !important;
    }
    
    /* 平板手機雙模：解決「字沒上去」的動態字體與行高 */
    .stMarkdown, p, span, label, li {
        color: #000000 !important;
        font-size: calc(1rem + 0.4vw) !important;
        line-height: 1.6 !important;
    }

    /* 修正指南方塊：確保文字不重疊，背景不反黑 */
    .guide-box { 
        border: 2px dashed #01579b; 
        padding: 1.5rem; 
        border-radius: 15px; 
        background-color: #f0f8ff !important; 
        color: #000000 !important;
        margin-bottom: 25px;
        width: 100%;
    }
    
    /* Apple 設備防反黑補丁 */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
        .guide-box { background-color: #f0f8ff !important; color: #000000 !important; }
    }
    </style>
    <meta name="color-scheme" content="light">
""", unsafe_allow_html=True)

# --- 2. 曉臻語音引擎 (口語轉譯) ---
async def generate_voice_base64(text):
    # 清除劇本殘留符號，讓曉臻只唸口語中文
    clean_text = re.sub(r'[^\w\u4e00-\u9fff\d，。！？「」]', '', text)
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 曉臻馬拉松助教版：核心 API 通行證指南 ---
st.title("🚀 曉臻馬拉松助教版")
st.markdown("""
<div class="guide-box">
    <b>📖 學生快速通行指南：</b><br>
    1. 前往 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 並登入。<br>
    2. 點擊 <b>Create API key</b>，<b>務必勾選兩次同意條款</b>。<br>
    3. 貼回下方「通行證」欄位按 Enter 邀請曉臻助教。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 通行證輸入區：", type="password")
st.divider()

# --- 4. 曉臻助教 6 項核心 API SOP (提示詞鎖定) ---
SYSTEM_PROMPT = """
你是資深理化助教曉臻。人設：馬拉松選手 (PB 92分)，語音溫和穩定。