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

# --- 1. 核心視覺規範 (深度白晝協議：全白、全黑、翩翩體) [cite: 2026-02-03] ---
st.set_page_config(page_title="臻·極速自然能量域", layout="wide")
st.markdown("""
    <style>
    .stApp, [data-testid="stAppViewContainer"], .stMain, [data-testid="stHeader"] { background-color: #ffffff !important; }
    html, body, .stMarkdown, p, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif !important;
    }
    /* 側邊欄縮小至 300px [cite: 2026-02-03] */
    [data-testid="stSidebar"] { min-width: 300px !important; max-width: 300px !important; }
    .stMarkdown p { font-size: calc(1rem + 0.3vw) !important; }
    
    @media (prefers-color-scheme: dark) { .stApp { background-color: #ffffff !important; color: #000000 !important; } }
    .guide-box { border: 2px dashed #01579b; padding: 1rem; border-radius: 12px; background-color: #f0f8ff; color: #000000; }
    </style>
    <meta name="color-scheme" content="light">
""", unsafe_allow_html=True)

# --- 2. 曉臻語音引擎 (口語轉譯版) [cite: 2026-02-01, 2026-02-03] ---
async def generate_voice_base64(text):
    # 確保曉臻只唸翻譯好的口語中文 [cite: 2026-02-03]
    clean_text = re.sub(r'[^\w\u4e00-\u9fff\d，。！？「」]', '', text)
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 側邊欄：曉臻的科學實驗室任意門 [cite: 2026-02-03] ---
st.sidebar.title("🏃‍♀️ 曉臻的科學實驗室任意門")
st.sidebar.markdown("""
<div class="guide-box">
    <b>📖 值日生啟動指南：</b><br>
    1. 前往 <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#01579b; font-weight:bold;">Google AI Studio</a>。<br>
    2. 點擊 <b>Create API key</b> 並勾選同意。<br>
    3. 貼回下方金鑰區開啟能量域！
</div>
""", unsafe_allow_html=True)
user_key = st.sidebar.text_input("🔑 值日生專屬：實驗室啟動金鑰", type="password", key="tower_key")

st.sidebar.divider()
st.sidebar.subheader("💬 曉臻問題箱")
student_q = st.sidebar.text_input("打字問曉臻：", placeholder="例如：什麼是質量守恆？", key="science_q")
uploaded_file = st.sidebar.file_uploader("📸 照片區：", type=["jpg", "png", "jpeg"], key="science_f")

# --- 4. 曉臻教學 6 項核心指令 (真理對答案強化版) [cite: 2026-02-03] ---
SYSTEM_PROMPT = """
你是資深自然科學助教曉臻，馬拉松選手 (PB 92分)。語氣專業熱血。 [cite: 2026-02-01]

【教學指令 SOP】：
1. 【熱血開場】：隨機產出 30 秒開場，聊聊「運動對大腦的好處」 (如：多巴胺、血液含氧量、耐力) 或馬拉松心得。嚴禁編造不實比分，必含『熱身一下下課老師就要去跑步了』。 [cite: 2026-02-03]
2. 【練習題偵測】：
   - 若頁面標題含「練習」、「習題」、「挑戰」或出現空白填空，即啟動「真理對答案協議」。
   - 必須先公佈正確答案，再假設全體同學都不會，啟動「分段配速解說」。 [cite: 2026-02-03]
3. 【上下文串連】：通讀全圖，將前面概念教學與後方習題連結，用珍珠奶茶邏輯解釋。 [cite: 2026-02-01]
4. 【導航】：必說：『各位同學，請翻到第 X 頁。』 [cite: 2026-02-03]
5. 【轉譯規範】：LaTeX 公式轉口語時，英文符號與數字必須拆解。
   - 例如：O2 寫作「O two」、CO2 寫作「C O two」、H2O 寫作「H two O」。
   - 絕對不要直接輸出符號，確保聲紋統一。 [cite: 2026-02-03]
6. 【激勵】：結尾必喊『這就是自然科學的真理！』並鼓勵同學不要在馬拉松半路放棄。 [cite: 2026-02-03]
"""

# 頁碼直選置頂 [cite: 2026-02-03]
target_page = st.number_input("📍 請輸入/選擇講義頁碼 (1-64)", 1, 64, 1, key="main_pg")

pdf_path = os.path.join("data", "二下第一章.pdf")

if os.path.exists(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(target_page - 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_data = Image.open(io.BytesIO(pix.tobytes()))
    
    st.image(img_data, use_column_width=True) # 講義原圖 [cite: 2026-02-03]
    st.divider()
    
    # 備課按鈕升級 [cite: 2026-02-03]
    if st.button("🏃‍♀️ 曉臻：心率同步，進入備課衝刺！"):
        if not user_key:
            st.warning("⚠️ 值日生請注意：尚未轉動啟動金鑰！")
        else:
            with st.spinner("曉臻正在分析賽事戰報與對答案邏輯..."):
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