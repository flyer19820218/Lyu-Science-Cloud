import streamlit as st
import google.generativeai as genai
import os, asyncio, edge_tts, re, base64, io
from PIL import Image

# --- 零件檢查：確保 PyMuPDF 有裝好 [cite: 2026-02-03] ---
try:
    import fitz
except ImportError:
    st.error("❌ 零件缺失！請確保 requirements.txt 已加入 pymupdf。")
    st.stop()

# --- 1. 核心規範：視覺鎖定與 Apple 適配 (手機/平板雙模) [cite: 2026-02-03] ---
st.set_page_config(page_title="Lyu-Science-Cloud", layout="wide")

st.markdown("""
    <style>
    /* 1. 全局白底黑字鎖定：防止 Apple 設備自動反黑 [cite: 2026-02-03] */
    html, body, .stApp, [data-testid="stAppViewContainer"], .stMain {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif !important;
    }
    
    /* 2. 平板手機雙模字體縮放 [cite: 2026-02-03] */
    .stMarkdown, p, span, label, li {
        color: #000000 !important;
        font-size: calc(1rem + 0.3vw) !important;
    }

    /* 3. 照片與公式區禁止反黑 [cite: 2026-02-03] */
    .stImage, .stMarkdown, div[data-testid="stVerticalBlock"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    /* 4. 強制暗色模式失效 (Apple 補丁) [cite: 2026-02-03] */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
    }
    </style>
    <meta name="color-scheme" content="light">
""", unsafe_allow_html=True)

# --- 2. 曉臻語音引擎 (口語轉譯) [cite: 2026-02-01, 2026-02-03] ---
async def generate_voice_base64(text):
    # 這裡會根據 6 項規範，將 LaTeX 符號由 Gemini 預先轉為中文口語
    communicate = edge_tts.Communicate(text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 側邊欄：API 與 頁碼選擇 [cite: 2026-02-03] ---
st.sidebar.title("🏃‍♀️ 產線儀表板")
user_key = st.sidebar.text_input("🔑 通行證 (API Key)：", type="password")
pdf_path = os.path.join("data", "二下第一章.pdf") # 預設讀取 data 資料夾 [cite: 2026-02-03]

if user_key:
    genai.configure(api_key=user_key)
    # 使用呂老師指定的正版模型
    MODEL = genai.GenerativeModel('models/gemini-2.5-flash')
    
    if os.path.exists(pdf_path):
        doc = fitz.open(pdf_path)
        # 只要有頁碼選擇就可以了 [cite: 2026-02-03]
        page_num = st.sidebar.number_input("請選擇頁碼 (1-64)", 1, doc.page_count, 1)
        
        # 4. 雙模佈局：左側教材，右側曉臻 [cite: 2026-02-03]
        col1, col2 = st.columns([2, 1])
        
        with col1:
            page = doc.load_page(page_num - 1)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = Image.open(io.BytesIO(pix.tobytes()))
            st.image(img_data, use_column_width=True)
            
        with col2:
            st.subheader("🗣️ 曉臻老師導讀")
            if st.button("啟動馬拉松導讀"):
                # --- 6 項提示詞實裝 [cite: 2026-02-03] ---
                prompt = f"""你是助教曉臻，馬拉松選手 (PB 92分)。
                1. 【開場】：隨機 15 秒關於跑步熱身與健康內容。
                2. 【導航】：必說『各位同學，請翻到第 {page_num} 頁』。
                3. 【語音】：分開『視覺內容』(Markdown) 與『聽覺劇本』(純中文口語)。
                4. 【轉譯】：所有 LaTeX 公式 (如 n=m/M) 在聽覺劇本中必須翻譯成中文。
                """
                with st.spinner("曉臻熱身中..."):
                    res = MODEL.generate_content([prompt, img_data])
                    full_text = res.text
                    # 簡單切割視覺與聽覺內容
                    st.success(full_text.split("【聽覺劇本】")[0])
                    # 生成曉臻語音
                    voice_script = full_text.split("【聽覺劇本】")[-1] if "【聽覺劇本】" in full_text else full_text
                    st.markdown(asyncio.run(generate_voice_base64(voice_script)), unsafe_allow_html=True)
    else:
        st.error("❌ 找不到 data/二下第一章.pdf")
else:
    st.warning("⚠️ 請在左側輸入 API Key 讓曉臻老師上線！")