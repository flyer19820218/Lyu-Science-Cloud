import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
from PIL import Image
import os, random, io

# --- 1. 核心規範：視覺鎖定與 Apple 防反黑補丁 ---
st.set_page_config(page_title="Lyu-Science-Cloud", layout="wide")
st.markdown("""
    <style>
    /* 強制全白背景、全黑文字、翩翩體 (HanziPen SC) */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: white !important;
        color: black !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif;
    }
    /* 側邊欄視覺同步 */
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; }
    /* 照片與公式區禁止反黑 */
    .stImage, .stMarkdown, div[data-testid="stVerticalBlock"] {
        background-color: white !important;
        color: black !important;
    }
    /* 針對 Apple 設備 dark mode 的強制補丁 */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: white !important; color: black !important; }
    }
    </style>
    <meta name="color-scheme" content="light">
""", unsafe_allow_html=True)

# --- 2. 曉臻助教 6 項核心 API SOP ---
SYSTEM_PROMPT = """
你是曉臻助教，馬拉松選手 (PB 92分)。
1. 【開場】：隨機 10-20 秒運動健康內容，必含『熱身一下上完課就要去跑步了』。
2. 【導航】：腳本開頭必說：『各位同學，請翻到第 X 頁。』
3. 【珍珠邏輯】：解釋莫耳數相關公式時，必須使用珍珠奶茶邏輯。
4. 【口語轉譯】：所有 LaTeX 公式 (如 $n=m/M$) 必須轉為口語 (如「莫耳數等於質量除以分子量」)。
5. 【視覺】：背景全白、文字全黑、翩翩體。針對照片實驗現象同步解釋。
"""

# --- 3. 左側儀表板：API 與 頁碼選擇 ---
st.sidebar.title("🏃‍♀️ 產線設定")
user_api_key = st.sidebar.text_input("請輸入您的 Gemini API Key", type="password")
pdf_path = os.path.join("data", "二下第一章.pdf")

if user_api_key:
    genai.configure(api_key=user_api_key)
    MODEL = genai.GenerativeModel('gemini-2.5-flash') 
    
    if os.path.exists(pdf_path):
        doc = fitz.open(pdf_path)
        page_num = st.sidebar.number_input("請選擇講義頁碼", 1, doc.page_count, 1)
        
        # 渲染 PDF 頁面圖片
        page = doc.load_page(page_num - 1)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_data = Image.open(io.BytesIO(pix.tobytes()))
        
        # 雙模顯示佈局
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(f"📖 講義第 {page_num} 頁")
            st.image(img_data, use_column_width=True)
            
        with col2:
            st.subheader("🗣️ 曉臻助教導讀")
            if st.button("啟動 AI 導讀"):
                with st.spinner("曉臻熱身中..."):
                    try:
                        response = MODEL.generate_content([f"{SYSTEM_PROMPT}\n導讀第 {page_num} 頁。", img_data])
                        st.success(response.text)
                    except Exception as e:
                        st.error(f"API 連線失敗：{e}")
    else:
        st.error("❌ 找不到 data/二下第一章.pdf")
else:
    st.warning("⚠️ 請在左側輸入 API Key 讓曉臻助教上線！")