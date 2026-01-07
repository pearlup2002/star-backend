from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from lunar_python import Solar
import datetime

def calculate_positions(year, month, day, hour=12, minute=0, lat=22.3, lon=114.2, is_time_unknown=False):
    # --- 0. 真太陽時校正 ---
    if not is_time_unknown:
        longitude_offset_minutes = (lon - 120.0) * 4.0
        original_dt = datetime.datetime(year, month, day, hour, minute)
        solar_dt = original_dt + datetime.timedelta(minutes=longitude_offset_minutes)
        bazi_year, bazi_month, bazi_day = solar_dt.year, solar_dt.month, solar_dt.day
        bazi_hour, bazi_minute = solar_dt.hour, solar_dt.minute
    else:
        bazi_year, bazi_month, bazi_day = year, month, day
        bazi_hour, bazi_minute = 12, 0

    # --- 1. 西方占星 (保留原樣) ---
    date_str = f"{year:04d}/{month:02d}/{day:02d}"
    time_str = f"{hour:02d}:{minute:02d}"
    date = Datetime(date_str, time_str, '+08:00')
    pos = GeoPos(lat, lon)
    chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS)

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
            
            western_results[p_id.lower()] = {"sign": sign_name, "element": elem, "deg": round(exact_degree % 30, 2)}
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

    # --- 3. 中式八字 (終極修復版) ---
    # 初始化
    bazi_text = ["", "", "", ""]
    self_element = "未知"
    wuxing_count = {"Metal": 0, "Wood": 0, "Water": 0, "Fire": 0, "Earth": 0}

    try:
        print(f"DEBUG: Calculating BaZi for {bazi_year}-{bazi_month}-{bazi_day} {bazi_hour}:{bazi_minute}")
        
        solar = Solar.fromYmdHms(bazi_year, bazi_month, bazi_day, bazi_hour, bazi_minute, 0)
        lunar = solar.getLunar()
        
        bazi_text = [
            lunar.getYearInGanZhi(), lunar.getMonthInGanZhi(),
            lunar.getDayInGanZhi(), lunar.getTimeInGanZhi()
        ]
        
        # 獲取五行列表
        bazi_wuxing_list = lunar.getBaZiWuXing()
        # print(f"DEBUG: Raw WuXing List: {bazi_wuxing_list}") # 解除註解可在 Render Log 看到原始數據
        
        limit = 6 if is_time_unknown else 8
        
        for i in range(limit):
            if i < len(bazi_wuxing_list):
                # 嘗試多種方法獲取文字
                item = bazi_wuxing_list[i]
                char = ""
                
                # 方法1: 如果是字串
                if isinstance(item, str):
                    char = item
                # 方法2: 如果是物件，嘗試 .getName()
                elif hasattr(item, 'getName'):
                    char = item.getName()
                # 方法3: 強制轉字串
                else:
                    char = str(item)
                
                # 判斷五行
                if '金' in char: wuxing_count['Metal'] += 1
                elif '木' in char: wuxing_count['Wood'] += 1
                elif '水' in char: wuxing_count['Water'] += 1
                elif '火' in char: wuxing_count['Fire'] += 1
                elif '土' in char: wuxing_count['Earth'] += 1
        
        # 日主
        day_master_gan = bazi_text[2][0] if len(bazi_text[2]) > 0 else "甲"
        gan_wuxing = {"甲": "Wood", "乙": "Wood", "丙": "Fire", "丁": "Fire", "戊": "Earth", "己": "Earth", "庚": "Metal", "辛": "Metal", "壬": "Water", "癸": "Water"}
        self_element = gan_wuxing.get(day_master_gan, "未知")
        
    except Exception as e:
        # 這是關鍵：如果出錯，會在 Render Log 看到
        print(f"CRITICAL BAZI ERROR: {e}")
        import traceback
        traceback.print_exc()

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
            "five_elements": wuxing_count
        }
    }