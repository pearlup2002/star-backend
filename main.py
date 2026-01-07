from fastapi import FastAPI
from pydantic import BaseModel
import os
import engine
import bazi_engine
from openai import OpenAI
import json

# ==========================================
# 關鍵修正：必須先初始化 app，才能使用 @app
# ==========================================
app = FastAPI()

# 初始化 OpenAI Client
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

# 定義資料模型
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
# 路由定義 (現在 app 已經存在，這裡就不會報錯了)
# ==========================================
@app.post("/analyze")
def analyze_chart(req: ChartRequest):
    # 1. 計算星盤與八字
    chart = engine.calculate_positions(req.year, req.month, req.day, req.hour, req.minute, req.lat, req.lon, req.is_time_unknown)
    
    try:
        bazi_data = bazi_engine.get_bazi_analysis(req.year, req.month, req.day, req.hour, req.minute)
        if 'chinese' not in chart:
            chart['chinese'] = {}
        chart['chinese']['five_elements'] = bazi_data['percentages']
        bazi_text = bazi_data['bazi_text']
    except Exception as e:
        print(f"八字計算錯誤: {e}")
        bazi_text = "八字計算失敗"

    # 2. 準備使用者資料 Summary
    w = chart['western']['planets']
    summary = (
        f"用戶星盤資料：\n"
        f"太陽{w['sun']['sign']}, 月亮{w['moon']['sign']}, 上升{chart['western']['rising']}。\n"
        f"金星{w['venus']['sign']}, 火星{w['mars']['sign']}, 土星{w['saturn']['sign']}。\n"
        f"八字：{bazi_text}。\n"
        f"五行能量：{chart['chinese'].get('five_elements', 'N/A')}。"
    )

    # 3. 定義 AI 人格與指令 (Markdown 模式)
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
    
    # 4. 呼叫 AI (純文字模式)
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