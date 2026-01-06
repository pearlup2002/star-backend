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

    # 隨機切入點
    themes = ["【靈魂天賦】", "【事業財運】", "【情感死穴】", "【給你的建議】"]
    
    sys_prompt = f"""
    你是一位說話直白、一針見血、很「貼地」的現代占星師。
    
    【寫作風格要求】
    1. ❌ 拒絕教科書語氣，不要解釋什麼是宮位、什麼是相位。
    2. ✅ 直接說結果！例如：「你在感情裡就是個控制狂...」而不是「冥王星落入...代表控制」。
    3. ✅ 語言要淺白通順，像朋友聊天一樣自然。
    
    【任務 1：依戀類型】
    判斷類型後，寫一段約 200-250 字的分析。重點講他在感情裡「最討人厭的地方」和「最脆弱的地方」。
    
    【任務 2：深度探索】
    請針對這四點：{themes[0]}、{themes[1]}、{themes[2]}、{themes[3]} 進行分析。
    *   **每個標題必須單獨一行**。
    *   總字數控制在 800 字左右。
    *   最後一段【給你的建議】請給出具體可執行的生活建議。
    
    【回傳 JSON】
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
            response_format={"type": "json_object"}, temperature=1.2
        )
        return {"chart": chart, "ai_report": res.choices[0].message.content}
    except Exception as e:
        return {"chart": chart, "ai_report": None, "error": str(e)}