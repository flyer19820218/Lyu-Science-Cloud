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

# --- 1. 核心視覺規範 (全白、全黑、翩翩體) [cite: 2026-02-03] ---
st.set_page_config(page_title="理化 AI 雞排珍奶實驗室", layout="wide")
st.markdown("""
    <style>
    .stApp, [data-testid="stAppViewContainer"], .stMain, [data-testid="stHeader"] { background-color: #ffffff !important; }
    html, body, .stMarkdown, p, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif !important;
    }
    /* 側邊欄縮小三分之一 (300px) [cite: 2026-02-03] */
    [data-testid="stSidebar"] { min-width: 300px !important; max-width: 300px !important; }
    
    @media (prefers-color-scheme: dark) { .stApp { background-color: #ffffff !important; color: #000000 !important; } }
    .guide-box { border: 2px dashed #01579b; padding: 1rem; border-radius: 12px; background-color: #f0f8ff; color: #000000; }
    </style>
    <meta name="color-scheme" content="light">
""", unsafe_allow_html=True)

# --- 2. 曉臻語音引擎 (口語轉譯) ---
async def generate_voice_base64(text):
    clean_text = re.sub(r'[^\w\u4e00-\u9fff\d，。！？「」]', '', text)
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 側邊欄：API 與 問題區 [cite: 2026-02-03] ---
st.sidebar.title("🏃‍♀️ 曉臻產線儀表板")
st.sidebar.markdown("""
<div class="guide-box">
    <b>📖 學生快速通行指南：</b><br>
    1. 前往 <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#01579b; font-weight:bold;">Google AI Studio</a>。<br>
    2. 點擊 <b>Create API key</b> 並勾選同意。<br>
    3. 貼回下方邀請曉臻助教上線！
</div>
""", unsafe_allow_html=True)
user_key = st.sidebar.text_input("🔑 通行證輸入區：", type="password", key="api_key_v2")

st.sidebar.divider()
st.sidebar.subheader("💬 曉臻問題箱")
student_q = st.sidebar.text_input("打字問曉臻：", placeholder="例如：原子量是什麼？", key="sidebar_q")
uploaded_file = st.sidebar.file_uploader("📸 照片區：", type=["jpg", "png", "jpeg"], key="sidebar_f")

# --- 4. 曉臻教學 6 項核心指令 (強化邏輯版) [cite: 2026-02-03] ---
SYSTEM_PROMPT = """
你是資深理化助教曉臻，馬拉松選手 (PB 92分)。語速穩定、專業熱血。 [cite: 2026-02-01]

【開場指令】：
- 隨機生成 30 秒開場白，聊聊昨天的體育新聞 (NBA 戰況、經典賽棒球、或馬拉松訓練心得)。
- 嚴禁提到投影片的顏色、字體或圖片元數據。
- 結尾必含『熱身一下上完課就要去跑步了』。

【教學邏輯】：
- AI 必須「通讀」整張圖片。如果有化學平衡的教學，後面跟著空白題，必須引導學生將概念與練習串連。
- 必說：『各位同學，請翻到第 X 頁。』
- LaTeX 公式 (如 $n=m/M$) 必須口語化 (如「莫耳數等於質量除以分子量」)。珍珠奶茶邏輯優先 [cite: 2026-02-01]。
"""

# --- 5. 右側主畫面：頁碼置頂與 PDF 呈現 [cite: 2026-02-03] ---
st.title("🚀 理化 AI 雞排珍奶實驗室 (教學優化版)")
target_page = st.number_input("📍 請輸入/選擇講義頁碼 (1-64)", 1, 64, 1, key="main_pg")

pdf_path = os.path.join("data", "二下第一章.pdf")

if os.path.exists(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(target_page - 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_data = Image.open(io.BytesIO(pix.tobytes()))
    st.image(img_data, use_column_width=True)
    st.divider()
    
    if st.button("🏃‍♀️ 曉臻老師：熱身準備上課！"):
        if not user_key:
            st.warning("⚠️ 請先在左側輸入全新的通行證！")
        else:
            with st.spinner("曉臻正在分析運動新聞與備課邏輯..."):
                try:
                    genai.configure(api_key=user_key)
                    MODEL = genai.GenerativeModel('models/gemini-2.5-flash')
                    prompt = f"{SYSTEM_PROMPT}\n請導讀第 {target_page} 頁內容。將教學概念與練習題串連說明。"
                    res = MODEL.generate_content([prompt, img_data])
                    
                    st.info(f"🔊 曉臻老師正在口播第 {target_page} 頁教學...")
                    st.markdown(asyncio.run(generate_voice_base64(res.text)), unsafe_allow_html=True)
                    st.balloons()
                except Exception as e: st.error(f"❌ 曉臻遇到連線問題：{e}")
else:
    st.error(f"❌ 找不到講義：{pdf_path}")