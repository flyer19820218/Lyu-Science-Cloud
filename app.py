import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF [cite: 2026-02-03]
from PIL import Image
import os, random, io

# --- 1. 核心規範：視覺鎖定與 Apple 防反黑補丁 [cite: 2026-02-03] ---
st.set_page_config(page_title="Lyu-Science-Cloud", layout="wide")
st.markdown("""
    <style>
    /* 強制全白背景、全黑文字、翩翩體 (HanziPen SC) [cite: 2026-02-03] */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: white !important;
        color: black !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif;
    }
    /* 平板/手機雙模文字顯示邏輯 [cite: 2026-02-03] */
    [data-testid="column"] {
        background-color: white !important;
    }
    /* 照片與公式區禁止反黑 [cite: 2026-02-03] */
    .stImage, .stMarkdown, div[data-testid="stVerticalBlock"] {
        background-color: white !important;
        color: black !important;
    }
    /* 針對 Apple 設備 dark mode 的強制補丁 [cite: 2026-02-03] */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: white !important; color: black !important; }
    }
    </style>
    <meta name="color-scheme" content="light">
""", unsafe_allow_html=True)

# --- 2. 曉臻助教 6 項核心 API SOP [cite: 2026-02-03] ---
SYSTEM_PROMPT = """
你是曉臻助教，馬拉松選手 (PB 92分)，語音溫和穩定。 [cite: 2026-02-01]
1. 【開場】：隨機產出 10-20 秒運動健康內容，包含『熱身一下上完課就要去跑步了』。 [cite: 2026-02-03]
2. 【導航】：必說：『各位同學，請翻到第 X 頁。』 [cite: 2026-02-03]
3. 【視覺】：背景全白、文字全黑、翩翩體。照片區禁止背景反黑。 [cite: 2026-02-03]
4. 【數學】：公式如 $n=m/M$ 必須用 LaTeX 並在導讀中轉成口語中文。 [cite: 2026-02-03]
5. 【手機適配】：生成內容需簡潔，支援平板與手機切換顯示。
6. 【同步解釋】：針對照片中的實驗現象進行說明，解決黑底黑字顯示問題。
"""

# --- 3. 模型設定 (使用穩定型號) ---
API_KEY = "AIzaSyBEO5jqly5qFnjCGgzcs68O0iavJMrXl7k"
genai.configure(api_key=API_KEY)
MODEL = genai.GenerativeModel('gemini-2.5-flash') 

st.title("🏃‍♀️ 曉臻助教：理化雲端教室")

# --- 4. 讀取 PDF 與 頁碼選擇 ---
pdf_path = os.path.join("data", "二下第一章.pdf")

if os.path.exists(pdf_path):
    doc = fitz.open(pdf_path)
    # 只要有頁碼選擇就可以了 [cite: 2026-02-03]
    page_num = st.sidebar.number_input("請選擇頁碼", 1, doc.page_count, 1)
    
    # 渲染 PDF 頁面圖片 [cite: 2026-02-03]
    page = doc.load_page(page_num - 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_data = Image.open(io.BytesIO(pix.tobytes()))
    
    # 雙模佈局：左側圖片，右側曉臻 [cite: 2026-02-03]
    col1, col2 = st.columns([2, 1])
    with col1:
        st.image(img_data, use_column_width=True)
        
    with col2:
        if st.button("啟動曉臻導讀"):
            with st.spinner("曉臻熱身中..."):
                response = MODEL.generate_content([
                    f"{SYSTEM_PROMPT}\n請導讀第 {page_num} 頁內容。", 
                    img_data
                ])
                st.success(response.text)
else:
    st.error("❌ 找不到 data/二下第一章.pdf")