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

    # --- D. 定義 AI 提示詞 ---
    # 1. 依戀模式分析提示詞（300字，心理學角度）
    attachment_prompt = """
    你是專業的心理學分析師，根據星盤數據分析用戶的依戀模式。

    【任務】
    根據用戶的星盤（特別是月亮、土星、金星的位置和相位），分析其依戀類型傾向。

    【要求 - 嚴格執行】
    1. 字數：約 300 字
    2. 風格：語言淺白，一針見血，不要廢話，不要解釋
    3. 禁止建議：絕對不要寫「建議你...」、「你可以試著...」、「你應該...」
    4. 禁止解釋：不要解釋「什麼是依戀類型」、「什麼是安全型依戀」，直接分析
    5. 必須判定：將用戶歸類為以下四者之一，並用粗體標示：
       - **安全型依戀 (Secure)**
       - **焦慮型依戀 (Anxious)**
       - **逃避型依戀 (Avoidant)**
       - **恐懼-逃避型依戀 (Fearful-Avoidant)**
    
    6. 分析角度：從心理學角度分析其在親密關係中的表現、情感模式、防禦機制
    7. 語言風格：
       - 淺白：用簡單直白的語言
       - 一針見血：直接說重點
       - 不要廢話：不要說「一般來說」、「通常」、「可能」
       - 直接描述：用「你在關係中...」、「你會...」、「你總是...」

    【輸出格式】
    直接輸出分析內容，不要標題，不要 Markdown 格式，純文字即可。
    """
    
    # 2. 星盤深度探索提示詞（1000字，多角度分析）
    deep_analysis_prompt = """
    你是現代星盤解說師，風格：語言淺白，一針見血，不要廢話，不需要建議。

    【任務】
    根據用戶星盤，進行 1000 字左右的深度分析。

    【格式要求】
    1. 小標題格式：使用【標題】格式標記小標題（例如：【內在靈魂】），這樣前端可以識別並顯示為黃色
    2. 每個小標題必須獨立一行
    3. 小標題後空一行再寫內容
    4. 不要使用其他 Markdown 符號（不要用 ##、**、* 等符號）

    【內容要求 - 極重要，嚴格執行】
    1. **禁止建議**：絕對不要寫「建議你...」、「你可以試著...」、「你應該...」
    2. **禁止名詞解釋**（極重要）：
       - 絕對不要說「第X宮代表...」、「XX宮是...」、「XX星座代表...」
       - 絕對不要說「落入XX座的能量影響你如何...」
       - 絕對不要解釋「什麼是二宮」、「什麼是金星」、「什麼是上升星座」
       - 直接說結論，直接描述用戶的實際表現
    3. **宮位分析規則（極重要）**：
       - 絕對禁止：不要說「第二宮代表金錢和價值觀」、「第五宮代表創意和戀愛」、「第12宮代表...」
       - 必須直接描述：直接說「你在金錢上...」、「你在戀愛中...」、「你在工作中...」、「你在隱藏的情感上...」
       - 實際模樣：描述用戶在該宮位的實際表現、行為模式、真實狀態
       - 範例：
         (X) 錯誤：「第12宮 天秤座。落入天秤座的能量影響你如何處理隱藏的情感...」
         (O) 正確：「你在隱藏的情感上：你習慣...，你會...，你總是...」
    4. **多角度分析**：
       - 每個小標題從不同角度出發
       - 可以是：內在靈魂、處事風格、愛情與慾望、人際博弈、金錢觀、工作模式、情感盲點、防禦機制、真實模樣等
       - 每次分析的角度要不同，全面描繪這個人
    5. **語言風格（極重要）**：
       - 淺白：用簡單直白的語言，不要用複雜的詞彙
       - 一針見血：直接說重點，不要繞彎子
       - 不要廢話：不要說「一般來說」、「通常」、「可能」這種不確定的話
       - 像在描述一個真實的人：用「你...」、「你會...」、「你總是...」這種直接描述
       - 不要用「這代表...」、「這意味著...」這種解釋性語言

    【範例格式】
    【內在靈魂】

    你外表看似...，其實內心...。你的月亮...，這讓你在...時會...。

    【處事風格】

    你在工作中...，你習慣...，你總是...。

    【輸出】
    直接輸出分析內容，開頭不要有標題，直接從第一個小標題開始。小標題使用【標題】格式。
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
        # 1. 生成依戀模式分析（300字，心理學角度）
        attachment_res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": attachment_prompt}, 
                {"role": "user", "content": summary}
            ],
            temperature=1.0,
            max_tokens=500
        )
        attachment_analysis = attachment_res.choices[0].message.content
        
        # 2. 生成星盤深度探索（1000字，多角度分析）
        deep_res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": deep_analysis_prompt}, 
                {"role": "user", "content": summary}
            ],
            temperature=1.3,
            max_tokens=2000
        )
        deep_analysis = deep_res.choices[0].message.content
        
        # 返回前最後一次驗證數據結構 - 確保五行能量數據正確
        if 'chinese' not in chart:
            chart['chinese'] = {}
        if 'five_elements' not in chart['chinese'] or not isinstance(chart['chinese']['five_elements'], dict):
            chart['chinese']['five_elements'] = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
        else:
            # 確保所有中文鍵都存在且為數字
            required_keys = ["金", "木", "水", "火", "土"]
            for key in required_keys:
                if key not in chart['chinese']['five_elements']:
                    chart['chinese']['five_elements'][key] = 0
                # 確保值是數字
                if not isinstance(chart['chinese']['five_elements'][key], (int, float)):
                    chart['chinese']['five_elements'][key] = 0
        
        # 返回前最後一次驗證數據結構
        final_response = {
            "chart": chart, 
            "attachment_analysis": attachment_analysis,  # 依戀模式分析（300字）
            "deep_analysis": deep_analysis  # 星盤深度探索（1000字）
        }
        print(f"[DEBUG] 最終返回的 chart.chinese.five_elements: {final_response['chart'].get('chinese', {}).get('five_elements', 'NOT FOUND')}")
        print(f"[DEBUG] 最終返回的完整 chart.chinese: {final_response['chart'].get('chinese', {})}")
        return final_response
    except Exception as e:
        # 即使 AI 調用失敗，也要確保返回正確的 chart 數據
        print(f"[DEBUG] AI 調用失敗，但返回 chart: {chart.get('chinese', {}).get('five_elements', 'NOT FOUND')}")
        import traceback
        return {
            "chart": chart, 
            "attachment_analysis": None, 
            "deep_analysis": None, 
            "error": str(e),
            "traceback": traceback.format_exc()
        }