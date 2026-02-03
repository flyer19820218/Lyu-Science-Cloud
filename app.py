import streamlit as st
import google.generativeai as genai
import os, asyncio, edge_tts, re, base64, io, random
from PIL import Image

# --- 零件檢查：PDF 視力元件 ---
try:
    import fitz
except ImportError:
    st.error("❌ 零件缺失！請確保 requirements.txt 已加入 pymupdf 與 edge-tts。")
    st.stop()

# --- 1. 核心規範：視覺鎖定與 Apple 適配 (深度白晝協議) ---
st.set_page_config(page_title="Lyu-Science-Cloud", layout="wide")

st.markdown("""
    <style>
    /* 全黑文字、白色背景、翩翩體鎖定 */
    .stApp, [data-testid="stAppViewContainer"], .stMain {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', sans-serif !important;
    }
    
    /* 平板手機雙模文字適配 */
    .stMarkdown, p, span, label, li {
        color: #000000 !important;
        font-size: calc(1rem + 0.3vw) !important;
    }

    /* 指南方塊與按鈕視覺 */
    .guide-box { 
        border: 2px dashed #01579b; padding: 1.2rem; 
        border-radius: 12px; background-color: #f0f8ff; color: #000000; 
    }
    
    /* 蘋果設備防反黑補丁 */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
    }
    </style>
    <meta name="color-scheme" content="light">
""", unsafe_allow_html=True)

# --- 2. 曉臻語音引擎 (口語轉譯) ---
async def generate_voice_base64(text):
    # 清除劇本中殘留的符號，讓曉臻只唸翻譯好的口語中文
    clean_text = re.sub(r'[^\w\u4e00-\u9fff\d，。！？「」]', '', text)
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 核心 API 通行證指南 (曉臻助教版實裝) ---
st.title("🚀 自然曉臻助教版)")
st.markdown("""
<div class="guide-box">
    <b>📖 學生快速通行指南：</b><br>
    1. 前往 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 並登入。<br>
    2. 點擊 <b>Create API key</b>，<b>務必勾選兩次同意條款</b>。<br>
    3. 貼回下方「通行證」欄位按 Enter 邀請曉臻助教。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 通行證輸入區：", type="password")
st.divider()

# --- 4. 曉臻助教 6 項核心 API 規範 (SOP) ---
SYSTEM_PROMPT = """
你是一位資深理化助教。人設：助教曉臻，馬拉松選手 (PB 92分)。
1. 【開場】：隨機 15 秒關於跑步熱身與健康的重要性，提到熱身完要跟老師去跑步。
2. 【導航】：腳本開頭必須說：『各位同學，請翻到第 X 頁。』
3. 【公式】：LaTeX 格式，但聽覺劇本必須轉成中文口語 (如 n=m/M 唸作「莫耳數等於質量除以分子量」)。
4. 【視覺】：背景全白、文字全黑、翩翩體。解釋照片中的實驗現象。
5. 【手機適配】：內容簡潔，支援平板與手機雙模顯示。
"""

# --- 5. 啟動產線 ---
pdf_path = os.path.join("data", "二下第一章.pdf")
if user_key and os.path.exists(pdf_path):
    genai.configure(api_key=user_key)
    MODEL = genai.GenerativeModel('models/gemini-2.5-flash')
    doc = fitz.open(pdf_path)
    
    # 只要有頁碼選擇就可以了
    page_num = st.sidebar.number_input("請選擇講義頁碼", 1, doc.page_count, 1)
    
    if st.button(f"🚀 啟動【第 {page_num} 頁】星艦導讀"):
        # 渲染 PDF 頁面圖片
        page = doc.load_page(page_num - 1)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_data = Image.open(io.BytesIO(pix.tobytes()))
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.image(img_data, use_column_width=True) # 顯示教材
            
        with col2:
            with st.spinner("曉臻熱身中..."):
                prompt = f"{SYSTEM_PROMPT}\n【指令】：請導讀第 {page_num} 頁。分開『視覺內容』與『聽覺劇本』。"
                res = MODEL.generate_content([prompt, img_data])
                
                # 分離視覺與聽覺內容
                display_txt = res.text.split("【聽覺劇本】")[0].replace("【視覺內容】", "").strip()
                voice_txt = res.text.split("【聽覺劇本】")[-1].strip() if "【聽覺劇本】" in res.text else display_txt
                
                st.markdown(f"### 🗣️ 曉臻導讀：\n{display_txt}")
                st.markdown(asyncio.run(generate_voice_base64(voice_txt)), unsafe_allow_html=True)
else:
    if not user_key: st.warning