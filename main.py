# Star Mirror Backend - v2.0 (Fixed Order & New AI Persona)
from fastapi import FastAPI
from pydantic import BaseModel
import os
import sys
from pathlib import Path

# 確保當前目錄在 Python 路徑中
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import engine
import bazi_engine
from openai import OpenAI

# ==========================================
# 1. 初始化 App (必須放在最前面！)
# ==========================================
app = FastAPI()

# 2. 初始化 OpenAI Client
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

# 3. 定義資料模型
class ChartRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    lat: float = 22.3
    lon: float = 114.2
    is_time_unknown: bool = False

# ==========================================
# 4. 定義 API 路由
# ==========================================
@app.post("/analyze")
def analyze_chart(req: ChartRequest):
    # --- A. 計算西方星盤 ---
    chart = engine.calculate_positions(req.year, req.month, req.day, req.hour, req.minute, req.lat, req.lon, req.is_time_unknown)
    
    # --- B. 計算東方八字 (修復 0% 問題) ---
    # 確保 chinese 結構存在
    if 'chinese' not in chart:
        chart['chinese'] = {}
    
    # 設置默認值（以防計算失敗）
    default_five_elements = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
    chart['chinese']['five_elements'] = default_five_elements
    bazi_text = "八字計算失敗"
    
    try:
        bazi_data = bazi_engine.get_bazi_analysis(req.year, req.month, req.day, req.hour, req.minute)
        
        # 注入數據供前端使用
        if bazi_data and 'percentages' in bazi_data:
            chart['chinese']['five_elements'] = bazi_data['percentages']
        
        # 獲取文字供 AI 使用
        if bazi_data and 'bazi_text' in bazi_data:
            bazi_text = bazi_data['bazi_text']
    except Exception as e:
        import traceback
        error_msg = f"八字計算錯誤: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        # 保持默認值，確保前端能收到數據結構

    # --- C. 準備 AI 閱讀的資料 ---
    w = chart['western']['planets']
    summary = (
        f"用戶星盤資料：\n"
        f"太陽{w['sun']['sign']}, 月亮{w['moon']['sign']}, 上升{chart['western']['rising']}。\n"
        f"金星{w['venus']['sign']}, 火星{w['mars']['sign']}, 土星{w['saturn']['sign']}。\n"
        f"八字：{bazi_text}。\n"
        f"五行能量：{chart['chinese'].get('five_elements', 'N/A')}。"
    )

    # --- D. 定義 AI 人格 (心理學冷讀風格) ---
    sys_prompt = """
    你是一款名為《Star Mirror》的專業星盤分析引擎。你的風格是：**一針見血、深刻、甚至帶有心理學的冷讀色彩**。

    【分析規則 - 絕對嚴格執行】
    1. **禁止建議**：絕對不要寫「建議你...」、「你可以試著...」。用戶不需要心靈雞湯，他們需要被看穿。
    2. **禁止名詞解釋**：不要解釋「什麼是二宮」、「什麼是金星」。直接說結論。
    3. **四大維度**：請務必從以下四個角度進行分析，每個角度一段：
       - **內在靈魂 (The Soul)**：潛意識、安全感來源、恐懼。
       - **處事風格 (Execution)**：工作邏輯、決策模式、行動力。
       - **愛情與慾望 (Love & Desire)**：依戀模式、性吸引力、情感盲點。
       - **人際博弈 (Social Strategy)**：社交手段、防禦機制、給人的印象。

    4. **依戀類型判定**：
       根據星盤（尤其是月亮與土星相位），將用戶歸類為以下四者之一，並用粗體標示：
       - **安全型依戀 (Secure)**
       - **焦慮型依戀 (Anxious)**
       - **逃避型依戀 (Avoidant)**
       - **恐懼-逃避型依戀 (Fearful-Avoidant)**

    【語氣範例】
    (O) 正確：「你外表看似隨和，其實內心極度計較公平。這是因為你的月亮天秤在...」
    (X) 錯誤：「月亮代表內心，落在天秤座的人通常...」

    請以 Markdown 格式輸出，不要有 JSON 結構，直接進入文章標題與內容。
    """
    
    # --- E. 呼叫 DeepSeek AI ---
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": sys_prompt}, 
                {"role": "user", "content": summary}
            ],
            temperature=1.3 
        )
        return {"chart": chart, "ai_report": res.choices[0].message.content}
    except Exception as e:
        return {"chart": chart, "ai_report": None, "error": str(e)}