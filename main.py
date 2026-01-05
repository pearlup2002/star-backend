"""
FastAPI server for Star Mirror Astrology Backend.
"""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
from engine import calculate_positions

app = FastAPI(title="Star Mirror Backend API")


class CalculationRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: Optional[int] = None
    minute: Optional[int] = None
    lat: float
    lon: float


@app.get("/")
async def root():
    """Root endpoint to check if the server is running."""
    return {"status": "Star Mirror Backend is running"}


@app.post("/calculate")
async def calculate(request: CalculationRequest):
    """
    Calculate planetary positions and house cusps.
    
    Request body should contain:
    - year: int
    - month: int
    - day: int
    - hour: int (optional, defaults to 12:00 PM if not provided)
    - minute: int (optional, defaults to 0)
    - lat: float (latitude)
    - lon: float (longitude)
    """
    try:
        result = calculate_positions(
            year=request.year,
            month=request.month,
            day=request.day,
            hour=request.hour,
            minute=request.minute,
            lat=request.lat,
            lon=request.lon
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@app.post("/analyze")
async def analyze(request: CalculationRequest):
    """
    Calculate planetary positions and generate a 1000-word deep analysis using DeepSeek AI.
    
    Request body should contain:
    - year: int
    - month: int
    - day: int
    - hour: int (optional, defaults to 12:00 PM if not provided)
    - minute: int (optional, defaults to 0)
    - lat: float (latitude)
    - lon: float (longitude)
    """
    try:
        # 1. Calculate the star chart
        chart_data = calculate_positions(
            year=request.year,
            month=request.month,
            day=request.day,
            hour=request.hour,
            minute=request.minute,
            lat=request.lat,
            lon=request.lon
        )
        
        # 2. Construct the prompt
        # Map planet names to Chinese
        planet_names_cn = {
            'sun': '太陽',
            'moon': '月亮',
            'mercury': '水星',
            'venus': '金星',
            'mars': '火星',
            'jupiter': '木星',
            'saturn': '土星',
            'uranus': '天王星',
            'neptune': '海王星',
            'pluto': '冥王星'
        }
        
        # Map zodiac signs to Chinese
        zodiac_signs_cn = {
            'Aries': '白羊座',
            'Taurus': '金牛座',
            'Gemini': '雙子座',
            'Cancer': '巨蟹座',
            'Leo': '獅子座',
            'Virgo': '處女座',
            'Libra': '天秤座',
            'Scorpio': '天蠍座',
            'Sagittarius': '射手座',
            'Capricorn': '摩羯座',
            'Aquarius': '水瓶座',
            'Pisces': '雙魚座'
        }
        
        # Build chart data string
        chart_parts = []
        for planet_key, planet_cn in planet_names_cn.items():
            if planet_key in chart_data:
                planet_data = chart_data[planet_key]
                sign_en = planet_data.get('sign', '')
                sign_cn = zodiac_signs_cn.get(sign_en, sign_en)
                deg = planet_data.get('deg', 0)
                chart_parts.append(f"{planet_cn}={sign_cn} {deg}度")
        
        chart_string = "，".join(chart_parts)
        
        # Construct the full prompt
        prompt_content = f"用戶的星盤數據如下：{chart_string}。請為他撰寫一份 1000 字的深度分析報告。包含：性格盲點、情感模式、事業潛力、靈魂使命。"
        
        # 3. Call DeepSeek API
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500, 
                detail="DEEPSEEK_API_KEY environment variable is not set"
            )
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "你是一位精通心理占星術的大師，擅長用溫暖、療癒且一針見血的語氣分析星盤。"
                },
                {
                    "role": "user",
                    "content": prompt_content
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        analysis_text = response.choices[0].message.content
        
        # 4. Return chart data and analysis
        return {
            "chart": chart_data,
            "analysis": analysis_text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

