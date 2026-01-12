import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import datetime

# --- 1. 頁面設定 ---
st.set_page_config(page_title="哩來練 Li-Lai-Lian", page_icon="💪", layout="wide")

# --- 2. 側邊欄：設定與使用者資料 ---
with st.sidebar:
    st.title("💪 哩來練 設定")
    
    # API Key 輸入
    api_key = st.text_input("請輸入 Google Gemini API Key", type="password")
    
    st.markdown("---")
    st.subheader("👤 使用者檔案")
    user_name = st.text_input("你的名字/暱稱", value="帥哥")
    target = st.selectbox("目前目標", ["減脂", "增肌", "維持"])
    tdee = st.number_input("TDEE (每日總消耗熱量)", value=2200)
    body_fat = st.number_input("目前體脂率 (%)", value=25.0)
    
    # 組合 Context 字串
    user_context = f"[User: {user_name}, Target: {target}, TDEE: {tdee}, Current_Fat: {body_fat}%]"
    
    st.markdown("---")
    st.caption("版本: v1.1 (Flash Debug Mode)")

# --- 3. 主程式邏輯 ---
st.title("🏋️‍♂️ 哩來練 (Li-Lai-Lian) AI 教練")

if not api_key:
    st.warning("👈 請先在左側側邊欄輸入你的 API Key 才能開始使用喔！")
else:
    # 設定 API Key
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"API Key 設定失敗: {e}")

    # --- 🛠️ 診斷工具區塊 (如果報錯，請點開這裡) ---
    with st.expander("🔧 如果發生 404 錯誤，請點這裡檢查模型"):
        st.info("這是一個診斷工具，用來檢查你的 API Key 能看到哪些模型。")
        if st.button("🔍 列出我能用的所有模型"):
            try:
                st.write("正在查詢 API...")
                available_models = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        available_models.append(m.name)
                        st.code(m.name) # 顯示模型名稱
                
                if not available_models:
                    st.error("❌ 你的 API Key 似乎無法存取任何模型，請重新建立一個 API Key。")
                elif "models/gemini-1.5-flash" in available_models:
                    st.success("✅ 檢測成功！你的帳號可以使用 gemini-1.5-flash。")
                else:
                    st.warning("⚠️ 你的帳號似乎沒有 Flash 模型，請嘗試使用列表中的其他模型名稱。")
            except Exception as e:
                st.error(f"查詢失敗，請檢查 API Key 是否正確。錯誤訊息: {e}")

    # --- 4. AI 核心設定 ---
    # 這裡就是我們設計的教練大腦
    sys_instruction = """
    Role: 你是 "哩來練 (Li-Lai-Lian)"，一位專業、幽默且嚴格的台灣 AI 私人教練與營養師。
    Objective: 解析使用者輸入(飲食照片/運動截圖/文字)，輸出 JSON 格式，並根據 User Context 給予建議。
    Context Protocol: 每次對話開頭會提供使用者的 Context，必須據此調整建議 (如 TDEE 警告)。
    
    Output Format (Strict JSON Only):
    你的回應必須包含一個 JSON 區塊，格式如下。JSON 區塊外可以包含你的口語回覆。
    ```json
    {
      "user_id": "String",
      "record_type": "diet/strength/cardio",
      "timestamp": "YYYY-MM-DD HH:MM",
      "item_name": "String",
      "data_metrics": {
        "calories": Number,
        "protein_g": Number,
        "carbs_g": Number,
        "fat_g": Number,
        "weight_kg": Number,
        "sets": Number,
        "reps": Number,
        "duration_min": Number,
        "avg_heart_rate": Number
      },
      "coach_comment": "String"
    }
    ```
    Tone: 台灣繁體中文，幽默，減脂期嚴格，增肌期鼓勵。
    """

    # --- 關鍵修正：使用最穩定的模型名稱設定 ---
    # 如果這裡還是 404，請把下面的 "gemini-1.5-flash" 改成診斷工具裡看到的名稱
    try:
        model = genai.GenerativeModel(
            model_name="gemini-3-flash-preview", 
            system_instruction=sys_instruction
        )
    except Exception as e:
        st.error(f"模型初始化失敗: {e}")

    # --- 5. 使用者介面 ---
    st.markdown("### 拍個照、上傳截圖，或是直接跟我說！")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📷 上傳影像")
        uploaded_file = st.file_uploader("選擇照片 (食物/器材/手錶截圖)", type=["jpg", "jpeg", "png"])
        image = None
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="預覽圖片", use_column_width=True)

    with col2:
        st.subheader("📝 文字補充")
        text_input = st.text_area("有什麼要補充的嗎？(例如：這是大碗的，或是我做了5組)", height=150)
        
        submit = st.button("🚀 送出分析")

    # --- 6. 處理與回應 ---
    if submit:
        with st.spinner("⏳ 哩來練正在分析中... (眼神銳利)"):
            try:
                # 準備傳送給 AI 的內容
                prompt_parts = [user_context] 
                if text_input:
                    prompt_parts.append(f"User Note: {text_input}")
                if image:
                    prompt_parts.append(image)
                
                if not image and not text_input:
                    st.warning("請至少提供照片或文字！")
                else:
                    # 發送請求
                    response = model.generate_content(prompt_parts)
                    
                    # 處理回應文字
                    full_text = response.text
                    
                    # 嘗試解析 JSON (為了顯示漂亮介面)
                    try:
                        # 簡單的 JSON 提取邏輯
                        json_str = full_text
                        if "```json" in full_text:
                            json_str = full_text.split("```json")[1].split("```")[0]
                        elif "```" in full_text:
                            json_str = full_text.split("```")[1].split("```")[0]
                        
                        data = json.loads(json_str)
                        
                        # 1. 顯示教練建議 (大字體)
                        st.success(f"🗣️ **教練說：** {data.get('coach_comment', '沒抓到建議')}")
                        
                        # 2. 顯示數據表格 (準備存檔用)
                        st.markdown("#### 📊 數據分析結果")
                        st.json(data)
                        
                    except Exception as e:
                        # 如果 JSON 解析失敗，直接把 AI 講的話全部印出來
                        st.warning("⚠️ 數據解析稍微有點問題，但以下是教練的回覆：")
                        st.write(full_text)
                        # st.error(f"JSON Error: {e}") # 除錯用

            except Exception as e:
                st.error(f"發生連線錯誤 (請檢查診斷工具): {e}")

