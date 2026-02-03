import streamlit as st
import google.generativeai as genai
import os, asyncio, edge_tts, re, base64, io, random
from PIL import Image

# --- 零件檢查 ---
try:
    import fitz
except ImportError:
    st.error("❌ 零件缺失！請確保 requirements.txt 已加入 pymupdf。")
    st.stop()

# --- 1. 核心規範：視覺鎖定與 Apple 適配 [cite: 2026-02-03] ---
st.set_page_config(page_title="Lyu-Science-Cloud", layout="wide")

st.markdown("""
    <style>
    /* 規範 3: 全黑文字、白色背景、翩翩體鎖定 [cite: 2026-02-03] */
    .stApp, [data-testid="stAppViewContainer"], .stMain {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif !important;
    }
    
    /* 規範 6: 適配平板與手機雙模顯示 [cite: 2026-02-03] */
    .stMarkdown, p, span, label, li {
        color: #000000 !important;
        font-size: calc(1rem + 0.3vw) !important;
    }

    /* 規範 3 & 6: 解決照片與公式區黑底與 Apple 反黑問題 [cite: 2026-02-03] */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
    }
    div[data-testid="stVerticalBlock"], .stImage, .stMarkdown {
        background-color: #ffffff !important;
    }
    </style>
    <meta name="color-scheme" content="light">
""", unsafe_allow_html=True)

# --- 2. 曉臻語音引擎 (口譯版) [cite: 2026-02-01] ---
async def generate_voice_base64(text):
    # 清除殘留符號，讓曉臻只唸口語化中文 [cite: 2026-02-03]
    clean_text = re.sub(r'[\$#_]', '', text)
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 側邊欄：API 與 頁碼選擇 (規範 5 頁碼導航) [cite: 2026-02-03] ---
import streamlit as st
import google.generativeai as genai
import os, asyncio, edge_tts, re, base64, io, random
from PIL import Image

# --- 零件檢查 ---
try:
    import fitz
except ImportError:
    st.error("❌ 零件缺失！請確保 requirements.txt 已加入 pymupdf。")
    st.stop()

# --- 1. 核心規範：視覺鎖定與 Apple 適配 [cite: 2026-02-03] ---
st.set_page_config(page_title="Lyu-Science-Cloud", layout="wide")

st.markdown("""
    <style>
    /* 規範 3: 全黑文字、白色背景、翩翩體鎖定 [cite: 2026-02-03] */
    .stApp, [data-testid="stAppViewContainer"], .stMain {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif !important;
    }
    
    /* 規範 6: 適配平板與手機雙模顯示 [cite: 2026-02-03] */
    .stMarkdown, p, span, label, li {
        color: #000000 !important;
        font-size: calc(1rem + 0.3vw) !important;
    }

    /* 規範 3 & 6: 解決照片與公式區黑底與 Apple 反黑問題 [cite: 2026-02-03] */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
    }
    div[data-testid="stVerticalBlock"], .stImage, .stMarkdown {
        background-color: #ffffff !important;
    }
    </style>
    <meta name="color-scheme" content="light">
""", unsafe_allow_html=True)

# --- 2. 曉臻語音引擎 (口譯版) [cite: 2026-02-01] ---
async def generate_voice_base64(text):
    # 清除殘留符號，讓曉臻只唸口語化中文 [cite: 2026-02-03]
    clean_text = re.sub(r'[\$#_]', '', text)
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 側邊欄：API 與 頁碼選擇 (規範 5 頁碼導航) [cite: 2026-02-03] ---
st.sidebar.title("🏃‍♀️ 曉臻產線儀表板")
user_key = st.sidebar.text_input("🔑 通行證 (API Key)：", type="password")
pdf_path = os.path.join("data", "二下第一章.pdf") # 預設講義路徑 [cite: 2026-02-03]

# --- 4. 核心 6 項提示詞實裝 [cite: 2026-02-03] ---
SYSTEM_PROMPT = """
你是資深理化助教曉臻。人設：熱愛馬拉松 (PB 92分)，語調溫和穩定。 [cite: 2026-02-01]

【API 6 項核心指令】：
1. 人設：鎖定曉臻老師導讀，展現馬拉松精神。
2. 開場：隨機產出 10-20 秒運動健康內容 (如拉筋、剛跑完馬拉松)。 [cite: 2026-02-03]
3. 視覺：背景全白、文字全黑、翩翩體。照片區禁止背景反黑。 [cite: 2026-02-03]
4. 公式：嚴格使用 LaTeX。但聽覺劇本必須轉成口語中文 (如 n=m/M 唸作「莫耳數等於質量除以分子量」)。 [cite: 2026-02-03]
5. 導航：劇本開頭必須說：『各位同學，請翻到第 X 頁。』支援頁碼切換。 [cite: 2026-02-03]
6. 適配：內容簡潔，支援手機與平板雙模顯示。
"""

if user_key and os.path.exists(pdf_path):
    genai.configure(api_key=user_key)
    MODEL = genai.GenerativeModel('models/gemini-2.5-flash')
    doc = fitz.open(pdf_path)
    
    # 只要有頁碼選擇就可以了 [cite: 2026-02-03]
    page_num = st.sidebar.number_input("請選擇頁碼", 1, doc.page_count, 1)
    
    if st.button(f"🚀 啟動【第 {page_num} 頁】真理導讀"):
        # 渲染 PDF 高畫質圖片 [cite: 2026-02-03]
        page = doc.load_page(page_num - 1)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_data = Image.open(io.BytesIO(pix.tobytes()))
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.image(img_data, use_column_width=True) # 顯示教材 [cite: 2026-02-03]
            
        with col2:
            with st.spinner("曉臻熱身中..."):
                # 執行 6 項指令生成雙軌內容 [cite: 2026-02-03]
                prompt = f"{SYSTEM_PROMPT}\n【指令】：請導讀第 {page_num} 頁。請分『視覺內容』與『聽覺劇本』。"
                res = MODEL.generate_content([prompt, img_data])
                
                # 內容分離 [cite: 2026-02-03]
                display_txt = res.text.split("【聽覺劇本】")[0].replace("【視覺內容】", "").strip()
                voice_txt = res.text.split("【聽覺劇本】")[-1].strip() if "【聽覺劇本】" in res.text else display_txt
                
                st.markdown(f"### 🗣️ 曉臻老師說：\n{display_txt}")
                st.markdown(asyncio.run(generate_voice_base64(voice_txt)), unsafe_allow_html=True)
                st.balloons()

# --- 4. 核心 6 項提示詞實裝 [cite: 2026-02-03] ---
SYSTEM_PROMPT = """
你是資深理化助教曉臻。人設：熱愛馬拉松 (PB 92分)，語調溫和穩定。 [cite: 2026-02-01]

【API 6 項核心指令】：
1. 人設：鎖定曉臻老師導讀，展現馬拉松精神。
2. 開場：隨機產出 10-20 秒運動健康內容 (如拉筋、剛跑完馬拉松)。 [cite: 2026-02-03]
3. 視覺：背景全白、文字全黑、翩翩體。照片區禁止背景反黑。 [cite: 2026-02-03]
4. 公式：嚴格使用 LaTeX。但聽覺劇本必須轉成口語中文 (如 n=m/M 唸作「莫耳數等於質量除以分子量」)。 [cite: 2026-02-03]
5. 導航：劇本開頭必須說：『各位同學，請翻到第 X 頁。』支援頁碼切換。 [cite: 2026-02-03]
6. 適配：內容簡潔，支援手機與平板雙模顯示。
"""

if user_key and os.path.exists(pdf_path):
    genai.configure(api_key=user_key)
    MODEL = genai.GenerativeModel('models/gemini-2.5-flash')
    doc = fitz.open(pdf_path)
    
    # 只要有頁碼選擇就可以了 [cite: 2026-02-03]
    page_num = st.sidebar.number_input("請選擇頁碼", 1, doc.page_count, 1)
    
    if st.button(f"🚀 啟動【第 {page_num} 頁】真理導讀"):
        # 渲染 PDF 高畫質圖片 [cite: 2026-02-03]
        page = doc.load_page(page_num - 1)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_data = Image.open(io.BytesIO(pix.tobytes()))
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.image(img_data, use_column_width=True) # 顯示教材 [cite: 2026-02-03]
            
        with col2:
            with st.spinner("曉臻熱身中..."):
                # 執行 6 項指令生成雙軌內容 [cite: 2026-02-03]
                prompt = f"{SYSTEM_PROMPT}\n【指令】：請導讀第 {page_num} 頁。請分『視覺內容』與『聽覺劇本』。"
                res = MODEL.generate_content([prompt, img_data])
                
                # 內容分離 [cite: 2026-02-03]
                display_txt = res.text.split("【聽覺劇本】")[0].replace("【視覺內容】", "").strip()
                voice_txt = res.text.split("【聽覺劇本】")[-1].strip() if "【聽覺劇本】" in res.text else display_txt
                
                st.markdown(f"### 🗣️ 曉臻老師說：\n{display_txt}")
                st.markdown(asyncio.run(generate_voice_base64(voice_txt)), unsafe_allow_html=True)
                st.balloons()