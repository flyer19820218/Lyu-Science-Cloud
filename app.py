import streamlit as st
import google.generativeai as genai
import os, asyncio, edge_tts, re, base64, io, random
from PIL import Image

# --- 零件檢查 ---
try:
    import fitz # pymupdf
except ImportError:
    st.error("❌ 零件缺失！請確保已安裝 pymupdf 與 edge-tts。")
    st.stop()

# --- 1. 核心視覺規範 (全白背景、全黑文字、翩翩體、側邊欄恆定展開) ---
st.set_page_config(page_title="臻·極速自然能量域", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* 1. 全局視覺鎖定 (白底黑字翩翩體) */
    .stApp, [data-testid="stAppViewContainer"], .stMain, [data-testid="stHeader"] { 
        background-color: #ffffff !important; 
    }
    
    /* 2. 側邊欄固定協議：鎖定寬度 320px */
    [data-testid="stSidebar"] { 
        min-width: 320px !important; 
        max-width: 320px !important; 
    }
    
    /* 3. 側邊欄按鈕絕對隱藏 (防止文字殘留) */
    button[data-testid="stSidebarCollapseButton"],
    button[data-testid="stSidebarCollapseButton"] > * {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        width: 0px !important;
        font-size: 0px !important;
        color: transparent !important;
        opacity: 0 !important;
    }

    /* 4. 輸入框美化修復：純白圖塊 + 溫柔邊框 */
    /* 修正點：背景改回白色，加入 1px 淺灰邊框，自然形成方框 */
    [data-baseweb="input"], [data-testid="stNumberInput"] div, [data-testid="stTextInput"] div {
        background-color: #ffffff !important;  /* 白色圖塊 */
        border: 1px solid #d1d5db !important;  /* 淺灰色邊框 (取代醜黑線) */
        border-radius: 6px !important;         /* 微微圓角 */
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important; /* 增加一點點立體感 */
    }
    
    /* 確保輸入文字是深黑色的 */
    [data-baseweb="input"] input {
        color: #000000 !important;
    }

    /* 5. 字體規範：全黑翩翩體 */
    html, body, .stMarkdown, p, span, label, li, h1, h2, h3 {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif !important;
    }

    .stMarkdown p { font-size: calc(1rem + 0.3vw) !important; }

    /* 6. 📸 檔案上傳區中文化 */
    section[data-testid="stFileUploadDropzone"] span { visibility: hidden; }
    section[data-testid="stFileUploadDropzone"]::before {
        content: "📸 拖曳圖片至此或點擊下方按鈕 ➔";
        visibility: visible;
        display: block;
        color: #000000;
        font-weight: bold;
        text-align: center;
    }
    section[data-testid="stFileUploadDropzone"] button::after {
        content: "🔍 瀏覽檔案";
        visibility: visible;
        display: block;
        background-color: #f0f2f6;
        padding: 5px 10px;
        border-radius: 5px;
        color: #000000;
    }

    @media (prefers-color-scheme: dark) { .stApp { background-color: #ffffff !important; color: #000000 !important; } }
    .guide-box { border: 2px dashed #01579b; padding: 1rem; border-radius: 12px; background-color: #f0f8ff; color: #000000; }
    </style>
    <meta name="color-scheme" content="light">
""", unsafe_allow_html=True)

# --- 🚀 標題重置 ---
st.title("🏃‍♀️ 臻 · 極速自然能量域")
st.markdown("### 🔬 資深理化老師 AI 助教：曉臻老師陪你衝刺科學馬拉松")
st.divider()

# --- 2. 曉臻語音引擎 (口語轉譯版) ---
async def generate_voice_base64(text):
    # 確保曉臻只唸翻譯好的口語中文
    clean_text = re.sub(r'[^\w\u4e00-\u9fff\d，。！？「」～ ]', '', text)
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 側邊欄：曉臻的科學動能控制塔 ---
st.sidebar.title("🚪打開實驗室大門-申請金鑰")
st.sidebar.markdown("""
<div class="guide-box">
    <b>📖 值日生啟動指南：</b><br>
    1. 前往 <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#01579b; font-weight:bold;">Google AI Studio</a>。<br>
    2. 點擊 <b>Create API key</b> 並勾選同意。<br>
    3. 貼回下方金鑰區開啟能量域！
</div>
""", unsafe_allow_html=True)
user_key = st.sidebar.text_input("🔑 實驗室啟動金鑰", type="password", key="tower_key")

st.sidebar.divider()
st.sidebar.subheader("💬 曉臻問題箱")
student_q = st.sidebar.text_input("打字問曉臻：", placeholder="例如：什麼是質量守恆？", key="science_q")
uploaded_file = st.sidebar.file_uploader("📸 照片區：", type=["jpg", "png", "jpeg"], key="science_f")

# --- 4. 曉臻教學 6 項核心指令 (真理對答案完整回歸版) ---
SYSTEM_PROMPT = """
你是資深自然科學助教曉臻，馬拉松選手 (PB 92分)。

1. 【熱血開場】：隨機 30 秒聊「運動對大腦的科學好處」或馬拉松訓練心得。嚴禁編造比分，必含『熱身一下下課老師就要去跑步了』。
2. 【練習題偵測】：偵測「練習」字樣或空白填空。先公佈正確答案，再啟動「分段配速解說」，像拆解馬拉松戰術一樣詳細。
3. 【上下文串連】：通讀全圖，將教學概念與練習題連結，優先使用「珍珠奶茶」邏輯解釋（n=m/M）。嚴禁描述顏色字體。
4. 【導航】：腳本開頭必說：『各位同學，請翻到第 X 頁。』
5. 【轉譯規範：極致清晰版】：
   - LaTeX 公式轉口語時，嚴禁讓 AI 直接輸出符號（如 H2O2）。
   - 必須將所有英文單字與數字「完全拆開」，且每個字後方都加上「～～」拉長音標記與空格。
   - 例如：O2 寫作「O～～ two～～」。
   - 例如：H2O2 寫作「H～～ two～～ O～～ two～～」。
   - 例如：n = m/M 寫作「n～～ 等於～～ m～～ 除以～～ M～～」。
   - 這樣做能確保聲紋穩定，且讓曉臻唸得清楚有韻律感。
6. 【真理激勵】：結尾必喊『這就是自然科學的真理！』並鼓勵同學不要在馬拉松半路放棄。
"""

target_page = st.number_input("📍 請輸入/選擇講義頁碼 (1-64)", 1, 64, 1, key="main_pg")

pdf_path = os.path.join("data", "二下第一章.pdf")

if os.path.exists(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(target_page - 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_data = Image.open(io.BytesIO(pix.tobytes()))
    
    st.image(img_data, use_container_width=True) 
    st.divider()
    
    if st.button("🏃‍♀️ 曉臻：心率同步，進入備課衝刺！"):
        if not user_key:
            st.warning("⚠️ 值日生請注意：尚未轉動啟動金鑰！")
        else:
            with st.spinner("曉臻正在努力備課中，請稍等!你可以先喝杯珍奶..."):
                try:
                    genai.configure(api_key=user_key)
                    MODEL = genai.GenerativeModel('models/gemini-2.5-flash') 
                    prompt = f"{SYSTEM_PROMPT}\n請導讀第 {target_page} 頁。若有練習題請先讓學生練習，然後對答案並解說。"
                    res = MODEL.generate_content([prompt, img_data])
                    
                    st.info(f"🔊 曉臻正在進行音速破風導讀！")
                    st.markdown(asyncio.run(generate_voice_base64(res.text)), unsafe_allow_html=True)
                    st.balloons()
                except Exception as e: st.error(f"❌ 控制塔連線失敗：{e}")
else:
    st.error(f"❌ 找不到講義：{pdf_path}")