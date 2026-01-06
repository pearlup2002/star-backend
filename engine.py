from skyfield.api import load, Topos
from skyfield.framelib import ecliptic_frame
from lunar_python import Solar

def calculate_positions(year, month, day, hour=12, minute=0, lat=22.3, lon=114.2, is_time_unknown=False):
    # --- 1. 西方占星 ---
    ts = load.timescale()
    t = ts.utc(year, month, day, hour - 8, minute)
    eph = load('de421.bsp')
    earth = eph['earth']
    location = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
    
    planet_map = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 'Mercury': eph['mercury'],
        'Venus': eph['venus'], 'Mars': eph['mars'], 'Jupiter': eph['jupiter barycenter'],
        'Saturn': eph['saturn barycenter'], 'Uranus': eph['uranus barycenter'],
        'Neptune': eph['neptune barycenter'], 'Pluto': eph['pluto barycenter']
    }

    zodiac_map = ["白羊座", "金牛座", "雙子座", "巨蟹座", "獅子座", "處女座", "天秤座", "天蠍座", "射手座", "摩羯座", "水瓶座", "雙魚座"]
    
    # 權重系統 (Weighted System) - 讓百分比出現小數點
    # 太陽月亮=30分, 個人行星=15分, 外行星=10分
    planet_weights = {
        'Sun': 30, 'Moon': 30, 
        'Mercury': 15, 'Venus': 15, 'Mars': 15,
        'Jupiter': 10, 'Saturn': 10, 'Uranus': 5, 'Neptune': 5, 'Pluto': 5
    }

    western_results = {}
    western_elements_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    sign_scores = {} # 記錄每個星座的得分

    sun_sign_index = 0

    for name, body in planet_map.items():
        astrometric = location.at(t).observe(body)
        _, lon_deg, _ = astrometric.frame_latlon(ecliptic_frame)
        lon_deg = lon_deg.degrees % 360
        sign_index = int(lon_deg / 30)
        sign_name = zodiac_map[sign_index]
        
        if name == 'Sun': sun_sign_index = sign_index

        # 統計元素
        elem_map = {
            "白羊座": "Fire", "獅子座": "Fire", "射手座": "Fire",
            "金牛座": "Earth", "處女座": "Earth", "摩羯座": "Earth",
            "雙子座": "Air", "天秤座": "Air", "水瓶座": "Air",
            "巨蟹座": "Water", "天蠍座": "Water", "雙魚座": "Water"
        }
        elem = elem_map.get(sign_name, "Unknown")
        if elem in western_elements_count:
            western_elements_count[elem] += 1

        # 統計星座權重 (解決 10% 20% 死板問題)
        weight = planet_weights.get(name, 5)
        sign_scores[sign_name] = sign_scores.get(sign_name, 0) + weight

        western_results[name.lower()] = {
            "sign": sign_name, "element": elem, "deg": round(lon_deg % 30, 2)
        }

    # --- 2. 計算上升星座 (嚴格處理未知時間) ---
    rising_sign = "未知" # 預設未知
    if is_time_unknown == False: # 只有在知道時間時才算
        offset = (hour - 6) / 2
        rising_index = int((sun_sign_index - offset)) % 12
        rising_sign = zodiac_map[rising_index]
        # 上升星座非常重要，加權 20分
        sign_scores[rising_sign] = sign_scores.get(rising_sign, 0) + 20

    # 轉換星座分數為百分比 (Total = 100%)
    total_score = sum(sign_scores.values())
    sign_distribution = []
    for sign, score in sign_scores.items():
        percent = (score / total_score) * 100
        sign_distribution.append({"sign": sign, "percent": round(percent, 1)}) # 保留一位小數
    
    # 排序：由大到小
    sign_distribution.sort(key=lambda x: x['percent'], reverse=True)

    # --- 3. 中式八字 ---
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    bazi_text = [lunar.getYearInGanZhi(), lunar.getMonthInGanZhi(), lunar.getDayInGanZhi(), lunar.getTimeInGanZhi()]
    
    # 計算五行
    wuxing_count = {"Metal": 0, "Wood": 0, "Water": 0, "Fire": 0, "Earth": 0}
    wuxing_map = {"金": "Metal", "木": "Wood", "水": "Water", "火": "Fire", "土": "Earth"}
    bazi_wuxing = lunar.getBaZiWuXing()
    
    # 如果時間未知，最後一柱(時柱)不計入統計，以免誤導
    range_limit = 6 if is_time_unknown else 8
    for i in range(range_limit): 
        wx = bazi_wuxing[i] if i < len(bazi_wuxing) else "無"
        en_wx = wuxing_map.get(wx)
        if en_wx: wuxing_count[en_wx] += 1

    day_master = bazi_text[2][0] # 日干
    
    return {
        "western": {
            "planets": western_results,
            "elements": western_elements_count,
            "rising": rising_sign,
            "distribution": sign_distribution # 新增的精準比例
        },
        "chinese": {
            "bazi_text": bazi_text,
            "self_element": day_master,
            "five_elements": wuxing_count
        }
    }