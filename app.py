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
    
    /* 2. 空間壓縮術：消除上方大片留白 */
    /* 這是控制主要內容區域的關鍵，原本預設是 6rem (約 100px)，我們改成 1rem (約 16px) */
    div.block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }

    /* 3. 側邊欄固定協議：鎖定寬度 320px */
    [data-testid="stSidebar"] { 
        min-width: 320px !important; 
        max-width: 320px !important; 
    }
    
    /* 4. 核災級隱藏修復：針對 keyboard_double_arrow_right 文字殘留 */
    button[data-testid="stSidebarCollapseButton"],
    button[data-testid="stSidebarCollapseButton"] > *,
    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;        /* 1. 結構上移除 */
        visibility: hidden !important;   /* 2. 視覺上隱藏 */
        height: 0px !important;          /* 3. 高度壓扁 */
        width: 0px !important;           /* 4. 寬度壓扁 */
        font-size: 0px !important;       /* 5. 字體歸零 (關鍵！讓文字變成 0 大小) */
        color: transparent !important;   /* 6. 顏色透明 */
        opacity: 0 !important;           /* 7. 透明度歸零 */
        z-index: -100 !important;        /* 8. 丟到最底層 */
        margin: 0 !important;            /* 9. 移除邊距 */
        padding: 0 !important;           /* 10. 移除填充 */
    }
    
    /* 隱藏原本的 Header 裝飾條，避免它擋到我們往上拉的標題 */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        height: 0px !important; /* 讓 Header 高度歸零 */
        z-index: -1 !important;
    }

    /* 5. 輸入元件美化：純白圖塊 + 淺灰邊框 */
    [data-baseweb="input"], [data-baseweb="select"], [data-testid="stNumberInput"] div, [data-testid="stTextInput"] div, [data-testid="stSelectbox"] > div > div {
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    
    [data-baseweb="select"] > div { background-color: #ffffff !important; color: #000000 !important; }
    [data-baseweb="input"] input, [data-baseweb="select"] div { color: #000000 !important; }

    /* 6. 字體規範：全黑翩翩體 */
    html, body, .stMarkdown, p, span, label, li, h1, h2, h3, .stButton button {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif !important;
    }

    .stButton button {
        border: 2px solid #000000 !important;
        background-color: #ffffff !important;
        font-weight: bold !important;
    }

    .stMarkdown p { font-size: calc(1rem + 0.3vw) !important; }

    /* 7. 檔案上傳區中文化 */
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
    clean_text = re.sub(r'[^\w\u4e00-\u9fff\d，。！？「」～ ]', '', text)
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 側邊欄：更新標題為「打開實驗室大門-金鑰」 ---
st.sidebar.title("🚪 打開實驗室大門-金鑰")
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

# --- 4. 曉臻教學 6 項核心指令 (5頁連擊強化版) ---
SYSTEM_PROMPT = """
你是資深自然科學助教曉臻，馬拉松選手 (PB 92分)。

1. 【熱血開場】：隨機 30 秒聊「運動對大腦的科學好處」或馬拉松訓練心得。嚴禁編造比分，必含『熱身一下下課老師就要去跑步了』。
2. 【練習題偵測】：偵測圖片中的「練習」字樣或空白填空。先公佈正確答案，再啟動「分段配速解說」，像拆解馬拉松戰術一樣詳細。
3. 【上下文串連】：通讀**多張圖片**，將教學概念與練習題連結，優先使用「珍珠奶茶」邏輯解釋（n=m/M）。
4. 【翻頁導航】：這是一次講解 5 頁的連續課程。
   - 在講解完一頁後，必須明確說出：『好，各位同學，我們翻到第 X 頁。』
   - 確保學生跟上進度，每頁之間的過場要流暢。
5. 【轉譯規範：極致清晰版】：
   - LaTeX 公式轉口語時，嚴禁讓 AI 直接輸出符號（如 H2O2）。
   - 必須將所有英文單字與數字「完全拆開」，且每個字後方都加上「～～」拉長音標記與空格。
   - 例如：O2 寫作「O～～ two～～」。
   - 例如：H2O2 寫作「H～～ two～～ O～～ two～～」。
   - 例如：n = m/M 寫作「n～～ 等於～～ m～～ 除以～～ M～～」。
6. 【真理激勵】：在 5 頁全部講完的最後，必喊『這就是自然科學的真理！』並鼓勵同學不要在馬拉松半路放棄。
"""

# --- 5. 導航系統 (冊別 | 章節 | 起始頁碼) ---
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    vol_select = st.selectbox("📚 冊別選擇", ["第一冊", "第二冊", "第三冊", "二下(第四冊)", "第五冊", "第六冊"], index=3)
with col2:
    chap_select = st.selectbox("🧪 章節選擇", ["第一章", "第二章", "第三章", "第四章", "第五章", "第六章"], index=0)
with col3:
    start_page = st.number_input("🏁 起始頁碼 (一次衝刺5頁)", 1, 100, 1, key="start_pg")

# 檔名組合
if vol_select == "二下(第四冊)" and chap_select == "第一章":
    filename = "二下第一章.pdf"
else:
    filename = f"{vol_select}_{chap_select}.pdf"

pdf_path = os.path.join("data", filename)

# 初始化 Session State
if "class_started" not in st.session_state:
    st.session_state.class_started = False
if "audio_html" not in st.session_state:
    st.session_state.audio_html = None
if "display_images" not in st.session_state:
    st.session_state.display_images = []

# --- 主畫面邏輯 ---

if not st.session_state.class_started:
    # 狀態 A: 備課中 (顯示封面圖)
    cover_image_path = None
    possible_extensions = [".jpg", ".jpeg", ".png", ".JPG", ".PNG"]
    
    for ext in possible_extensions:
        temp_path = os.path.join("data", f"cover{ext}")
        if os.path.exists(temp_path):
            cover_image_path = temp_path
            break
            
    if cover_image_path:
        st.image(cover_image_path, caption="曉臻老師正在操場熱身準備中...", use_container_width=True)
    else:
        st.info("🏃‍♀️ 曉臻老師正在起跑線上熱身... (請在 data 資料夾放入 cover.jpg 或 cover.png 以顯示封面)")
    
    st.divider()
    
    # 備課按