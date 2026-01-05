from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import engine
from openai import OpenAI

app = FastAPI()

# 設定 DeepSeek 客戶端 (從 Render 環境變數讀取鑰匙)
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 定義請求格式
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
    return {"status": "Star Mirror Backend is running with DeepSeek AI"}

# 舊的純計算接口 (保留備用)
@app.post("/calculate")
def calculate_chart(req: ChartRequest):
    return engine.calculate_positions(
        req.year, req.month, req.day, req.hour, req.minute, req.lat, req.lon, req.is_time_unknown
    )

# --- 新增：深度分析接口 (AI 寫作文) ---
@app.post("/analyze")
def analyze_chart(req: ChartRequest):
    # 1. 先算出星盤數據
    chart_data = engine.calculate_positions(
        req.year, req.month, req.day, req.hour, req.minute, req.lat, req.lon, req.is_time_unknown
    )
    
    # 2. 準備給 AI 的提示詞 (Prompt)
    # 這裡把星盤數據轉成文字，餵給 AI
    chart_summary = f"太陽在{chart_data['sun']['sign']}, 月亮在{chart_data['moon']['sign']}, 金星在{chart_data['venus']['sign']}, 火星在{chart_data['mars']['sign']}。"
    
    system_prompt = """
    你是一位資深的心理占星專家。請根據用戶的星盤數據，用溫暖、療癒、一針見血的語氣（繁體中文）撰寫分析報告。
    請嚴格按照以下 JSON 格式回傳，不要包含 markdown 標記：
    {
      "attachment_style": "焦慮型/迴避型/安全型 (請根據星盤判斷)",
      "attachment_desc": "關於依戀類型的簡短分析 (約200字)",
      "deep_analysis": "深度分析文章，包含性格盲點、情感模式、事業潛力、靈魂使命 (約1000字)"
    }
    """
    
    user_prompt = f"用戶的星盤數據如下：{chart_summary}。請進行分析。"

    try:
        # 3. 呼叫 DeepSeek
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={ "type": "json_object" }, # 強制回傳 JSON
            temperature=1.0
        )
        
        # 4. 取得 AI 寫的內容
        ai_content = response.choices[0].message.content
        
        # 5. 回傳結果 (包含星盤數據 + AI文章)
        return {
            "chart": chart_data,
            "ai_report": ai_content # 這裡是字串，前端需要再解析一次 JSON
        }

    except Exception as e:
        print(f"DeepSeek Error: {e}")
        # 如果 AI 失敗，至少回傳星盤數據，不要報錯
        return {
            "chart": chart_data,
            "ai_report": None,
            "error": str(e)
        }