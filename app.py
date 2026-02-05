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

# --- 💡 視覺洗淨函式 ---
def clean_for_eye(text):
    t = text.replace("---PAGE_SEP---", "")
    t = re.sub(r'([a-zA-Z0-9])～～\s*', r'\1', t) 
    t = t.replace("～～", "")
    return t

# --- 3. 側邊欄 (完整原封不動內容) ---
st.sidebar.title("門 打開實驗室大門-金鑰")

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

# --- 4. 曉臻教學核心指令 ---
SYSTEM_PROMPT = """
你是資深自然科學助教曉臻，馬拉松選手 (PB 92分)。
你現在要導讀連續 5 頁講義。請遵守規範：

1. 【科學人開場】：
   - 請從下方的「科學小知識庫」中「嚴格挑選僅限一則」進行 30 秒開場，不可重複列出多則。
   - 關鍵字：BDNF (腦源性神經滋養因子)、海馬迴增生、線粒體與能量、神經塑性。
   - 格式：『根據科學研究...』或『在《科學人》相關報導中提到...』。
   - 結尾必含：『熱身一下下課老師就要去跑步了』。
2. 【翻頁】：解說完當頁內容才唸『翻到第 X 頁』。每頁解說最開頭加上標籤『---PAGE_SEP---』。
3. 【偵測】：僅當圖片明確出現「練習」二字才啟動題目模式。講義中的「底線」是重點提醒，嚴禁誤判為題目。
4. 【轉譯規範】：
   - 慢速標記：英文、數字、化學式字母後方必須加「～～」與空格。
   - ⚠️ 係數整數化規則：如果觀察法過程中出現分數（如 $\frac{7}{2}$），請引導學生進行『全體擴大』。讀音範例：『現在係數出現了二分之七，我們要全體乘以二，化簡為最簡整數比！』
   - ⚠️ 係數處理：化學式前方的「係數」必須與後方元素斷開，係數後方也要加「～～」。
   - 範例：2A ➔ 「2～～ a～～ 」、2H2O ➔ 「2～～ H～～ two～～ O～～ 」
   - ⚠️ 化學式讀法：遇到化學式，請在讀音導引中先唸配速字母，接著必含「也就是 [中文名稱]」。
   - 結晶水：遇到點號（·）翻譯為『帶 X 個結晶水』。
   - 範例格式：
     * 氧氣 ➔ $$O_{2}$$ (O～～ two～～ 也就是氧氣)
     * 雙氧水 ➔ $$H_{2}O_{2}$$ (H～～ two～～ O～～ two～～ 也就是雙氧水)
     * 乙醇 ➔ Ethanol (乙醇)
     * 結晶水 ➔ $$CuSO_{4} \cdot 5H_{2}O$$ (C～～ u～～ S～～ O～～ four～～ 帶五個結晶水)
5. 【結尾】：必喊『這就是自然科學的真理！』。
# --- 曉臻科學小知識庫 (來源：科學人與大腦科學研究) ---
1. BDNF：運動能促進「腦源性神經滋養因子」分泌，這被科學人譽為大腦的「神經肥料」，能強化記憶連結。
2. 鳶尾素 (Irisin)：肌肉運動時會分泌這種激素，它能跨越大腦屏障，保護神經元免受老化損害。
3. 海馬迴增生：有氧運動能直接增加大腦海馬迴的血流量，這是大腦中負責長期記憶與空間導航的核心。
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

if "class_started" not in st.session_state: st.session_state.class_started = False
if "res_text" not in st.session_state: st.session_state.res_text = ""

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
    if st.button(f"🏃‍♀️ 開始馬拉松課程", type="primary", use_container_width=True):
        if user_key and os.path.exists(pdf_path):
            with st.spinner("曉臻正在翻閱講義..."):
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
                    res = MODEL.generate_content([f"{SYSTEM_PROMPT}\n導讀P.{start_page}起內容。"] + images_to_process)
                    
                    st.session_state.res_text = res.text
                    st.session_state.audio_html = asyncio.run(generate_voice_base64(res.text))
                    st.session_state.display_images = display_images_list
                    st.session_state.class_started = True
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 發生錯誤：{e}")
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

    if st.button("🏁 下課休息 (回到首頁)"):
        st.session_state.class_started = False
        st.rerun()
