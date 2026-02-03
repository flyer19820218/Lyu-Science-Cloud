import streamlit as st
import google.generativeai as genai
import os, asyncio, edge_tts, re, base64, io, random
from PIL import Image

# --- 零件檢查 [cite: 2026-02-03] ---
try:
    import fitz # pymupdf
except ImportError:
    st.error("❌ 零件缺失！請確保 requirements.txt 已加入 pymupdf。")
    st.stop()

# --- 1. 頁面配置 (深度白晝協議 + 側邊欄加大一倍) [cite: 2026-02-03] ---
st.set_page_config(page_title="理化 AI 雞排珍奶實驗室", layout="wide")

st.markdown("""
    <style>
    /* 核心規範：全白背景、全黑文字、翩翩體鎖定 [cite: 2026-02-03] */
    .stApp, [data-testid="stAppViewContainer"], .stMain, [data-testid="stHeader"] {
        background-color: #ffffff !important;
    }
    html, body, .stMarkdown, p, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif !important;
    }
    
    /* 左邊空間加大一倍 (450px) [cite: 2026-02-03] */
    [data-testid="stSidebar"] {
        min-width: 450px !important;
        max-width: 450px !important;
    }

    /* 按鈕適配：淺藍配色 [cite: 2026-02-03] */
    div.stButton > button {
        background-color: #e3f2fd !important; color: #000000 !important;
        border: 2px solid #01579b !important; border-radius: 12px !important;
        font-family: 'HanziPen SC', '翩翩體' !important;
    }

    /* 強制 Apple 設備暗色模式失效 [cite: 2026-02-03] */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
    }
    </style>
    <meta name="color-scheme" content="light">
""", unsafe_allow_html=True)

# --- 2. 曉臻語音引擎 (口語轉譯) [cite: 2026-02-01] ---
async def generate_voice_base64(text):
    # 確保曉臻只唸翻譯好的中文口語，排除所有 LaTeX 符號 [cite: 2026-02-03]
    clean_text = re.sub(r'[^\w\u4e00-\u9fff\d，。！？「」]', '', text)
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 側邊欄儀表板：頁碼置頂 + API + 問問題 [cite: 2026-02-03] ---
st.sidebar.title("🏃‍♀️ 曉臻產線儀表板")

# 規範：頁碼放在最上面 [cite: 2026-02-03]
target_page = st.sidebar.number_input("📍 請直接輸入講義頁碼 (1-72)", 1, 72, 1)

st.sidebar.divider()

# API 通行證指南 [cite: 2026-02-03]
st.sidebar.markdown("""
<div style="border: 2px dashed #01579b; padding: 15px; border-radius: 10px; background-color: #f0f8ff;">
    <b>📖 學生快速通行指南：</b><br>
    1. 前往 Google AI Studio 產出專屬通行證。<br>
    2. <b>務必勾選兩次同意條款</b>。<br>
    3. 貼回下方邀請曉臻助教上線！
</div>
""", unsafe_allow_html=True)
user_key = st.sidebar.text_input("🔑 通行證輸入區：", type="password")

st.sidebar.divider()

# 學生問問題區 [cite: 2026-02-03]
st.sidebar.subheader("💬 曉臻問題箱")
student_q = st.sidebar.text_input("打字問曉臻：", placeholder="例如：為什麼 $n = m/M$？")
uploaded_file = st.sidebar.file_uploader("📸 照片區 (解析實驗現象)：", type=["jpg", "png", "jpeg"])

# --- 4. 核心 API 提示詞 (曉臻馬拉松 SOP) [cite: 2026-02-03] ---
SYSTEM_PROMPT = """
你是資深理化助教曉臻，馬拉松選手 (PB 92分)。語氣熱血且專業。 [cite: 2026-02-01]
1. 【開場】：聊聊「現炸大雞排」配「波霸珍奶」或「跑步熱身」的心得。 [cite: 2026-02-03]
2. 【導航】：開頭必說：『各位同學，請翻到第 X 頁。』 [cite: 2026-02-03]
3. 【視覺】：不產生課文，僅針對聽覺劇本進行口播。 [cite: 2026-02-03]
4. 【聽覺】：LaTeX 公式必須翻譯成中文口語 (如 n=m/M 唸作「莫耳數等於質量除以分子量」)。 [cite: 2026-02-03]
5. 【結尾】：必喊「這就是理化的真理！」。 [cite: 2026-02-03]
"""

# --- 5. 右側主畫面：PDF 呈現與備課按鈕 [cite: 2026-02-03] ---
st.title("🚀 理化 AI 雞排珍奶實驗室 (實體課對應版)")
pdf_path = os.path.join("data", "Ph_Ch_finals.pdf") # 鎖定檔案路徑

if user_key and os.path.exists(pdf_path):
    genai.configure(api_key=user_key)
    MODEL = genai.GenerativeModel('models/gemini-2.5-flash')
    
    doc = fitz.open(pdf_path)
    # 渲染 PDF 頁面圖片並顯示 [cite: 2026-02-03]
    page = doc.load_page(target_page - 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_data = Image.open(io.BytesIO(pix.tobytes()))
    
    # PDF 原圖呈現 [cite: 2026-02-03]
    st.image(img_data, use_column_width=True)
    
    st.divider()
    
    # 曉臻老師：熱身準備上課的備課按鈕 [cite: 2026-02-03]
    if st.button("🏃‍♀️ 曉臻老師：熱身準備上課！(啟動 AI 導讀)"):
        with st.spinner("曉臻正在備課調製珍奶..."):
            prompt = f"{SYSTEM_PROMPT}\n請導讀第 {target_page} 頁內容。"
            parts = [prompt, img_data]
            if uploaded_file: parts.append(Image.open(uploaded_file))
            
            res = MODEL.generate_content(parts)
            # 僅產出語音，不產生重複課文 [cite: 2026-02-03]
            st.info(f"🔊 曉臻老師正在口播第 {target_page} 頁真理...")
            st.markdown(asyncio.run(generate_voice_base64(res.text)), unsafe_allow_html=True)
            st.balloons()
else:
    if not user_key: st.warning("⚠️ 請先在左側輸入通行證讓曉臻上線！")
    elif not os.path.exists(pdf_path): st.error(f"❌ 找不到講義檔案：{pdf_path}")