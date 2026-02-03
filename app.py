import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF 處理 PDF 視力 [cite: 2026-02-03]
from PIL import Image
import os, random, io

# --- 1. 核心規範：視覺鎖定與 Apple 適配 [cite: 2026-02-03] ---
st.set_page_config(page_title="Lyu-Science-Cloud", layout="wide")
st.markdown("""
    <style>
    /* 全黑文字、白色背景、翩翩體 [cite: 2026-02-03] */
    .stApp, .main, div[data-testid="stVerticalBlock"] { 
        background-color: white !important; color: black !important; 
        font-family: 'HanziPen SC', '翩翩體', sans-serif; 
    }
    /* 蘋果設備防反黑 [cite: 2026-02-03] */
    @media (prefers-color-scheme: dark) { .stApp { background-color: white !important; color: black !important; } }
    </style>
""", unsafe_allow_html=True)

# --- 2. 模型設定 (依據 image_b8ddb9.png) ---
API_KEY = "AIzaSyBEO5jqly5qFnjCGgzcs68O0iavJMrXl7k"
genai.configure(api_key=API_KEY)
MODEL = genai.GenerativeModel('gemini-2.5-flash') 

# --- 3. 曉臻助教 6 項核心 SOP 指令 [cite: 2026-02-03] ---
SYSTEM_PROMPT = """
你是一位資深理化老師。人設：助教曉臻，馬拉松選手 (PB 92分)，語氣溫馨專業 [cite: 2026-02-01]。
1. 開場：隨機產出 10-20 秒運動健康內容。
2. 導航：必說『各位同學，請翻到第 X 頁』 [cite: 2026-02-03]。
3. 珍珠邏輯：解釋莫耳數相關公式時，必須使用珍珠奶茶邏輯 [cite: 2026-02-01]。
4. 口語轉譯：LaTeX 公式必須轉為自然中文口語，例如 $n = m/M$ 讀作『莫耳數等於質量除以分子量』 [cite: 2026-02-03]。
"""

st.title("🏃‍♀️ 曉臻助教：理化雲端教室 (Lyu-Science-Cloud)")

# --- 4. 讀取與渲染 PDF (高畫質 300 DPI) [cite: 2026-02-03] ---
pdf_path = os.path.join("data", "二下第一章.pdf")

if os.path.exists(pdf_path):
    doc = fitz.open(pdf_path)
    page_count = doc.page_count
    
    # 頁碼選擇器
    page_num = st.sidebar.number_input("請選擇講義頁碼", 1, page_count, 1)
    
    # 將 PDF 轉為高畫質圖片 [cite: 2026-02-03]
    page = doc.load_page(page_num - 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 放大兩倍保證清晰
    img_data = Image.open(io.BytesIO(pix.tobytes()))
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"📖 講義第 {page_num} 頁")
        st.image(img_data, use_column_width=True) # 顯示高畫質 PDF 畫面
        
    with col2:
        st.subheader("🗣️ 曉臻老師導讀")
        if st.button("啟動 AI 導讀解說"):
            # 真正的 API 連線：讓 Gemini 看著這張圖片生成腳本 [cite: 2026-02-03]
            with st.spinner("曉臻正在準備馬拉松熱身與講稿..."):
                response = MODEL.generate_content([
                    f"{SYSTEM_PROMPT}\n請針對這頁教材內容產出第 {page_num} 頁的導讀稿。",
                    img_data
                ])
                st.success(response.text)
                st.caption("（聽不懂可以將進度條往回拉重複觀看喔！）")
else:
    st.error(f"❌ 找不到教材檔案，請確認 data 資料夾內有『{pdf_path}』")