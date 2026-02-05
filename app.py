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

# --- 1. 核心視覺規範 (全白背景、全黑文字、翩翩體、側邊欄預設展開) [cite: 2026-02-03] ---
st.set_page_config(page_title="臻·極速自然能量域", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* 1. 全局視覺鎖定 (白底黑字翩翩體) [cite: 2026-02-03] */
    .stApp, [data-testid="stAppViewContainer"], .stMain, [data-testid="stHeader"] { 
        background-color: #ffffff !important; 
    }
    
    /* 2. 空間壓縮術 (主畫面 + 側邊欄) [cite: 2026-02-03] */
    div.block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem !important;
    }

    [data-testid="stSidebar"] { 
        min-width: 320px !important; 
        max-width: 320px !important; 
    }
    
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        z-index: 1 !important;
    }
    
    button[data-testid="stSidebarCollapseButton"] {
        color: #000000 !important;
        display: block !important;
    }

    [data-baseweb="input"], [data-baseweb="select"], [data-testid="stNumberInput"] div, [data-testid="stTextInput"] div, [data-testid="stSelectbox"] > div > div {
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    
    [data-baseweb="select"] > div { background-color: #ffffff !important; color: #000000 !important; }
    [data-baseweb="input"] input, [data-baseweb="select"] div { color: #000000 !important; }

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
    .info-box { border: 1px solid #ddd; padding: 1rem; border-radius: 8px; background-color: #f9f9f9; font-size: 0.9rem; }
    /* 逐字稿美化樣式 */
    .transcript-box {
        background-color: #fdfdfd;
        border-left: 5px solid #000000;
        padding: 15px;
        margin: 10px 0 30px 0;
        font-size: 1.1rem;
        line-height: 1.6;
    }
    </style>
    <meta name="color-scheme" content="light">
""", unsafe_allow_html=True)

# --- 🚀 標題重置 ---
st.title("🏃‍♀️ 臻 · 極速自然能量域")
st.markdown("### 🔬 資深理化老師 AI 助教：曉臻老師陪你衝刺科學馬拉松")
st.divider()

# --- 2. 曉臻語音引擎 (口語轉譯版) ---
async def generate_voice_base64(text):
    # 【暴力發音修正：名詞類】
    voice_text = text.replace("補給", "補己") 
    
    # 清理符號，保留長音符號 ～～
    clean_text = re.sub(r'[^\w\u4e00-\u9fff\d，。！？「」～ ]', '', voice_text)
    
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 側邊欄 ---
st.sidebar.title("🚪 打開實驗室大門-金鑰")
st.sidebar.markdown("""
<div class="info-box">
    <b>📢 曉臻老師的叮嚀：</b><br>
    曉臻是 AI，不一定完全對，但別小看她。一般的考試可是輕輕鬆鬆考滿分！曉臻怕大家會不專心，一次只會上5頁的講義。想要繼續上課，選好頁碼，再按一次就可以了。有發現什麼 Bug，請來信：<br>
    <a href="mailto:flyer19820218@gmail.com" style="color: #01579b; text-decoration: none; font-weight: bold;">flyer19820218@gmail.com</a>
</div>
<br>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div class="guide-box">
    <b>📖 值日生啟動指南：</b><br>
    1. 前往 <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#01579b; font-weight:bold;">Google AI Studio</a>。<br>
    2. 點擊 <b>Create API key</b> 並勾選同意。<br>
    3. 貼回下方金鑰區打開實驗室
</div>
""", unsafe_allow_html=True)
user_key = st.sidebar.text_input("🔑 實驗室啟動金鑰", type="password", key="tower_key")

st.sidebar.divider()
st.sidebar.subheader("💬 曉臻問題箱")
student_q = st.sidebar.text_input("打字問曉臻：", placeholder="例如：什麼是質量守恆？", key="science_q")
uploaded_file = st.sidebar.file_uploader("📸 照片區：", type=["jpg", "png", "jpeg"], key="science_f")

# --- 4. 曉臻教學 6 項核心指令 (優化切割版) ---
SYSTEM_PROMPT = """
你是資深自然科學助教曉臻，馬拉松選手 (PB 92分)。
你現在要進行一次導讀連續 5 頁講義的課程。請嚴格遵守以下對齊規範：

1. 【熱血開場】：
   - 隨機產出 30 秒關於「運動對大腦的科學好處」或馬拉松訓練心得。
   - 嚴禁編造比分。開場結尾必含：『熱身一下下課老師就要去跑步了』。

2. 【翻頁導航與過場】：
   - ⚠️ 除了一開始講解的那一頁之外，嚴禁在頁面解說開始前就唸出頁碼。
   - ⚠️ 重要：請在每一頁講評內容的最開始，單獨一行加上標籤：『---PAGE_SEP---』。
   - 正確節奏：a. 講評完 ➔ b. 說：『好，各位同學，我們翻到第 X 頁。』 ➔ c. 下一頁。

3. 【練習題偵測】：
   - 偵測圖片中若有「練習」、「範例」字樣。先請同學練習，後公佈正確答案，再啟動「分段配速解說」。

4. 【上下文串連】：將 5 頁圖片中的概念串接。

5. 【轉譯規範：極致清晰版】：
   - ⚠️ 語音暴力修正：所有的「補給站」一律在文字中輸出為『補給站』，確保語音唸成 jǐ。
   - LaTeX 公式請用：$$化學式$$ (語音導引 ～～ 也就是 中文名稱)。
   - 英文與數字必須完全拆開，每個字符後方加上「～～」標記與一個空格。
   - 範例：$$O_{2}$$ (O～～ two～～ 也就是氧氣)。

6. 【真理激勵】：結尾必喊：『這就是自然科學的真理！』並鼓勵同學。
"""

# --- 5. 導航系統 ---
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    vol_select = st.selectbox("📚 冊別選擇", ["第一冊", "第二冊", "第三冊", "第四冊", "第五冊", "第六冊"], index=3)
with col2:
    chap_select = st.selectbox("🧪 章節選擇", ["第一章", "第二章", "第三章", "第四章", "第五章", "第六章"], index=0)
with col3:
    start_page = st.number_input("🏁 起始頁碼 (一次衝刺5頁)", 1, 100, 1, key="start_pg")

if vol_select == "二下(第四冊)" and chap_select == "第一章":
    filename = "二下第一章.pdf"
else:
    filename = f"{vol_select}_{chap_select}.pdf"

pdf_path = os.path.join("data", filename)

if "class_started" not in st.session_state:
    st.session_state.class_started = False
if "audio_html" not in st.session_state:
    st.session_state.audio_html = None
if "display_images" not in st.session_state:
    st.session_state.display_images = []
if "res_text" not in st.session_state:
    st.session_state.res_text = ""

# --- 主畫面邏輯 ---

if not st.session_state.class_started:
    cover_image_path = None
    possible_extensions = [".jpg", ".jpeg", ".png", ".JPG", ".PNG"]
    for ext in possible_extensions:
        temp_path = os.path.join("data", f"cover{ext}")
        if os.path.exists(temp_path):
            cover_image_path = temp_path
            break
            
    if cover_image_path:
        try:
            image = Image.open(cover_image_path)
            st.image(image, caption="曉臻老師正在操場熱身準備中...", use_container_width=True)
        except:
            st.warning("⚠️ 封面圖片讀取失敗。")
    else:
        st.info("🏃‍♀️ 曉臻老師正在起跑線上熱身... (請在 data 放入 cover.jpg)")
    
    st.divider()
    
    if st.button(f"🏃‍♀️ 開始 25 分鐘馬拉松課程 (第 {start_page} ~ {start_page+4} 頁)", type="primary", use_container_width=True):
        if not user_key:
            st.warning("⚠️ 請輸入金鑰！")
        elif not os.path.exists(pdf_path):
            st.error(f"❌ 找不到課本：{filename}")
        else:
            with st.spinner("曉臻正在極速翻閱 5 頁講義..."):
                try:
                    doc = fitz.open(pdf_path)
                    images_to_process = []
                    display_images_list = []
                    pages_to_read = range(start_page - 1, min(start_page + 4, len(doc)))
                    
                    if len(pages_to_read) == 0:
                        st.error("⚠️ 已翻到最後一頁！")
                        st.stop()

                    for page_num in pages_to_read:
                        page = doc.load_page(page_num)
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        img = Image.open(io.BytesIO(pix.tobytes()))
                        images_to_process.append(img)
                        display_images_list.append((page_num + 1, img))
                    
                    genai.configure(api_key=user_key)
                    MODEL = genai.GenerativeModel('models/gemini-2.5-flash') 
                    
                    prompt = f"{SYSTEM_PROMPT}\n現在請一次導讀第 {start_page} 頁到第 {pages_to_read[-1]+1} 頁。換頁請加標籤並提醒學生。"
                    res = MODEL.generate_content([prompt] + images_to_process)
                    
                    audio_html = asyncio.run(generate_voice_base64(res.text))
                    
                    st.session_state.res_text = res.text # 🔑 儲存文字稿
                    st.session_state.audio_html = audio_html
                    st.session_state.display_images = display_images_list
                    st.session_state.class_started = True
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 錯誤：{e}")

else:
    # 狀態 B: 上課中
    st.success("🔔 曉臻老師正在導讀中，請專注聆聽！")
    
    if st.session_state.audio_html:
        st.markdown(st.session_state.audio_html, unsafe_allow_html=True)
    
    st.divider()

    # --- 💡 逐字稿與圖片對齊邏輯 ---
    full_text = st.session_state.get("res_text", "")
    parts = full_text.split("---PAGE_SEP---") # 根據標籤切開

    # 顯示開場白
    if len(parts) > 0:
        with st.chat_message("曉臻"):
            st.markdown(parts[0].strip())

    st.divider()

    # 顯示每頁圖片與對應文字
    for i, (p_num, img) in enumerate(st.session_state.display_images):
        st.image(img, caption=f"🏁 第 {p_num} 頁講義跑道", use_container_width=True)
        
        # 顯示對應這張圖片的文字稿
        if (i + 1) < len(parts):
            st.markdown(f'<div class="transcript-box"><b>📜 曉臻老師的逐字稿 (第 {p_num} 頁)：</b><br>{parts[i+1].strip()}</div>', unsafe_allow_html=True)
        
        st.divider()
            
    if st.button("🏁 下課休息 (回到首頁)"):
        st.session_state.class_started = False
        st.session_state.audio_html = None
        st.session_state.display_images = []
        st.rerun()
