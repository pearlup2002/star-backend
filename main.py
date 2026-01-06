from fastapi import FastAPI
from pydantic import BaseModel
import os
import engine
from openai import OpenAI
import json
import random

app = FastAPI()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

class ChartRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    lat: float = 22.3
    lon: float = 114.2
    is_time_unknown: bool = False

@app.post("/analyze")
def analyze_chart(req: ChartRequest):
    chart_data = engine.calculate_positions(
        req.year, req.month, req.day, req.hour, req.minute, req.lat, req.lon, req.is_time_unknown
    )
    
    # 隨機標題庫 (解決沉悶問題)
    topics = [
        "【潛意識與安全感】、 \n\n【職場致勝關鍵】、 \n\n【情感致命傷】",
        "【靈魂的天賦】、 \n\n【人際關係盲點】、 \n\n【財富能量流動】",
        "【外在面具與真實自我】、 \n\n【愛情中的控制與臣服】、 \n\n【事業突破口】"
    ]
    selected_topic = random.choice(topics)

    system_prompt = f"""
    你是一位說話直白、不打官腔的現代占星師。
    
    【任務 1：依戀類型 (固定風格)】
    請根據星盤判斷他是「焦慮型、迴避型、安全型、恐懼型」哪一種。
    分析必須客觀、心理學導向，每次對於相同星盤的判斷必須一致，不要隨機發揮。
    
    【任務 2：深度探索 (多變風格)】
    請針對以下三個維度進行深度解析：{selected_topic}。
    
    【格式要求】
    1. ❌ 嚴禁使用「親愛的朋友」、「這張星盤顯示」等廢話。
    2. ✅ 標題請使用【】符號，並且標題要變成黃色 (前端會處理)。
    3. ✅ 每一段直接講重點，例如：「你在工作中是個控制狂...」。
    4. 回傳 JSON：
    {{
      "attachment_style": "類型名稱",
      "attachment_desc": "直接分析他在關係中的具體行為與恐懼，不要有開場白。",
      "deep_exploration": "文章內容..."
    }}
    """
    
    western = chart_data['western']['planets']
    prompt_content = f"太陽{western['sun']['sign']}, 月亮{western['moon']['sign']}, 金星{western['venus']['sign']}, 上升{chart_data['western']['rising']}。"

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt_content}],
            response_format={ "type": "json_object" },
            temperature=1.0 # 稍微降低隨機性以保證依戀準確，但保留文章變化
        )
        return {"chart": chart_data, "ai_report": response.choices[0].message.content}
    except Exception as e:
        return {"chart": chart_data, "ai_report": None, "error": str(e)}