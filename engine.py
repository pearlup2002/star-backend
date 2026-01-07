from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from lunar_python import Solar
import datetime

def calculate_positions(year, month, day, hour=12, minute=0, lat=22.3, lon=114.2, is_time_unknown=False):
    
    # ==========================================
    # 第一軌：準備「真太陽時」 (只給八字用！)
    # ==========================================
    if not is_time_unknown:
        # 北京時間基準經度 120度
        # 修正公式：(本地經度 - 120) * 4 分鐘
        longitude_offset_minutes = (lon - 120.0) * 4.0
        
        # 原始時間 (手錶時間)
        original_dt = datetime.datetime(year, month, day, hour, minute)
        
        # 算出真太陽時
        solar_dt = original_dt + datetime.timedelta(minutes=longitude_offset_minutes)
        
        # 這些變數專門給八字用，不要拿去餵給 Flatlib
        bazi_year = solar_dt.year
        bazi_month = solar_dt.month
        bazi_day = solar_dt.day
        bazi_hour = solar_dt.hour
        bazi_minute = solar_dt.minute
    else:
        # 時間未知，不進行修正
        bazi_year, bazi_month, bazi_day = year, month, day
        bazi_hour, bazi_minute = 12, 0

    # ==========================================
    # 第二軌：西方占星計算 (完全保留原樣，使用原始輸入)
    # ==========================================
    
    # 注意：這裡依然使用函數傳進來的 year, month, day... (手錶時間)
    # Flatlib 會根據 GeoPos(lat, lon) 自動處理觀測角度，不需要我們手動改時間
    date_str = f"{year:04d}/{month:02d}/{day:02d}"
    time_str = f"{hour:02d}:{minute:02d}"
    date = Datetime(date_str, time_str, '+08:00')
    pos = GeoPos(lat, lon)
    
    # 建立星盤
    chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS)

    # ... [中間的西方占星計算邏輯完全不用動] ...
    # 為了讓你方便複製，我還是把中間補上，以免你貼錯
    
    ZODIAC_NAMES = ["白羊座", "金牛座", "雙子座", "巨蟹座", "獅子座", "處女座", "天秤座", "天蠍座", "射手座", "摩羯座", "水瓶座", "雙魚座"]
    sign_to_element = {'白羊座': 'Fire', '獅子座': 'Fire', '射手座': 'Fire', '金牛座': 'Earth', '處女座': 'Earth', '摩羯座': 'Earth', '雙子座': 'Air', '天秤座': 'Air', '水瓶座': 'Air', '巨蟹座': 'Water', '天蠍座': 'Water', '雙魚座': 'Water'}
    planets_list = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    planet_weights = {'Sun': 30, 'Moon': 30, 'Mercury': 15, 'Venus': 15, 'Mars': 15, 'Jupiter': 10, 'Saturn': 10, 'Uranus': 5, 'Neptune': 5, 'Pluto': 5}

    western_results = {}
    western_elements_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    sign_scores = {}

    for p_id in planets_list:
        try:
            obj = chart.get(p_id)
            exact_degree = obj.lon
            sign_index = int(exact_degree / 30) % 12
            sign_name = ZODIAC_NAMES[sign_index]
            
            elem = sign_to_element.get(sign_name, "Unknown")
            if elem in western_elements_count: western_elements_count[elem] += 1
            
            weight = planet_weights.get(p_id, 5)
            sign_scores[sign_name] = sign_scores.get(sign_name, 0) + weight
            
            western_results[p_id.lower()] = {
                "sign": sign_name, "element": elem, "deg": round(exact_degree % 30, 2)
            }
        except: continue

    rising_sign = "未知"
    houses_data = []
    if not is_time_unknown:
        try:
            asc = chart.get(const.ASC)
            asc_idx = int(asc.lon / 30) % 12
            rising_sign = ZODIAC_NAMES[asc_idx]
            
            sign_scores[rising_sign] = sign_scores.get(rising_sign, 0) + 30
            
            for i in range(1, 13):
                h = chart.get(getattr(const, f'HOUSE{i}'))
                h_idx = int(h.lon / 30) % 12
                houses_data.append({"house": i, "sign": ZODIAC_NAMES[h_idx]})
        except: pass

    total_score = sum(sign_scores.values())
    distribution = []
    if total_score > 0:
        for s, score in sign_scores.items():
            pct = (score / total_score) * 100
            distribution.append({"sign": s, "percent": round(pct, 1)})
        distribution.sort(key=lambda x: x['percent'], reverse=True)

    # ==========================================
    # 第三軌：中式八字計算 (使用修正後的變數)
    # ==========================================
    try:
        # 使用修正後的時間
        solar = Solar.fromYmdHms(bazi_year, bazi_month, bazi_day, bazi_hour, bazi_minute, 0)
        lunar = solar.getLunar()
        
        # 獲取八字文字 (e.g. ['甲子', '乙丑'...])
        bazi_text = [
            lunar.getYearInGanZhi(), lunar.getMonthInGanZhi(),
            lunar.getDayInGanZhi(), lunar.getTimeInGanZhi()
        ]
        
        # 獲取八字五行列表 (e.g. ['木', '水', '木', '土'...])
        # getBaZiWuXing() 回傳的是簡體或繁體中文
        bazi_wuxing_list = lunar.getBaZiWuXing()
        
        # 初始化計數器 (英文 Key)
        wuxing_count = {"Metal": 0, "Wood": 0, "Water": 0, "Fire": 0, "Earth": 0}
        
        # 決定要算幾個字 (未知時間算前6個字，已知時間算8個字)
        limit = 6 if is_time_unknown else 8
        
        # 【暴力判斷法】 直接檢查字元，不查字典了
        for i in range(limit):
            if i < len(bazi_wuxing_list):
                char = str(bazi_wuxing_list[i]) # 確保是字串
                
                # 金 (包含繁簡體部首)
                if '金' in char or '钅' in char: 
                    wuxing_count['Metal'] += 1
                # 木
                elif '木' in char:
                    wuxing_count['Wood'] += 1
                # 水 (包含三點水)
                elif '水' in char or '氵' in char:
                    wuxing_count['Water'] += 1
                # 火 (包含四點火)
                elif '火' in char or '灬' in char:
                    wuxing_count['Fire'] += 1
                # 土
                elif '土' in char:
                    wuxing_count['Earth'] += 1
        
        # 日主計算
        day_master_gan = bazi_text[2][0] if len(bazi_text[2]) > 0 else "甲"
        # 簡易日主五行 (Hardcode)
        if day_master_gan in ['甲', '乙']: self_element = "Wood"
        elif day_master_gan in ['丙', '丁']: self_element = "Fire"
        elif day_master_gan in ['戊', '己']: self_element = "Earth"
        elif day_master_gan in ['庚', '辛']: self_element = "Metal"
        elif day_master_gan in ['壬', '癸']: self_element = "Water"
        else: self_element = "Unknown"
        
    except Exception as e:
        print(f"BaZi Error: {e}")
        # 發生錯誤時回傳空數據，避免 APP 崩潰
        bazi_text = ["", "", "", ""]
        self_element = "未知"
        wuxing_count = {"Metal": 0, "Wood": 0, "Water": 0, "Fire": 0, "Earth": 0}

    return {
        "western": {
            "planets": western_results,
            "elements": western_elements_count,
            "rising": rising_sign,
            "distribution": distribution,
            "houses": houses_data
        },
        "chinese": {
            "bazi_text": bazi_text,
            "self_element": self_element,
            "five_elements": wuxing_count  # 這裡是關鍵，一定要傳回這個字典
        }
    }