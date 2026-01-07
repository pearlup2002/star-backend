from fastapi import FastAPI
from pydantic import BaseModel
import os
import engine          # 保留：原本的西方星盤引擎
import bazi_engine     # 新增：刚刚建立的八字五行引擎
from openai import OpenAI
import random
import json

app = FastAPI()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

class ChartRequest(BaseModel):
    year: int; month: int; day: int; hour: int = 12; minute: int = 0; lat: float = 22.3; lon: float = 114.2; is_time_unknown: bool = False

@app.post("/analyze")
def analyze_chart(req: ChartRequest):
    # 1. 保留原有邏輯：計算西方星盤 (Chart 變數還在，不會不見)
    chart = engine.calculate_positions(req.year, req.month, req.day, req.hour, req.minute, req.lat, req.lon, req.is_time_unknown)
    
    # 2. 新增邏輯：計算八字五行 (修復前端 0% 的問題)
    try:
        bazi_data = bazi_engine.get_bazi_analysis(req.year, req.month, req.day, req.hour, req.minute)
        
        # 將五行數據注入到 chart 字典中，讓前端可以讀取
        if 'chinese' not in chart:
            chart['chinese'] = {}
        chart['chinese']['five_elements'] = bazi_data['percentages']
        # 順便把詳細的八字文字也存起來，給 AI 用
        bazi_text = bazi_data['bazi_text']
    except Exception as e:
        print(f"八字計算錯誤: {e}")
        bazi_text = "八字計算失敗"

    # 3. 準備給 AI 的資料 (加入五行數據讓 AI 更準)
    w = chart['western']['planets']
    summary = (
        f"用戶星盤資料：\n"
        f"太陽{w['sun']['sign']}, 月亮{w['moon']['sign']}, 上升{chart['western']['rising']}。\n"
        f"金星{w['venus']['sign']}, 火星{w['mars']['sign']}, 土星{w['saturn']['sign']}。\n"
        f"八字：{bazi_text}。\n"
        f"五行能量：{chart['chinese'].get('five_elements', 'N/A')} (這顯示缺什麼元素)。"
    )

    # 4. 更新 AI 邏輯：移除「建議」，加入「四大維度」與「恐懼型依戀」
    # 隨機挑選 4 個非建議的維度
    all_themes = [
        "【內在靈魂 (The Soul)】", 
        "【處事風格 (Execution)】", 
        "【愛情與慾望 (Love & Desire)】", 
        "【人際博弈 (Social Strategy)】",
        "【家庭與陰影 (Family)】",
        "【世界觀 (Worldview)】"
    ]
    selected_themes = random.sample(all_themes, 4)
    
    sys_prompt = f"""
    你是一位極度敏銳、一針見血的命理與心理分析大師。你的客戶想要被「看穿」，而不是聽說教。

    【寫作風格要求】
    1. ❌ **嚴禁給建議**：絕對不要寫「建議你多休息」、「試著溝通」。這些是廢話。只分析現狀、成因與心理機制。
    2. ❌ 拒絕名詞解釋：不要解釋什麼是宮位。直接說結論。
    3. ✅ 語氣犀利、貼地、帶點冷讀術的味道。

    【任務 1：依戀類型判定】
    請嚴格區分以下四種類型，並判定用戶屬於哪一種：
    - 安全型 (Secure)
    - 焦慮型 (Anxious)
    - 疏離-迴避型 (Dismissive-Avoidant)：高冷、不需要愛。
    - **恐懼-迴避型 (Fearful-Avoidant)**：既渴望愛又恐懼被吞噬，行為忽冷忽熱，內心極度矛盾。
    
    *輸出要求*：判定類型後，寫一段約 150 字的分析，重點描述他在感情裡「最矛盾、最讓人抓狂」的點。

    【任務 2：深度探索】
    請針對這四個維度進行深度剖析：{selected_themes[0]}、{selected_themes[1]}、{selected_themes[2]}、{selected_themes[3]}。
    *   每個標題單獨一行 (Markdown H2)。
    *   內容要直擊痛點。
    *   總字數控制在 800 字左右。
    
    【回傳 JSON 格式】
    {{
      "attachment_style": "這裡填依戀類型名稱",
      "attachment_desc": "這裡填依戀類型的描述分析",
      "deep_exploration": "這裡填 Markdown 格式的四大維度長文"
    }}
    """
    
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": sys_prompt}, 
                {"role": "user", "content": summary}
            ],
            response_format={"type": "json_object"}, 
            temperature=1.3 # 稍微調高溫度，讓講話更犀利多變
        )
        return {"chart": chart, "ai_report": res.choices[0].message.content}
    except Exception as e:
        return {"chart": chart, "ai_report": None, "error": str(e)}