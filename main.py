from fastapi import FastAPI
from pydantic import BaseModel
import os
import engine
from openai import OpenAI
import random

app = FastAPI()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

class ChartRequest(BaseModel):
    year: int; month: int; day: int; hour: int = 12; minute: int = 0; lat: float = 22.3; lon: float = 114.2; is_time_unknown: bool = False

@app.post("/analyze")
def analyze_chart(req: ChartRequest):
    chart = engine.calculate_positions(req.year, req.month, req.day, req.hour, req.minute, req.lat, req.lon, req.is_time_unknown)
    
    w = chart['western']['planets']
    summary = f"太陽{w['sun']['sign']}, 月亮{w['moon']['sign']}, 上升{chart['western']['rising']}, 金星{w['venus']['sign']}, 火星{w['mars']['sign']}。日主{chart['chinese']['self_element']}。"

    # 隨機切入點 (保持新鮮感)
    themes = ["【靈魂藍圖與潛能】", "【金錢觀與事業運】", "【情感糾葛與正緣】", "【潛意識陰影與轉化】"]
    random.shuffle(themes)
    
    sys_prompt = f"""
    你是一位極具洞察力的心理占星大師。請分析用戶星盤並回傳 JSON。
    
    【深度探索寫作要求】
    1. 必須包含這四個章節：{themes[0]}、{themes[1]}、{themes[2]}、【綜合建議】。
    2. 每個章節至少 200 字，總字數必須接近 1000 字。
    3. 語氣：深刻、一針見血、不用客套話。
    4. 內容：結合宮位與相位進行具體分析，不要只講空泛的星座特質。
    
    【回傳格式】
    {{
      "attachment_style": "...",
      "attachment_desc": "...",
      "deep_exploration": "..."
    }}
    """
    
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": summary}],
            response_format={"type": "json_object"}, temperature=1.1
        )
        return {"chart": chart, "ai_report": res.choices[0].message.content}
    except Exception as e:
        return {"chart": chart, "ai_report": None, "error": str(e)}