from skyfield.api import load, Topos
from skyfield.framelib import ecliptic_frame
from lunar_python import Solar

def calculate_positions(year, month, day, hour=12, minute=0, lat=22.3, lon=114.2, is_time_unknown=False):
    # --- 1. 西方占星計算 (Western Astrology) ---
    ts = load.timescale()
    # 簡單時區處理 (假設 UTC+8)
    t = ts.utc(year, month, day, hour - 8, minute)
    eph = load('de421.bsp')
    
    earth = eph['earth']
    location = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
    
    # 行星對照表 (注意外行星用 barycenter)
    planet_map = {
        'Sun': eph['sun'],
        'Moon': eph['moon'],
        'Mercury': eph['mercury'],
        'Venus': eph['venus'],
        'Mars': eph['mars'],
        'Jupiter': eph['jupiter barycenter'],
        'Saturn': eph['saturn barycenter'],
        'Uranus': eph['uranus barycenter'],
        'Neptune': eph['neptune barycenter'],
        'Pluto': eph['pluto barycenter']
    }

    # 星座中英對照
    zodiac_map = [
        "白羊座", "金牛座", "雙子座", "巨蟹座", 
        "獅子座", "處女座", "天秤座", "天蠍座", 
        "射手座", "摩羯座", "水瓶座", "雙魚座"
    ]
    
    # 四大元素對照
    element_map = {
        "白羊座": "Fire", "獅子座": "Fire", "射手座": "Fire",
        "金牛座": "Earth", "處女座": "Earth", "摩羯座": "Earth",
        "雙子座": "Air", "天秤座": "Air", "水瓶座": "Air",
        "巨蟹座": "Water", "天蠍座": "Water", "雙魚座": "Water"
    }

    western_results = {}
    western_elements_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    
    # 計算行星落座
    for name, body in planet_map.items():
        astrometric = location.at(t).observe(body)
        _, lon_deg, _ = astrometric.frame_latlon(ecliptic_frame)
        
        lon_deg = lon_deg.degrees % 360
        sign_index = int(lon_deg / 30)
        sign_name = zodiac_map[sign_index]
        degree_in_sign = lon_deg % 30
        
        # 統計元素 (只統計主要行星，不含三王星可選，這裡全統計)
        elem = element_map.get(sign_name, "Unknown")
        if elem in western_elements_count:
            western_elements_count[elem] += 1

        western_results[name.lower()] = {
            "sign": sign_name,
            "element": elem,
            "deg": round(degree_in_sign, 2)
        }

    # 計算上升星座 (Rising Sign) - 簡易估算
    # 如果不知道時間，就不算上升
    rising_sign = "未知"
    if not is_time_unknown:
        # 這裡使用簡易算法，或者未來可加入更精確的 Sidereal Time 計算
        # 暫時回傳 "需精確算法" 或基於太陽星座推算 (此處僅為示例結構)
        rising_sign = "需實作精確算法" 

    # --- 2. 中式八字與五行 (Chinese BaZi & 5 Elements) ---
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    ba_zi = lunar.getBaZi() # 獲取八字列表 [天干, 地支, ...]
    
    # 獲取八字文字 (例如：癸亥)
    year_gz = lunar.getYearInGanZhi()
    month_gz = lunar.getMonthInGanZhi()
    day_gz = lunar.getDayInGanZhi()
    time_gz = lunar.getTimeInGanZhi()
    
    bazi_text = [year_gz, month_gz, day_gz, time_gz]

    # 計算五行數量 (金木水火土)
    # lunar_python 提供了 getWuXing() 方法
    wuxing_count = {"Metal": 0, "Wood": 0, "Water": 0, "Fire": 0, "Earth": 0}
    
    # 遍歷八字 (4柱 x 2字 = 8字)
    # 這裡我們需要把天干和地支都轉為五行
    gan_zhi_list = ba_zi # 這是八個字
    
    # 簡單映射 (lunar_python 的 WuXing 對象轉英文)
    # 由於庫的具體用法，我們這裡用簡單映射表來確保萬無一失
    wuxing_map = {
        "金": "Metal", "木": "Wood", "水": "Water", "火": "Fire", "土": "Earth"
    }
    
    # 獲取日主 (Day Master) - 日柱的天干
    day_gan = day_gz[0] # 取第一個字
    # 這裡需要一個簡單的天干五行表
    heavenly_stems = {
        "甲": "Wood", "乙": "Wood",
        "丙": "Fire", "丁": "Fire",
        "戊": "Earth", "己": "Earth",
        "庚": "Metal", "辛": "Metal",
        "壬": "Water", "癸": "Water"
    }
    self_element = heavenly_stems.get(day_gan, "Unknown")

    # 統計八字五行 (這裡使用 lunar 的 getBaZiWuXing 列表)
    bazi_wuxing = lunar.getBaZiWuXing() # 回傳如 ['水', '水', '木', ...]
    for wx in bazi_wuxing:
        en_wx = wuxing_map.get(wx, "Unknown")
        if en_wx in wuxing_count:
            wuxing_count[en_wx] += 1

    # --- 3. 整合回傳 ---
    return {
        "western": {
            "planets": western_results,
            "elements": western_elements_count,
            "rising": rising_sign
        },
        "chinese": {
            "bazi_text": bazi_text,
            "self_element": self_element, # 日主屬性 (如: Water)
            "five_elements": wuxing_count
        }
    }