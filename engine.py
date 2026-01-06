from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from lunar_python import Solar

def calculate_positions(year, month, day, hour=12, minute=0, lat=22.3, lon=114.2, is_time_unknown=False):
    # 1. 建立時間地點
    date_str = f"{year:04d}/{month:02d}/{day:02d}"
    time_str = f"{hour:02d}:{minute:02d}"
    date = Datetime(date_str, time_str, '+08:00')
    pos = GeoPos(lat, lon)
    
    # 2. 建立星盤
    chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS)

    # 【核心修復】純數學星座列表 (0=白羊, 1=金牛...)
    ZODIAC_NAMES = [
        "白羊座", "金牛座", "雙子座", "巨蟹座", 
        "獅子座", "處女座", "天秤座", "天蠍座", 
        "射手座", "摩羯座", "水瓶座", "雙魚座"
    ]
    
    # 元素對照 (直接用中文名查)
    sign_to_element = {
        '白羊座': 'Fire', '獅子座': 'Fire', '射手座': 'Fire',
        '金牛座': 'Earth', '處女座': 'Earth', '摩羯座': 'Earth',
        '雙子座': 'Air', '天秤座': 'Air', '水瓶座': 'Air',
        '巨蟹座': 'Water', '天蠍座': 'Water', '雙魚座': 'Water'
    }

    # 行星 ID 列表
    planets_list = [
        const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
        const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
    ]

    # 權重
    planet_weights = {
        const.SUN: 30, const.MOON: 30, 
        const.MERCURY: 15, const.VENUS: 15, const.MARS: 15,
        const.JUPITER: 10, const.SATURN: 10, 
        const.URANUS: 5, const.NEPTUNE: 5, const.PLUTO: 5
    }

    western_results = {}
    western_elements_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    sign_scores = {}
    
    # 3. 計算十大行星 (數學硬算)
    for p_id in planets_list:
        try:
            obj = chart.get(p_id)
            exact_degree = obj.lon # 0~360 的絕對度數
            
            # 【關鍵修復】直接用度數算星座，不查代號
            sign_index = int(exact_degree / 30) % 12
            sign_name = ZODIAC_NAMES[sign_index]
            degree_in_sign = exact_degree % 30
            
            # 統計元素
            elem = sign_to_element.get(sign_name, "Unknown")
            if elem in western_elements_count:
                western_elements_count[elem] += 1
                
            # 統計權重
            weight = planet_weights.get(p_id, 5)
            sign_scores[sign_name] = sign_scores.get(sign_name, 0) + weight
            
            western_results[p_id.lower()] = {
                "sign": sign_name,
                "element": elem,
                "deg": round(degree_in_sign, 2)
            }
        except Exception as e:
            print(f"Error calculating {p_id}: {e}")
            continue

    # 4. 計算上升與宮位
    rising_sign = "未知"
    houses_data = []
    
    if not is_time_unknown:
        try:
            # 上升點
            asc = chart.get(const.ASC)
            asc_idx = int(asc.lon / 30) % 12
            rising_sign = ZODIAC_NAMES[asc_idx]
            
            # 上升加權
            sign_scores[rising_sign] = sign_scores.get(rising_sign, 0) + 20
            
            # 12 宮位
            for i in range(1, 13):
                house = chart.get(getattr(const, f'HOUSE{i}'))
                h_idx = int(house.lon / 30) % 12
                h_sign = ZODIAC_NAMES[h_idx]
                
                houses_data.append({
                    "house": i,
                    "sign": h_sign
                })
        except Exception as e:
            print(f"Error calculating Houses: {e}")

    # 計算星座比例
    total_score = sum(sign_scores.values())
    distribution = []
    if total_score > 0:
        for sign, score in sign_scores.items():
            percent = (score / total_score) * 100
            distribution.append({"sign": sign, "percent": round(percent, 1)})
        distribution.sort(key=lambda x: x['percent'], reverse=True)

    # 5. 中式八字 (加強版防錯)
    try:
        solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
        lunar = solar.getLunar()
        
        bazi_text = [
            lunar.getYearInGanZhi(), lunar.getMonthInGanZhi(),
            lunar.getDayInGanZhi(), lunar.getTimeInGanZhi()
        ]
        
        wuxing_count = {"Metal": 0, "Wood": 0, "Water": 0, "Fire": 0, "Earth": 0}
        wuxing_map = {"金": "Metal", "木": "Wood", "水": "Water", "火": "Fire", "土": "Earth"}
        bazi_wuxing = lunar.getBaZiWuXing()
        
        limit = 6 if is_time_unknown else 8
        for i in range(limit):
            # 確保索引不越界
            if i < len(bazi_wuxing):
                wx = bazi_wuxing[i]
                en_wx = wuxing_map.get(wx)
                if en_wx: wuxing_count[en_wx] += 1
            
        day_master_gan = bazi_text[2][0] if len(bazi_text[2]) > 0 else "甲"
        gan_wuxing = {
            "甲": "Wood", "乙": "Wood", "丙": "Fire", "丁": "Fire", "戊": "Earth",
            "己": "Earth", "庚": "Metal", "辛": "Metal", "壬": "Water", "癸": "Water"
        }
        self_element = gan_wuxing.get(day_master_gan, "Unknown")
        
    except Exception as e:
        print(f"BaZi Error: {e}")
        bazi_text = ["", "", "", ""]
        self_element = "未知"

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