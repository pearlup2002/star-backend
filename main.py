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
    try:
        chart_data = engine.calculate_positions(
            req.year, req.month, req.day, req.hour, req.minute, req.lat, req.lon, req.is_time_unknown
        )
    except Exception as e:
        return {"error": str(e)}
    
    # 隨機主題
    topics = [
        "【潛意識與安全感】、 \n\n【職場致勝關鍵】、 \n\n【情感致命傷】",
        "【靈魂的天賦】、 \n\n【人際關係盲點】、 \n\n【財富能量流動】",
        "【外在面具與真實自我】、 \n\n【愛情中的控制與臣服】、 \n\n【事業突破口】"
    ]
    selected_topic = random.choice(topics)

    western = chart_data['western']['planets']
    
    # 構建更專業的數據描述
    chart_summary = f"""
    【星盤數據】
    太陽:{western['sun']['sign']}, 月亮:{western['moon']['sign']}, 上升:{chart_data['western']['rising']}
    水星:{western['mercury']['sign']}, 金星:{western['venus']['sign']}, 火星:{western['mars']['sign']}
    """
    
    # 如果有宮位數據，加入 AI 分析參考
    if 'houses' in chart_data['western'] and chart_data['western']['houses']:
        h = chart_data['western']['houses']
        # 挑選重點宮位給 AI (例如 1, 5, 7, 10宮)
        chart_summary += f"\n命宮:{h[0]['sign']}, 戀愛宮:{h[4]['sign']}, 夫妻宮:{h[6]['sign']}, 事業宮:{h[9]['sign']}"

    system_prompt = f"""
    你是一位說話直白、不打官腔的現代占星師。
    
    【任務 1：依戀類型】
    根據星盤判斷「焦慮型、迴避型、安全型、恐懼型」並分析 (約250字)。
    
    【任務 2：深度探索】
    請針對：{selected_topic} 進行深度解析。字數約 800-1000 字。
    
    【風格要求】
    1. ❌ 嚴禁廢話（如親愛的朋友）。
    2. ✅ 標題用【】。
    3. ✅ 內容必須具體，結合行星落座與宮位。
    
    回傳 JSON:
    {{
      "attachment_style": "...",
      "attachment_desc": "...",
      "deep_exploration": "..."
    }}
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": chart_summary}],
            response_format={ "type": "json_object" },
            temperature=1.0
        )
        return {"chart": chart_data, "ai_report": response.choices[0].message.content}
    except Exception as e:
        return {"chart": chart_data, "ai_report": None, "error": str(e)}