import streamlit as st
import google.generativeai as genai
import os, asyncio, edge_tts, re, base64, io, random
from PIL import Image

# --- 零件檢查 [cite: 2026-02-03] ---
try:
    import fitz # pymupdf
except ImportError:
    st.error("❌ 零件缺失！請確保已安裝 pymupdf。")
    st.stop()

# --- 1. 頁面配置 (側邊欄加大 + 蘋果/平板適配) [cite: 2026-02-03] ---
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
    
    /* 加大左側空間：側邊欄寬度翻倍 [cite: 2026-02-03] */
    [data-testid="stSidebar"] {
        min-width: 450px !important;
        max-width: 450px !important;
        background-color: #f8f9fa !important;
    }

    /* 解決照片與公式區黑底問題 (Apple 設備補丁) [cite: 2026-02-03] */
    @media (prefers-color-scheme: dark) {
        .stApp, [data-testid="stSidebar"] { background-color: #ffffff !important; color: #000000 !important; }
    }
    </style>
    <meta name="color-scheme" content="light">
""", unsafe_allow_html=True)

# --- 2. 曉臻語音引擎 (口語轉譯版) [cite: 2026-02-01] ---
async def generate_voice_base64(text):
    # 移除劇本符號，讓曉臻只唸翻譯好的中文口語 [cite: 2026-02-03]
    clean_text = re.sub(r'[^\w\u4e00-\u9fff\d，。！？「」]', '', text)
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 側邊欄儀表板 (寬度加大版) [cite: 2026-02-03] ---
st.sidebar.title("🏃‍♀️ 曉臻產線儀表板")

# 修正：頁碼放在最上面 [cite: 2026-02-03]
target_page = st.sidebar.number_input("📍 請輸入講義頁碼 (1-72)", 1, 72, 1)

st.sidebar.divider()

# API 通行證指南 [cite: 2026-02-03]
st.sidebar.markdown("""
<div style="border: 2px dashed #01579b; padding: 15px; border-radius: 10px; background-color: #f0f8ff;">
    <b>📖 學生快速通行指南：</b><br>
    1. 前往 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a>。<br>
    2. 點擊 <b>Create API key</b> 並勾選同意。<br>
    3. 貼回下方邀請曉臻助教。
</div>
""", unsafe_allow_html=True)
user_key = st.sidebar.text_input("🔑 通行證輸入區：", type="password")

st.sidebar.divider()

# 學生問問題與照片區 [cite: 2026-02-03]
st.sidebar.subheader("💬 曉臻問題箱")
student_q = st.sidebar.text_input("打字問曉臻：", placeholder="例如：原子量是什麼？")
uploaded_file = st.sidebar.file_uploader("📸 照片區：", type=["jpg", "png", "jpeg"])

# --- 4. 核心 API 提示詞 (6項 SOP 實裝) [cite: 2026-02-03] ---
SYSTEM_PROMPT = """
你是資深理化助教曉臻，馬拉松選手 (PB 92分)。 [cite: 2026-02-01]
1. 【開場】：隨機 15 秒跑步健康與大雞排珍奶解壓內容。
2. 【導航】：必說：『各位同學，請翻到第 X 頁。』 [cite: 2026-02-03]
3. 【視覺】：背景全白、文字全黑、翩翩體。公式用 LaTeX。 [cite: 2026-02-03]
4. 【聽覺】：提供『聽覺劇本』。LaTeX 公式必須翻譯成中文口語 (如 n=m/M 唸作「莫耳數等於質量除以分子量」)。 [cite: 2026-02-03]
5. 【內容】：針對講義照片實驗現象解釋，結尾喊「這就是理化的真理！」。
"""

# --- 5. 右側主畫面：PDF 呈現與導讀 [cite: 2026-02-03] ---
st.title("🚀 理化 AI 雞排珍奶實驗室 (實體課對應版)")
pdf_path = os.path.join("data", "Ph_Ch_finals.pdf") # 鎖定實體課程版本檔案

if user_key and os.path.exists(pdf_path):
    genai.configure(api_key=user_key)
    MODEL = genai.GenerativeModel('models/gemini-2.5-flash')
    
    doc = fitz.open(pdf_path)
    # 渲染 PDF 頁面圖片 [cite: 2026-02-03]
    page = doc.load_page(target_page - 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_data = Image.open(io.BytesIO(pix.tobytes()))
    
    st.image(img_data, use_column_width=True) # 原圖呈現
    
    if st.button(f"🚀 啟動【第 {target_page} 頁】導讀產線"):
        with st.spinner("曉臻正在備課調製珍奶..."):
            prompt = f"{SYSTEM_PROMPT}\n請導讀第 {target_page} 頁。分開『視覺內容』與『聽覺劇本』。"
            parts = [prompt, img_data]
            if uploaded_file: parts.append(Image.open(uploaded_file))
            
            res = MODEL.generate_content(parts)
            voice_txt = res.text.split("【聽覺劇本】")[-1].strip() if "【聽覺劇本】" in res.text else res.text
            
            st.info(f"🔊 曉臻老師正在口播第 {target_page} 頁真理...")
            st.markdown(asyncio.run(generate_voice_base64(voice_txt)), unsafe_allow_html=True)
            st.balloons()