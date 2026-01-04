"""
FastAPI server for Star Mirror Astrology Backend.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

