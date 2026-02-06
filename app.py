import streamlit as st
import google.generativeai as genai
import os, asyncio, edge_tts, re, base64, io, random
from PIL import Image

# --- 零件檢查 ---
try:
    import fitz # pymupdf
except ImportError:
    st.error("❌ 零件缺失！請確保安裝了 pymupdf。")
    st.stop()

# --- 1. 核心視覺規範 (全白背景、移除標籤方框、翩翩體) ---
st.set_page_config(page_title="臻·極速自然能量域", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* 1. 全局視覺鎖定 (白底黑字) */
    :root { color-scheme: light !important; }
    .stApp, [data-testid="stAppViewContainer"], .stMain, [data-testid="stHeader"] { 
        background-color: #ffffff !important; 
    }
    
    /* 2. 空間與邊距調整 */
    div.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
    section[data-testid="stSidebar"] > div { padding-top: 1rem !important; }
    [data-testid="stSidebar"] { min-width: 320px !important; max-width: 320px !important; }
    header[data-testid="stHeader"] { background-color: transparent !important; z-index: 1 !important; }
    button[data-testid="stSidebarCollapseButton"] { color: #000000 !important; display: block !important; }

    /* 3. 🚨 暴力拔除標籤方框 (起始頁碼、冊別等標籤) */
    [data-testid="stWidgetLabel"] div, [data-testid="stWidgetLabel"] p {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    /* 4. 字體規範：全黑翩翩體 */
    html, body, .stMarkdown, p, label, li, h1, h2, h3, .stButton button, a {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif !important;
    }

    .stButton button {
        border: 2px solid #000000 !important;
        background-color: #ffffff !important;
        font-weight: bold !important;
    }

    /* 5. 區塊樣式 */
    .info-box { border: 1px solid #ddd; padding: 1rem; border-radius: 8px; background-color: #f9f9f9; font-size: 0.9rem; color: #000; }
    .guide-box { border: 2px dashed #01579b; padding: 1rem; border-radius: 12px; background-color: #f0f8ff; color: #000; }
    .transcript-box { background-color: #fdfdfd; border-left: 5px solid #000; padding: 15px; margin-bottom: 25px; line-height: 1.6; }
    </style>
""", unsafe_allow_html=True)

st.title("🏃‍♀️ 臻 · 極速自然能量域")
st.markdown("### 🔬 資深理化老師 AI 助教：曉臻老師陪你衝刺科學馬拉松")
st.divider()

# --- 2. 曉臻語音引擎 (暴力音正 + 雜音過濾) ---
async def generate_voice_base64(text):
    # 【關鍵】徹底抹除分頁標籤，防止唸出奇怪雜音
    voice_text = text.replace("---PAGE_SEP---", " ")
    
    corrections = {
        "補給": "補己",
        "Ethanol": "乙醇",
        "75%": "百分之七十五",
        "Acetic acid": "醋酸",
        "%": "趴",
        "75g": "七十五公克",
    }
    for word, correct in corrections.items():
        voice_text = voice_text.replace(word, correct)
    
    # 章節自動修正 (例如 3-1 -> 3之1)
    voice_text = re.sub(r'(\d+)-(\d+)', r'\1之\2', voice_text)
    
    clean_text = voice_text.replace("$", "")
    clean_text = re.sub(r'[^\w\u4e00-\u9fff\d，。！？「」～ ]', '', clean_text)
    
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 💡 專家修正：解決單獨化學式無法渲染問題 ---
def clean_for_eye(text):
    # 1. 物理洗淨編碼與標籤
    t = text.replace('\u00a0', ' ').replace("---PAGE_SEP---", "")
    
    # 2. 🔵 核心修復：把單獨出現的聲音標記自動轉換回 LaTeX 格式
    # 邏輯：偵測類似 C～～ O～～ two～～ 並在其前後加上 $$ 確保單獨一行也能渲染
    # 我們利用正則表達式，尋找那些被括號包住或單獨存在的聲音標記
    t = re.sub(r'([A-Z][a-z]?～～\s*(?:[a-z0-9]+～～\s*)*)', r'$$\1$$', t)
    
    # 3. 移除多餘的波浪號，讓文字稿畫面乾淨 (但語音引擎那邊會保留，不用擔心)
    t = t.replace("～～", "")
    return t

# --- 3. 側邊欄 (完整原封不動內容) ---
st.sidebar.title("打開實驗室大門-金鑰")

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
    <b>📖 值日生啟動指南 (6項說明)：</b><br>
    1. 前往 <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#01579b; font-weight:bold;">Google AI Studio</a>。<br>
    2. 登入google帳號，第一次只要打勾即可產生金鑰<br>
    3. 點擊 <b>Create API key</b> 按鈕。<br>
    4. 複製產生的金鑰代碼。<br>
    5. 貼回下方「實驗室啟動金鑰」區。<br>
    6. 按下 Enter 即可啟動曉臻助教！
</div>
""", unsafe_allow_html=True)

user_key = st.sidebar.text_input("🔑 實驗室啟動金鑰", type="password", key="tower_key")
st.sidebar.divider()
st.sidebar.subheader("💬 曉臻問題箱")
student_q = st.sidebar.text_input("打字問曉臻：", key="science_q")
uploaded_file = st.sidebar.file_uploader("📸 照片區：", type=["jpg", "png", "jpeg"], key="science_f")

# --- 修改點：確保圖片快取不會遺失 ---
if "class_started" not in st.session_state: st.session_state.class_started = False
if "display_images" not in st.session_state: st.session_state.display_images = []
if "res_text" not in st.session_state: st.session_state.res_text = ""
   
# --- 4. 曉臻教學核心指令 (互動測驗加強版) ---
SYSTEM_PROMPT = """
你是資深自然科學助教曉臻。你現在要進行一場約 20 分鐘的深度講義導讀。
每一頁產出必須嚴格包含「顯示稿」與包裹在 [[VOICE_START]]...[[VOICE_END]] 內的「隱藏讀音稿」。

1. 【顯示稿規範 (學生看的)】：
   - ⚠️ 嚴禁出現「～～」。化學式必須使用標準 LaTeX。
   - 範例：藍色硫酸銅晶體 $$CuSO_{4} \cdot 5H_{2}O$$。

2. 【隱藏讀音稿規範 (曉臻唸的)】：
   - ⚠️ 必須包裹在 [[VOICE_START]] 與 [[VOICE_END]] 之間。
   - ⚠️ 慢速標記：字母、數字後必加「～～」。
   - ⚠️ 結晶水規範：點號（·）必須翻譯為『帶 X 個結晶水』。
   - 範例：[[VOICE_START]] 這是 C～～ u～～ S～～ O～～ four～～ 帶五個結晶水，也就是硫酸銅晶體 [[VOICE_END]]

4. 【互動與開場】：
   - 開場必從【曉臻科學小知識庫】隨機選取一則，並連結至今日課程。
   - 結尾必喊：『這就是自然科學 the 真理！』
   - 每一頁最後必須出 2 題隨堂填充練習題。
   - 題目格式：『隨堂練習 Q1：[題目內容] _______。』
   - 答案格式：『答案 A1：[標準答案]。』

5. 【科學開場與馬拉松人設】：
   - 妳是馬拉松選手 (半馬PB 92分)。
   - 語氣要有耐心、緩慢，適度增加思考性的停頓詞（如：『我們思考一下...』）。
   - 結尾必含：『熱身一下，待會下課老師就要去跑步了』。

6. 【化學式規範 (讀音專用)】：
   - 二氧化碳 ➔ C～～ O～～ two～～ 也就是二氧化碳
   - 雙氧水 ➔ H～～ two～～ O～～ two～～ 也就是雙氧水
   - 乙醇 ➔ Ethanol (乙醇)
   - 結晶水 ➔ C～～ u～～ S～～ O～～ four～～ 帶五個結晶水，也就是硫酸銅晶體

7. 【翻頁與偵測】：
   - 解說完當頁內容才唸『翻到第 X 頁』。
   - 每頁解說最開頭加上標籤『---PAGE_SEP---』。
   - 僅當圖片明確出現「練習」二字才啟動題目模式。

# --- 曉臻科學小知識庫 ---
1. BDNF：運動能促進「腦源性神經滋養因子」分泌。
2. 鳶尾素 (Irisin)：肌肉運動時會分泌這種激素。
3. 海馬迴增生：有氧運動能增加大腦海馬迴的血流量，這是大腦中負責長期記憶與空間導航的核心。
4. 前額葉皮質：規律跑步能活化負責決策與專注的「前額葉」，讓學生在處理複雜物理題時邏輯更清晰。
5. 神經遞質平衡：運動能調節麩胺酸與 GABA 的平衡，這就像幫大腦「重新開機」，能有效緩解考前焦慮。
6. 線粒體動力：運動會增加神經細胞內的線粒體密度，提供大腦在高強度思考時所需的 ATP 能量。
7. 突觸塑性：身體活動會增加神經元突觸的密度，讓大腦的「迴路」更寬闊，學習新知識的速度更快。
8. 內啡肽 (Endorphins)：這就是「跑者愉悅」的來源，能提升大腦對學習壓力的耐受度，讓人心情變好。
9. 晝夜節律：白天的適度運動能調節褪黑激素分泌，改善睡眠品質，而充足的睡眠是記憶固化的關鍵。
10. 鏡像神經元：集體運動（如接力賽）能活化鏡像神經元，提升學生的社交理解與團隊合作能力。
"""

# --- 5. 導航系統 ---
col1, col2, col3 = st.columns([1, 1, 1])
with col1: vol_select = st.selectbox("📚 冊別選擇", ["第一冊", "第二冊", "第三冊", "第四冊", "第五冊", "第六冊"], index=3)
with col2: chap_select = st.selectbox("🧪 章節選擇", ["第一章", "第二章", "第三章", "第四章", "第五章", "第六章"], index=2)
with col3: start_page = st.number_input("🏁 起始頁碼", 1, 100, 1, key="start_pg")

filename = f"{vol_select}_{chap_select}.pdf"
pdf_path = os.path.join("data", filename)

# --- 主畫面邏輯 ---
if not st.session_state.class_started:
    # 📸 曉臻封面圖讀取邏輯
    cover_image_path = None
    for ext in [".jpg", ".png", ".jpeg", ".JPG", ".PNG"]:
        temp_path = os.path.join("data", f"cover{ext}")
        if os.path.exists(temp_path):
            cover_image_path = temp_path
            break
            
    if cover_image_path:
        st.image(Image.open(cover_image_path), use_container_width=True)
    else:
        st.info("🏃‍♀️ 曉臻老師正在起跑線上熱身準備中...")
    
    st.divider()
    if st.button(f"🏃‍♀️點擊-開始今天的ai自然課程", type="primary", use_container_width=True):
        if user_key and os.path.exists(pdf_path):
            with st.spinner("曉臻正在超音速備課中..."):
                try:
                    doc = fitz.open(pdf_path)
                    images_to_process, display_images_list = [], []
                    pages_to_read = range(start_page - 1, min(start_page + 4, len(doc)))
                    for p in pages_to_read:
                        pix = doc.load_page(p).get_pixmap(matrix=fitz.Matrix(2, 2))
                        img = Image.open(io.BytesIO(pix.tobytes()))
                        images_to_process.append(img)
                        display_images_list.append((p + 1, img))
                    
                    genai.configure(api_key=user_key)
                    MODEL = genai.GenerativeModel('models/gemini-2.5-flash') 
                    # --- 第 231 行開始貼上：影分身拆分手術 ---
                    res = MODEL.generate_content([f"{SYSTEM_PROMPT}\n導讀P.{start_page}起內容。"] + images_to_process)
                    
                    # 🔴 專家核心邏輯：物理洗淨編碼並分離顯示與讀音
                    raw_res = res.text.replace('\u00a0', ' ')

                    # 1. 影分身：提取 [[VOICE_START]] 到 [[VOICE_END]] 之間的隱藏讀音內容
                    # re.DOTALL 確保即便內容跨行也能完整抓取
                    voice_matches = re.findall(r'\[\[VOICE_START\]\](.*?)\[\[VOICE_END\]\]', raw_res, re.DOTALL)
                    voice_full_text = " ".join(voice_matches) if voice_matches else raw_res

                    # 2. 產生語音 (這裡會包含結晶水、之、以及所有慢速標記)
                    st.session_state.audio_html = asyncio.run(generate_voice_base64(voice_full_text))

                    # 3. 顯示稿 (挖掉所有隱藏標籤，只留下乾淨的 LaTeX 內容)
                    # 這樣就不會再出現慘不忍睹的 $$$$ 亂碼了
                    display_res = re.sub(r'\[\[VOICE_START\]\].*?\[\[VOICE_END\]\]', '', raw_res, flags=re.DOTALL)
                    st.session_state.res_text = display_res
                    
                    st.session_state.display_images = display_images_list
                    st.session_state.class_started = True
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ 發生錯誤：{e}")
        elif not user_key:
            st.warning("🔑 請先輸入實驗室啟動金鑰。")
        else:
            st.error(f"📂 找不到講義文件：{filename}")
else:
    # 狀態 B: 上課中
    st.success("🔔 曉臻老師正在上課中！")
    if "audio_html" in st.session_state: st.markdown(st.session_state.audio_html, unsafe_allow_html=True)
    st.divider()

    # 🔵 專家修正處：先洗掉隱形空格，再精確切割
    raw_text = st.session_state.get("res_text", "").replace('\u00a0', ' ')
    parts = [p.strip() for p in raw_text.split("---PAGE_SEP---") if p.strip()] 

    # 顯示開場白 (第一段文字)
    if len(parts) > 0:
        with st.chat_message("曉臻"): 
            st.markdown(clean_for_eye(parts[0]))

    # 顯示圖片與對應的文字稿
    for i, (p_num, img) in enumerate(st.session_state.display_images):
        st.image(img, caption=f"🏁 第 {p_num} 頁講義", use_container_width=True)
        
        # 🔵 專家修正處：確保索引 i 準確對準 parts 內容，解決 2、4 頁消失問題
        # 注意：因為第一段是開場白，所以後續文字稿要從 parts[i+1] 開始對應
        if (i + 1) < len(parts):
            st.markdown(f'<div class="transcript-box"><b>📜 曉臻老師的逐字稿 (P.{p_num})：</b><br>{clean_for_eye(parts[i+1])}</div>', unsafe_allow_html=True)
        st.divider()

    if st.button("🏁 下課休息 (回到首頁)"):
        st.session_state.class_started = False
        st.rerun()
