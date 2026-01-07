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
@app.get("/test-bazi")
def test_bazi(year: int = 2000, month: int = 1, day: int = 1, hour: int = 12, minute: int = 0):
    """測試端點：直接返回八字計算結果"""
    try:
        bazi_data = bazi_engine.get_bazi_analysis(year, month, day, hour, minute)
        return {
            "success": True,
            "bazi_data": bazi_data,
            "five_elements": bazi_data.get('percentages', {})
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.post("/analyze")
def analyze_chart(req: ChartRequest):
    # --- A. 計算西方星盤 ---
    chart = engine.calculate_positions(req.year, req.month, req.day, req.hour, req.minute, req.lat, req.lon, req.is_time_unknown)
    
    print(f"[DEBUG] engine 返回的 chart['chinese']: {chart.get('chinese')}")  # 調試日誌
    
    # --- B. 計算東方八字 (使用 bazi_engine 的準確計算) ---
    # 確保 chinese 結構存在
    if 'chinese' not in chart:
        chart['chinese'] = {}
    
    # 立即清理 engine 返回的英文格式數據，改用中文格式
    # engine 返回的是 {"Metal": 0, "Wood": 0, ...}，我們需要 {"金": 0, "木": 0, ...}
    default_five_elements = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
    # 強制覆蓋，不管 engine 返回什麼格式
    chart['chinese']['five_elements'] = default_five_elements.copy()  # 使用 copy() 避免引用問題
    bazi_text = "八字計算失敗"
    
    print(f"[DEBUG] 設置默認值後的 chart['chinese']['five_elements']: {chart['chinese']['five_elements']}")  # 調試日誌
    
    try:
        bazi_data = bazi_engine.get_bazi_analysis(req.year, req.month, req.day, req.hour, req.minute)
        print(f"[DEBUG] bazi_data: {bazi_data}")  # 調試日誌
        
        # 注入數據供前端使用 - 使用 bazi_engine 的準確計算結果
        if bazi_data and 'percentages' in bazi_data:
            chart['chinese']['five_elements'] = bazi_data['percentages']
            print(f"[DEBUG] 設置 five_elements: {chart['chinese']['five_elements']}")  # 調試日誌
        
        # 獲取文字供 AI 使用
        if bazi_data and 'bazi_text' in bazi_data:
            bazi_text = bazi_data['bazi_text']
    except Exception as e:
        import traceback
        error_msg = f"八字計算錯誤: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        # 保持默認值，確保前端能收到數據結構
    
    # 確保 five_elements 存在且格式正確
    if 'five_elements' not in chart['chinese']:
        chart['chinese']['five_elements'] = default_five_elements
    print(f"[DEBUG] 最終 chart['chinese']['five_elements']: {chart['chinese'].get('five_elements')}")  # 調試日誌

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
    3. **宮位分析規則（極重要）**：
       - **絕對禁止**：不要說「第二宮代表金錢和價值觀」、「第五宮代表創意和戀愛」這類解釋。
       - **必須直接描述**：直接說「你在金錢上...」、「你在戀愛中...」、「你在工作中...」。
       - **實際模樣**：描述用戶在該宮位的實際表現、行為模式、真實狀態。
       - 範例：
         (X) 錯誤：「你的第二宮在金牛座，第二宮代表金錢，金牛座重視物質...」
         (O) 正確：「你對金錢的態度是：你習慣...，你會...，你總是...」
    
    4. **四大維度**：請務必從以下四個角度進行分析，每個角度一段：
       - **內在靈魂 (The Soul)**：潛意識、安全感來源、恐懼。
       - **處事風格 (Execution)**：工作邏輯、決策模式、行動力。
       - **愛情與慾望 (Love & Desire)**：依戀模式、性吸引力、情感盲點。
       - **人際博弈 (Social Strategy)**：社交手段、防禦機制、給人的印象。

    5. **依戀類型判定**：
       根據星盤（尤其是月亮與土星相位），將用戶歸類為以下四者之一，並用粗體標示：
       - **安全型依戀 (Secure)**
       - **焦慮型依戀 (Anxious)**
       - **逃避型依戀 (Avoidant)**
       - **恐懼-逃避型依戀 (Fearful-Avoidant)**

    【語氣範例】
    (O) 正確：「你外表看似隨和，其實內心極度計較公平。這是因為你的月亮天秤在...」
    (X) 錯誤：「月亮代表內心，落在天秤座的人通常...」
    (X) 錯誤：「你的第七宮在天蠍座，第七宮代表伴侶關係...」
    (O) 正確：「你在伴侶關係中：你總是...，你會...，你習慣...」

    請以 Markdown 格式輸出，不要有 JSON 結構，直接進入文章標題與內容。
    """
    
    # --- E. 呼叫 DeepSeek AI ---
    # 最終檢查：確保 five_elements 存在且格式正確（中文）
    if 'chinese' not in chart:
        chart['chinese'] = {}
    
    # 強制確保 five_elements 是中文格式
    if 'five_elements' not in chart['chinese']:
        chart['chinese']['five_elements'] = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
    else:
        # 如果存在但格式不對（可能是英文格式），轉換或重新設置
        fe = chart['chinese']['five_elements']
        # 檢查是否是英文格式
        if 'Metal' in fe or 'Wood' in fe or 'Water' in fe or 'Fire' in fe or 'Earth' in fe:
            # 是英文格式，重新設置為中文格式
            chart['chinese']['five_elements'] = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
        # 確保所有中文鍵都存在
        required_keys = ["金", "木", "水", "火", "土"]
        for key in required_keys:
            if key not in chart['chinese']['five_elements']:
                chart['chinese']['five_elements'][key] = 0
    
    print(f"[DEBUG] 返回前的完整 chart 結構: {chart}")  # 調試日誌
    print(f"[DEBUG] 返回前的 chart['chinese']: {chart.get('chinese')}")  # 調試日誌
    print(f"[DEBUG] 返回前的 chart['chinese']['five_elements']: {chart['chinese'].get('five_elements')}")  # 調試日誌
    
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": sys_prompt}, 
                {"role": "user", "content": summary}
            ],
            temperature=1.3 
        )
        # 返回前最後一次驗證數據結構
        final_response = {"chart": chart, "ai_report": res.choices[0].message.content}
        print(f"[DEBUG] 最終返回的 chart.chinese.five_elements: {final_response['chart'].get('chinese', {}).get('five_elements', 'NOT FOUND')}")
        return final_response
    except Exception as e:
        # 即使 AI 調用失敗，也要確保返回正確的 chart 數據
        print(f"[DEBUG] AI 調用失敗，但返回 chart: {chart.get('chinese', {}).get('five_elements', 'NOT FOUND')}")
        return {"chart": chart, "ai_report": None, "error": str(e)}