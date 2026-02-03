import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
from PIL import Image
import os, random, io

# --- 1. 核心規範：視覺鎖定與 Apple 適配 [cite: 2026-02-03] ---
st.set_page_config(page_title="Lyu-Science-Cloud", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: white !important; color: black !important; font-family: 'HanziPen SC', '翩翩體', sans-serif; }
    @media (prefers-color-scheme: dark) { .stApp { background-color: white !important; color: black !important; } }
    </style>
""", unsafe_allow_html=True)

# --- 2. 模型設定與 API 連結 ---
API_KEY = "AIzaSyBEO5jqly5qFnjCGgzcs68O0iavJMrXl7k"
genai.configure(api_key=API_KEY)
MODEL = genai.GenerativeModel('gemini-2.5-flash') 

# --- 3. 雲端介面與頁碼選擇 ---
st.title("🏃‍♀️ 曉臻助教：理化雲端教室 (Lyu-Science-Cloud)")
pdf_path = os.path.join("data", "二下第一章.pdf")

if os.path.exists(pdf_path):
    doc = fitz.open(pdf_path)
    page_num = st.sidebar.number_input("請選擇講義頁碼", 1, doc.page_count, 1)
    
    # 渲染 PDF 頁面 [cite: 2026-02-03]
    page = doc.load_page(page_num - 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_data = Image.open(io.BytesIO(pix.tobytes()))
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(f"📖 講義第 {page_num} 頁")
        st.image(img_data, use_column_width=True)
        
    with col2:
        st.subheader("🗣️ 曉臻老師導讀")
        if st.button("啟動 AI 導讀解說"):
            with st.spinner("曉臻正在熱身並閱讀講義..."):
                # 執行 6 項核心 SOP 提示詞 [cite: 2026-02-03]
                prompt = f"你現在是馬拉松助教曉臻。請閱讀這頁 PDF 內容，並產出第 {page_num} 頁的導讀稿。記得包含 15 秒運動熱身內容，並將 LaTeX 公式口語化。"
                response = MODEL.generate_content([prompt, img_data])
                st.success(response.text)
else:
    st.error("❌ 找不到 data/二下第一章.pdf，請確認檔案位置。")