from fastapi import FastAPI
from pydantic import BaseModel
import os
import engine
from openai import OpenAI
import json

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
    # 1. 算出星盤
    try:
        chart_data = engine.calculate_positions(
            req.year, req.month, req.day, req.hour, req.minute, req.lat, req.lon, req.is_time_unknown
        )
    except Exception as e:
        return {"error": f"Calculation Error: {str(e)}"}
    
    # 2. 準備提示詞
    western = chart_data['western']['planets']
    
    chart_summary = f"""
    【星盤數據】
    太陽:{western['sun']['sign']}, 月亮:{western['moon']['sign']}, 上升:{chart_data['western']['rising']}
    水星:{western['mercury']['sign']}, 金星:{western['venus']['sign']}, 火星:{western['mars']['sign']}
    """
    
    # 這裡是最核心的修改：教 AI 怎麼說話
    system_prompt = """
    你是一位說話直擊人心、不打官腔的心理咨詢師。
    請根據星盤數據輸出 JSON。
    
    【寫作風格要求】
    1. ❌ 禁止使用「親愛的朋友」、「從星盤來看」等客套話。直接切入重點。
    2. ❌ 少用占星術語（如四分相、對分相），請直接翻譯成「性格特質」。
    3. ✅ 語言要淺白、現代、有 DeepSeek 的犀利風格（既溫暖又一針見血）。
    4. ✅ 深度探索必須分段，包含：【內在性格】、【情感模式】、【事業與處事】、【陰影與成長】。
    5. ✅ 字數要求：深度探索部分必須豐富飽滿，接近 800-1000 字。

    【回傳格式 (JSON)】
    {
      "attachment_style": "焦慮型 / 迴避型 / 安全型 / 混亂型 (僅回傳類型名稱)",
      "attachment_desc": "依戀傾向分析 (250字)。請分析他在親密關係中的具體表現、恐懼點與需求。不要解釋什麼是依戀，直接分析他。",
      "deep_exploration": "深度探索文章。請用 \\n\\n 換行來分段。不要寫標題（如標題一、標題二），直接用【】作為段落開頭。"
    }
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"分析此人：{chart_summary}"},
            ],
            response_format={ "type": "json_object" },
            temperature=1.2 # 高創造性
        )
        ai_content = response.choices[0].message.content
        
        return {
            "chart": chart_data,
            "ai_report": ai_content
        }

    except Exception as e:
        return {"chart": chart_data, "ai_report": None, "error": str(e)}