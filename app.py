import streamlit as st
import google.generativeai as genai
import os, asyncio, edge_tts, re, base64, io, random
from PIL import Image

# --- 零件檢查 [cite: 2026-02-03] ---
try:
    import fitz # pymupdf
except ImportError:
    st.error("❌ 零件缺失！請確保已安裝 pymupdf 與 edge-tts。")
    st.stop()

# --- 1. 核心規範：視覺鎖定與 Apple 適配 (深度白晝協議) [cite: 2026-02-03] ---
st.set_page_config(page_title="理化 AI 雞排珍奶實驗室", layout="wide")

st.markdown("""
    <style>
    /* 全黑文字、白色背景、翩翩體鎖定 [cite: 2026-02-03] */
    .stApp, [data-testid="stAppViewContainer"], .stMain, [data-testid="stHeader"] {
        background-color: #ffffff !important;
    }
    html, body, .stMarkdown, p, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif !important;
    }
    
    /* 左側空間加大 (450px) 放置 API 與問題區 [cite: 2026-02-03] */
    [data-testid="stSidebar"] {
        min-width: 450px !important;
        max-width: 450px !important;
    }

    /* 強制 Apple 設備暗色模式失效 [cite: 2026-02-03] */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
    }
    </style>
    <meta name="color-scheme" content="light">
""", unsafe_allow_html=True)

# --- 2. 曉臻語音引擎 (口語轉譯版) [cite: 2026-02-01] ---
async def generate_voice_base64(text):
    # 確保曉臻只唸翻譯好的口語中文 [cite: 2026-02-03]
    clean_text = re.sub(r'[^\w\u4e00-\u9fff\d，。！？「」]', '', text)
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 左側側邊欄：API 指南與問題區 [cite: 2026-02-03] ---
st.sidebar.title("🏃‍♀️ 曉臻產線儀表板")

st.sidebar.markdown("""
<div style="border: 2px dashed #01579b; padding: 15px; border-radius: 10px; background-color: #f0f8ff; color: black;">
    <b>📖 學生快速通行指南：</b><br>
    1. 前往 Google AI Studio 產出通行證。<br>
    2. <b>務必勾選兩次同意條款</b>。<br>
    3. 貼回下方邀請曉臻助教上線！
</div>
""", unsafe_allow_html=True)
user_key = st.sidebar.text_input("🔑 通行證輸入區：", type="password")

st.sidebar.divider()
st.sidebar.subheader("💬 曉臻問題箱")
student_q = st.sidebar.text_input("打字問曉臻：", placeholder="例如：什麼是比熱？")
uploaded_file = st.sidebar.file_uploader("📸 照片區：", type=["jpg", "png", "jpeg"])

# --- 4. 曉臻助教 6 項核心 API SOP (提示詞鎖定) [cite: 2026-02-03] ---
SYSTEM_PROMPT = """
你是資深理化助教曉臻。人設：馬拉松選手 (PB 92分)，語音溫和穩定。 [cite: 2026-02-01]
1. 【熱身開場】：隨機 15 秒跑步或健康開場，包含『熱身一下上完課就要去跑步了』。 [cite: 2026-02-03]
2. 【導航指令】：腳本開頭必須說：『各位同學，請翻到第 X 頁。』 [cite: 2026-02-03]
3. 【視覺規範】：背景全白、文字全黑、翩翩體。公式用 LaTeX。 [cite: 2026-02-03]
4. 【聽覺轉譯】：LaTeX 公式必須翻譯成中文口語 (如 n=m/M 唸作「莫耳數等於質量除以分子量」)。 [cite: 2026-02-03]
5. 【內容解釋】：同步針對講義照片中的實驗現象進行說明，解決黑底黑字顯示問題。 [cite: 2026-02-03]
6. 【跨機適配】：支援手機與平板雙模顯示。 [cite: 2026-02-03]
"""

# --- 5. 右側主畫面：頁碼直選(置頂) + PDF 呈現 [cite: 2026-02-03] ---
st.title("🚀 理化 AI 雞排珍奶實驗室 (實體課對應版)")

# 修正：頁碼移至右側最上面 [cite: 2026-02-03]
target_page = st.number_input("📍 請直接輸入/選擇講義頁碼 (1-64)", 1, 64, 1)

pdf_path = os.path.join("data", "二下第一章.pdf") [cite: 2026-02-03]

if os.path.exists(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(target_page - 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_data = Image.open(io.BytesIO(pix.tobytes()))
    
    # PDF 原圖呈現 [cite: 2026-02-03]
    st.image(img_data, use_column_width=True)
    
    st.divider()
    
    # 曉臻老師備課啟動按鈕 [cite: 2026-02-03]
    if st.button("🏃‍♀️ 曉臻老師：熱身準備上課！"):
        if not user_key:
            st.warning("⚠️ 請先在左側輸入通行證讓曉臻助教上線！")
        else:
            with st.spinner("曉臻助教正在穿跑鞋備課中..."):
                try:
                    genai.configure(api_key=user_key)
                    MODEL = genai.GenerativeModel('models/gemini-2.5-flash')
                    prompt = f"{SYSTEM_PROMPT}\n請導讀第 {target_page} 頁內容。分開『視覺內容』與『聽覺劇本』。"
                    parts = [prompt, img_data]
                    if uploaded_file: parts.append(Image.open(uploaded_file))
                    
                    res = MODEL.generate_content(parts)
                    voice_txt = res.text.split("【聽覺劇本】")[-1].strip() if "【聽覺劇本】" in res.text else res.text
                    
                    st.info(f"🔊 曉臻老師正在口播第 {target_page} 頁真理...")
                    st.markdown(asyncio.run(generate_voice_base64(voice_txt)), unsafe_allow_html=True)
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ 曉臻遇到了權限問題：{e}")
else:
    st.error(f"❌ 找不到檔案：{pdf_path}")