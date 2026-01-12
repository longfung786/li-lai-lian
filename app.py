import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import datetime

# --- 設定頁面 ---
st.set_page_config(page_title="哩來練 Li-Lai-Lian", page_icon="💪", layout="wide")

# --- 側邊欄：設定與使用者資料 ---
with st.sidebar:
    st.title("💪 哩來練 設定")
    
    # 這裡填入從 Google AI Studio 拿到的 API Key
    api_key = st.text_input("請輸入 Google Gemini API Key", type="password")
    
    st.markdown("---")
    st.subheader("👤 使用者檔案")
    user_name = st.text_input("你的名字/暱稱", value="帥哥")
    target = st.selectbox("目前目標", ["減脂", "增肌", "維持"])
    tdee = st.number_input("TDEE (每日總消耗熱量)", value=2200)
    body_fat = st.number_input("目前體脂率 (%)", value=25.0)
    
    # 組合 Context 字串 (這是要貼給 AI 的標籤)
    user_context = f"[User: {user_name}, Target: {target}, TDEE: {tdee}, Current_Fat: {body_fat}%]"
    
    st.markdown("---")
    st.info("💡 提示：記得去 Google AI Studio 申請 API Key 才能使用喔！")

# --- 主程式邏輯 ---
st.title("🏋️‍♂️ 哩來練 (Li-Lai-Lian) AI 教練")
st.markdown("### 拍個照、上傳截圖，或是直接跟我說！")

# 設定 Gemini 模型
if api_key:
    genai.configure(api_key=api_key)
    
    # 這裡就是我們剛剛設計的 System Instruction
    sys_instruction = """
    Role: 你是 "哩來練 (Li-Lai-Lian)"，一位專業、幽默且嚴格的台灣 AI 教練。
    Objective: 解析使用者輸入(飲食照片/運動截圖/文字)，輸出 JSON 格式，並根據 User Context 給予建議。
    Context Protocol: 必須參考提供的 User Context (TDEE, 體脂) 來調整建議語氣。
    
    Output Format (Strict JSON):
    請回傳如下格式的 JSON 字串，並在 JSON 後面附上你的建議文字：
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
        "duration_min": Number
      },
      "coach_comment": "String"
    }
    Tone: 台灣繁體中文，幽默，減脂期嚴格，增肌期鼓勵。
    """
    
    model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=sys_instruction)

    # 輸入區塊
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

    # 處理回應
    if submit:
        if not api_key:
            st.error("❌ 請先在左側輸入 API Key！")
        else:
            with st.spinner("⏳ 教練正在分析中... (哩來練正在看你的照片)"):
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
                        response = model.generate_content(prompt_parts)
                        
                        # 顯示結果
                        st.markdown("### 💬 教練的回饋")
                        
                        # 嘗試解析 JSON (為了美觀顯示)
                        try:
                            # 抓取 JSON 部分 (有些時候 AI 會在前後加 markdown 符號)
                            json_str = response.text
                            if "```json" in json_str:
                                json_str = json_str.split("```json")[1].split("```")[0]
                            elif "```" in json_str:
                                json_str = json_str.split("```")[1].split("```")[0]
                                
                            data = json.loads(json_str)
                            
                            # 顯示漂亮的建議卡片
                            st.success(f"🗣️ **{data.get('coach_comment')}**")
                            
                            # 顯示數據表格
                            st.markdown("#### 📊 解析數據 (準備存入 Sheet)")
                            st.json(data)
                            
                        except Exception as e:
                            # 如果 JSON 解析失敗，直接顯示原始文字
                            st.write(response.text)
                            st.error(f"解析數據時發生小錯誤，但教練還是有話說。錯誤: {e}")

                except Exception as e:
                    st.error(f"發生錯誤：{e}")

else:
    st.warning("👈 請先在左側側邊欄輸入你的 API Key 才能開始使用喔！")
