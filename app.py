import streamlit as st
import google.generativeai as genai
import os, asyncio, edge_tts, re, base64, io, random
from PIL import Image

# --- 零件檢查 ---
try:
    import fitz # pymupdf
except ImportError:
    st.error("❌ 零件缺失！請安裝 pymupdf。")
    st.stop()

# --- 1. 核心視覺規範 (移除標籤框框、全白背景、翩翩體) ---
st.set_page_config(page_title="臻·極速自然能量域", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* 1. 全局視覺鎖定 (白底黑字翩翩體) */
    .stApp, [data-testid="stAppViewContainer"], .stMain, [data-testid="stHeader"] { 
        background-color: #ffffff !important; 
    }
    
    /* 2. 空間與邊距調整 */
    div.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
    section[data-testid="stSidebar"] > div { padding-top: 1rem !important; }
    [data-testid="stSidebar"] { min-width: 320px !important; max-width: 320px !important; }
    header[data-testid="stHeader"] { background-color: transparent !important; z-index: 1 !important; }
    button[data-testid="stSidebarCollapseButton"] { color: #000000 !important; display: block !important; }

    /* 3. 修正：移除標籤周圍的方框 (針對起始頁碼等) */
    [data-testid="stWidgetLabel"] p {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
    }

    /* 4. 輸入元件美化：僅針對輸入框本身 */
    [data-baseweb="input"], [data-baseweb="select"], [data-testid="stNumberInput"] div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
    }

    /* 5. 字體規範 */
    html, body, .stMarkdown, p, label, li, h1, h2, h3, .stButton button, a {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif !important;
    }

    .stButton button {
        border: 2px solid #000000 !important;
        background-color: #ffffff !important;
        font-weight: bold !important;
    }
    .stMarkdown p { font-size: calc(1rem + 0.3vw) !important; }

    /* 6. 曉臻逐字稿顯示盒 */
    .transcript-box {
        background-color: #fdfdfd;
        border-left: 5px solid #000;
        padding: 15px;
        margin-bottom: 25px;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# --- 🚀 主標題 ---
st.title("🏃‍♀️ 臻 · 極速自然能量域")
st.markdown("### 🔬 資深理化老師 AI 助教：曉臻老師陪你衝刺科學馬拉松")
st.divider()

# --- 2. 曉臻語音引擎 (暴力發音修正：聽起來要專業) ---
async def generate_voice_base64(text):
    # 彻底抹除換頁標籤，防止唸出「Page Sep」雜音
    voice_text = text.replace("---PAGE_SEP---", " ")
    
    corrections = {
        "補給": "補己",
        "Ethanol": "乙醇",
        "75%": "百分之七十五",
        "Acetic acid": "醋酸",
        "%": "趴",
    }
    for word, correct in corrections.items():
        voice_text = voice_text.replace(word, correct)
    
    # 章節全自動修正 (例如 3-1 -> 三之一)
    voice_text = re.sub(r'(\d+)-(\d+)', r'\1之\2', voice_text)
    
    clean_text = voice_text.replace("$", "")
    clean_text = re.sub(r'[^\w\u4e00-\u9fff\d，。！？「」～ ]', '', clean_text)
    
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 💡 視覺洗淨 (讓學生看到的文字美觀) ---
def clean_for_eye(text):
    t = text.replace("---PAGE_SEP---", "")
    t = re.sub(r'([a-zA-Z0-9])～～\s*', r'\1', t) 
    t = t.replace("～～", "")
    return t

# --- 3. 側邊欄 (老師最愛的原始叮嚀，一字不漏) ---
st.sidebar.title("🚪 打開實驗室大門-金鑰")

st.sidebar.markdown("""
<div class="info-box">
    <b>📢 曉臻老師的叮嚀：</b><br>
    曉臻是 AI，不一定完全對，但別小看她。一般的考試可是輕輕鬆鬆考滿分！曉臻怕大家會不專心，一次只會上5頁的講義。想要繼續上課，選好頁碼，再按一次就可以了。有發現什麼 Bug，請來信：<br>
    <a href="mailto:flyer19820218@gmail.com" style="color: #01579b; text-decoration: none; font-weight: bold;">flyer19820218@gmail.com</a>
</div>
<br>
""", unsafe_allow_html=True)

user_key = st.sidebar.text_input("🔑 實驗室啟動金鑰", type="password", key="tower_key")
st.sidebar.divider()
st.sidebar.subheader("💬 曉臻問題箱")
student_q = st.sidebar.text_input("打字問曉臻：", key="science_q")
uploaded_file = st.sidebar.file_uploader("📸 照片區：", type=["jpg", "png", "jpeg"], key="science_f")

# --- 4. 曉臻教學核心指令 ---
SYSTEM_PROMPT = """
你是資深自然科學助教曉臻，馬拉松選手 (PB 92分)。
你現在要導讀 5 頁講義。請遵守規範：

1. 【開場】：聊運動大腦科學。必含：『熱身一下下課老師就要去跑步了』。
2. 【翻頁】：解說完當頁才唸『翻到第 X 頁』。每頁最開頭加上標籤『---PAGE_SEP---』。
3. 【偵測】：僅當圖片出現「練習」二字才啟動題目模式。底線文字視為教學重點提醒，嚴禁誤判為題目。
4. 【規範】：
   - 慢速標記：英文、數字、字母後方加「～～」。
   - 結晶水：點號（·）翻譯為『帶 X 個結晶水』。
   - 範例：$$O_{2}$$ (O～～ two～～)、$$CuSO_{4} \cdot 5H_{2}O$$ (C～～ u～～ S～～ O～～ four～～ 帶五個結晶水)。
5. 【結尾】：必喊『這就是自然科學的真理！』。
"""

# --- 5. 導航系統 (移除方框後依然清晰) ---
col1, col2, col3 = st.columns([1, 1, 1])
with col1: vol_select = st.selectbox("📚 冊別選擇", ["第一冊", "第二冊", "第三冊", "第四冊", "第五冊", "第六冊"], index=3)
with col2: chap_select = st.selectbox("🧪 章節選擇", ["第一章", "第二章", "第三章", "第四章", "第五章", "第六章"], index=2)
with col3: start_page = st.number_input("🏁 起始頁碼", 1, 100, 1, key="start_pg")

filename = f"{vol_select}_{chap_select}.pdf"
pdf_path = os.path.join("data", filename)

if "class_started" not in st.session_state: st.session_state.class_started = False
if "res_text" not in st.session_state: st.session_state.res_text = ""

# --- 主畫面邏輯 ---
if not st.session_state.class_started:
    # 📸 曉臻封面圖片邏輯 (回歸！)
    cover_image_path = None
    for ext in [".jpg", ".png", ".jpeg", ".JPG", ".PNG"]:
        temp_path = os.path.join("data", f"cover{ext}")
        if os.path.exists(temp_path):
            cover_image_path = temp_path
            break
            
    if cover_image_path:
        st.image(Image.open(cover_image_path), use_container_width=True) # 顯示我們的主角曉臻！
    else:
        st.info("🏃‍♀️ 曉臻老師正在起跑線上熱身準備中...")
    
    st.divider()
    if st.button(f"🏃‍♀️ 開始馬拉松課程", type="primary", use_container_width=True):
        if user_key and os.path.exists(pdf_path):
            with st.spinner("曉臻正在極速翻閱講義..."):
                doc = fitz.open(pdf_path)
                images_to_process, display_images_list = [], []
                pages_to_read = range(start_page - 1, min(start_page + 4, len(doc)))
                for p_num in pages_to_read:
                    pix = doc.load_page(p_num).get_pixmap(matrix=fitz.Matrix(2, 2))
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    images_to_process.append(img)
                    display_images_list.append((p_num + 1, img))
                
                genai.configure(api_key=user_key)
                MODEL = genai.GenerativeModel('models/gemini-2.5-flash') 
                res = MODEL.generate_content([f"{SYSTEM_PROMPT}\n導讀P.{start_page}起內容。"] + images_to_process)
                
                st.session_state.res_text = res.text
                st.session_state.audio_html = asyncio.run(generate_voice_base64(res.text))
                st.session_state.display_images = display_images_list
                st.session_state.class_started = True
                st.rerun()
else:
    # 狀態 B: 上課中
    st.success("🔔 曉臻老師正在上課中！")
    if "audio_html" in st.session_state: st.markdown(st.session_state.audio_html, unsafe_allow_html=True)
    st.divider()

    parts = st.session_state.get("res_text", "").split("---PAGE_SEP---")
    if len(parts) > 0:
        with st.chat_message("曉臻"): st.markdown(clean_for_eye(parts[0]))

    for i, (p_num, img) in enumerate(st.session_state.display_images):
        st.image(img, caption=f"🏁 第 {p_num} 頁講義", use_container_width=True)
        if (i + 1) < len(parts):
            st.markdown(f'<div class="transcript-box"><b>📜 曉臻老師的逐字稿 (P.{p_num})：</b><br>{clean_for_eye(parts[i+1])}</div>', unsafe_allow_html=True)
        st.divider()

    if st.button("🏁 下
