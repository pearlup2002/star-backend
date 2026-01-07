# 檔案名稱: bazi_engine.py
from lunar_python import Solar

def get_bazi_analysis(year, month, day, hour, minute):
    """
    輸入公曆日期，回傳五行能量百分比與八字文字
    """
    # 1. 初始化：將公曆轉為農曆八字物件
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    ba_zi = lunar.getEightChar()

    # 2. 獲取四柱（年、月、日、時）的天干與地支，共 8 個字
    # 這些物件都有 .getWuXing() 方法，會回傳 "金", "木", "水", "火", "土"
    chars = [
        ba_zi.getYearGan(), ba_zi.getYearZhi(),   # 年柱
        ba_zi.getMonthGan(), ba_zi.getMonthZhi(), # 月柱
        ba_zi.getDayGan(), ba_zi.getDayZhi(),     # 日柱
        ba_zi.getTimeGan(), ba_zi.getTimeZhi()    # 時柱
    ]

    # 3. 開始統計五行數量
    counts = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
    
    for char in chars:
        wx = char.getWuXing() # 獲取五行屬性
        if wx in counts:
            counts[wx] += 1

    # 4. 計算百分比
    total = sum(counts.values()) # 應該總是 8
    percentages = {}
    
    for k, v in counts.items():
        if total > 0:
            # 計算百分比並取整數
            percentages[k] = round((v / total) * 100)
        else:
            percentages[k] = 0

    # 5. 回傳資料結構
    return {
        "percentages": percentages, # 給前端畫能量條用
        "bazi_text": f"{ba_zi.getYearGan().getName()}{ba_zi.getYearZhi().getName()}年 "
                     f"{ba_zi.getMonthGan().getName()}{ba_zi.getMonthZhi().getName()}月 "
                     f"{ba_zi.getDayGan().getName()}{ba_zi.getDayZhi().getName()}日 "
                     f"{ba_zi.getTimeGan().getName()}{ba_zi.getTimeZhi().getName()}時" 
                     # 這行字可以給 AI 看，讓它分析八字
    }