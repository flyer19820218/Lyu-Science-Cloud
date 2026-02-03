import streamlit as st
import google.generativeai as genai
import os, asyncio, edge_tts, re, base64, io, random
from PIL import Image

# --- 零件檢查 ---
try:
    import fitz  # pymupdf
except ImportError:
    st.error("❌ 零件缺失！請確保已安裝 pymupdf。")
    st.stop()

# --- 1. 頁面配置 (蘋果/平板雙模適配：深度白晝協議) ---
st.set_page_config(page_title="理化 AI 雞排珍奶實驗室", layout="wide")

st.markdown("""
    <style>
    /* 全局白底黑字鎖定 [cite: 2026-02-03] */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stMain {
        background-color: #ffffff !important;
    }
    html, body, .stMarkdown, p, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif !important;
    }
    /* 側邊欄縮小三分之一 (從 450px 變為 300px) [cite: 2026-02-03] */
    [data-testid="stSidebar"] {
        min-width: 300px !important;
        max-width: 300px !important;
    }
    /* 平板手機雙模字體縮放 [cite: 2026-02-03] */
    .stMarkdown p { font-size: calc(1rem + 0.3vw) !important; }
    
    /* 蘋果設備防反黑修正 [cite: 2026-02-03] */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
    }
    .guide-box { border: 2px dashed #01579b; padding: 1rem; border-radius: 12px; background-color: #f0f8ff; color: #000000; font-size: 0.95rem !important; }
    </style>
    <meta name="color-scheme" content="light">
""", unsafe_allow_html=True)

# --- 2. 曉臻語音引擎 (口語轉譯) ---
async def generate_voice_base64(text):
    # 清除 LaTeX 與符號，讓曉臻只唸翻譯好的口語 [cite: 2026-02-03]
    clean_text = re.sub(r'[^\w\u4e00-\u9fff\d，。！？「」]', '', text)
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 側邊欄：API 指南、通行證輸入、問問題、照片區 ---
st.sidebar.title("🏃‍♀️ 曉臻產線儀表板")
# 修復超連結 [cite: 2026-02-03]
st.sidebar.markdown("""
<div class="guide-box">
    <b>📖 曉臻助教版通行指南：</b><br>
    1. 前往 <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#01579b; font-weight:bold;">Google AI Studio</a>。<br>
    2. 點擊 <b>Create API key</b> 並勾選同意。<br>
    3. 貼回下方邀請曉臻助教！
</div>
""", unsafe_allow_html=True)
user_key = st.sidebar.text_input("🔑 通行證輸入區：", type="password", key="api_field")

st.sidebar.divider()
st.sidebar.subheader("💬 曉臻問題箱")
student_q = st.sidebar.text_input("打字問曉臻：", placeholder="例如：原子量是什麼？", key="side_q")
uploaded_file = st.sidebar.file_uploader("📸 照片區：", type=["jpg", "png", "jpeg"], key="side_file")

# --- 4. 核心 API 提示詞 (6項 SOP 實裝) [cite: 2026-02-03] ---
SYSTEM_PROMPT = """
你是資深理化助教曉臻，馬拉松選手 (PB 92分)。
1. 【開場】：隨機 15 秒跑步熱身或運動健康內容，必含『熱身一下上完課就要去跑步了』。 [cite: 2026-02-03]
2. 【導航】：腳本開頭必說：『各位同學，請翻到第 X 頁。』 [cite: 2026-02-03]
3. 【視覺】：背景全白、文字全黑、翩翩體。公式用 LaTeX。 [cite: 2026-02-03]
4. 【聽覺】：LaTeX 公式如 $n=m/M$ 必須轉成中文口語 (如「莫耳數等於質量除以分子量」)。 [cite: 2026-02-03]
5. 【結尾】：結尾喊「這就是理化的真理！」。 [cite: 2026-02-03]
"""

# --- 5. 右側主畫面：頁碼直選(置頂) + PDF 呈現 ---
st.title("🚀 理化 AI 雞排珍奶實驗室 (實體課對應版)")

# 頁碼直選移到講義上面 [cite: 2026-02-03]
target_page = st.number_input("📍 請直接輸入/選擇講義頁碼 (1-64)", min_value=1, max_value=64, value=1, key="pg_idx")

# 鎖定檔案路徑 [cite: 2026-02-03]
pdf_path = os.path.join("data", "二下第一章.pdf")

if os.path.exists(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(target_page - 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_data = Image.open(io.BytesIO(pix.tobytes()))
    
    st.image(img_data, use_column_width=True)
    st.divider()
    
    if st.button("🏃‍♀️ 曉臻老師：熱身準備上課！", key="run_lecture"):
        if not user_key:
            st.warning("⚠️ 請先在左側輸入全新的通行證！")
        else:
            with st.spinner("曉臻正在備課調製珍奶..."):
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
    st.error(f"❌ 找不到講義：{pdf_path}")