from skyfield.api import load, Topos
from skyfield.framelib import ecliptic_frame
from lunar_python import Solar

def calculate_positions(year, month, day, hour=12, minute=0, lat=22.3, lon=114.2, is_time_unknown=False):
    # --- 1. 西方占星計算 ---
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
    
    # 用來統計元素的表
    element_map = {
        "白羊座": "Fire", "獅子座": "Fire", "射手座": "Fire",
        "金牛座": "Earth", "處女座": "Earth", "摩羯座": "Earth",
        "雙子座": "Air", "天秤座": "Air", "水瓶座": "Air",
        "巨蟹座": "Water", "天蠍座": "Water", "雙魚座": "Water"
    }

    western_results = {}
    western_elements_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    
    sun_sign_index = 0 # 暫存太陽星座索引，用來算上升

    for name, body in planet_map.items():
        astrometric = location.at(t).observe(body)
        _, lon_deg, _ = astrometric.frame_latlon(ecliptic_frame)
        lon_deg = lon_deg.degrees % 360
        sign_index = int(lon_deg / 30)
        sign_name = zodiac_map[sign_index]
        
        # 紀錄太陽星座索引
        if name == 'Sun':
            sun_sign_index = sign_index

        elem = element_map.get(sign_name, "Unknown")
        if elem in western_elements_count:
            western_elements_count[elem] += 1

        western_results[name.lower()] = {
            "sign": sign_name, "element": elem, "deg": round(lon_deg % 30, 2)
        }

    # --- 2. 計算上升星座 (Rising Sign) ---
    rising_sign = "未知"
    if not is_time_unknown:
        # 簡易算法：每 2 小時上升星座移動一個宮位
        # 假設 6:00 AM 上升星座 = 太陽星座
        # 偏移量 = (出生小時 - 6) / 2
        offset = (hour - 6) / 2
        # 上升星座索引 = (太陽索引 - offset) % 12
        # 注意：地球自轉是逆時針，但星盤是順時針，這裡用簡易近似值
        rising_index = int((sun_sign_index - offset)) % 12
        rising_sign = zodiac_map[rising_index]

    # --- 3. 中式八字與五行 ---
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    
    # 八字文字
    bazi_text = [
        lunar.getYearInGanZhi(), lunar.getMonthInGanZhi(),
        lunar.getDayInGanZhi(), lunar.getTimeInGanZhi()
    ]

    # 計算五行 (精準版)
    # 我們遍歷八字的每一個字，查它是什麼五行
    wuxing_count = {"Metal": 0, "Wood": 0, "Water": 0, "Fire": 0, "Earth": 0}
    
    # 簡易字典：天干地支對應五行
    gan_zhi_wuxing = {
        # 天干
        "甲": "Wood", "乙": "Wood", "丙": "Fire", "丁": "Fire",
        "戊": "Earth", "己": "Earth", "庚": "Metal", "辛": "Metal",
        "壬": "Water", "癸": "Water",
        # 地支
        "子": "Water", "丑": "Earth", "寅": "Wood", "卯": "Wood",
        "辰": "Earth", "巳": "Fire", "午": "Fire", "未": "Earth",
        "申": "Metal", "酉": "Metal", "戌": "Earth", "亥": "Water"
    }

    # 把八字字串拆開來統計 (例如 "癸亥" -> "癸", "亥")
    for pillar in bazi_text: # pillar 是 "癸亥"
        for char in pillar:
            element = gan_zhi_wuxing.get(char)
            if element in wuxing_count:
                wuxing_count[element] += 1
    
    # 日主 (日柱的天干)
    day_master_char = bazi_text[2][0] # 日柱的第一個字
    self_element = gan_zhi_wuxing.get(day_master_char, "Unknown")

    return {
        "western": {
            "planets": western_results,
            "elements": western_elements_count,
            "rising": rising_sign
        },
        "chinese": {
            "bazi_text": bazi_text,
            "self_element": self_element,
            "five_elements": wuxing_count
        }
    }