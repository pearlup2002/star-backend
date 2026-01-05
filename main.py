from fastapi import FastAPI, HTTPException
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

@app.get("/")
def read_root():
    return {"status": "Star Mirror Backend v2 is Running"}

@app.post("/analyze")
def analyze_chart(req: ChartRequest):
    # 1. 算出星盤 (含八字五行)
    try:
        chart_data = engine.calculate_positions(
            req.year, req.month, req.day, req.hour, req.minute, req.lat, req.lon, req.is_time_unknown
        )
    except Exception as e:
        return {"error": f"Calculation Error: {str(e)}"}
    
    # 2. 準備 AI 提示詞
    # 判斷是否降級
    time_info = "出生時間已知"
    if req.is_time_unknown:
        time_info = "出生時間未知（請忽略宮位、上升星座與月亮具體度數的分析，重點放在行星落座與相位）"

    # 把數據轉成文字餵給 AI
    western = chart_data['western']['planets']
    chinese = chart_data['chinese']
    
    chart_summary = f"""
    【基本資料】{time_info}
    【西方星盤】
    太陽: {western['sun']['sign']}
    月亮: {western['moon']['sign']}
    水星: {western['mercury']['sign']}
    金星: {western['venus']['sign']}
    火星: {western['mars']['sign']}
    上升: {chart_data['western']['rising']}
    【中式八字】
    日主(命主屬性): {chinese['self_element']}
    五行分佈: {json.dumps(chinese['five_elements'], ensure_ascii=False)}
    """
    
    system_prompt = """
    你是一位資深的心理占星與命理大師。請根據用戶數據，輸出繁體中文 JSON 格式報告。
    語氣要求：溫暖、療癒、專業。
    
    必須回傳嚴格的 JSON 格式，不要 Markdown：
    {
      "attachment_style": "焦慮型/迴避型/安全型/恐懼型",
      "attachment_desc": "依戀類型傾向分析（約250字）。結尾必須加上：『（註：此結果依據星盤分析，不構成心理咨詢和專業意見）』",
      "deep_exploration": "星盤深度探索（約1000字）。每次請隨機選擇一個切入點（如：潛意識陰影、靈魂藍圖、原生家庭業力、事業天賦）進行深入解讀，確保每次生成內容不同。若時間未知，請勿分析宮位。"
    }
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"用戶數據：{chart_summary}"},
            ],
            response_format={ "type": "json_object" },
            temperature=1.2 # 提高隨機性，讓每次深度探索都不同
        )
        ai_content = response.choices[0].message.content
        
        return {
            "chart": chart_data,
            "ai_report": ai_content
        }

    except Exception as e:
        print(f"DeepSeek Error: {e}")
        return {
            "chart": chart_data,
            "ai_report": None,
            "error": str(e)
        }