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
    
    # 2. 建立星盤 (使用 Placidus 宮位制)
    chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS)

    # 星座對照表
    sign_map = {
        'Ari': '白羊座', 'Tau': '金牛座', 'Gem': '雙子座', 'Can': '巨蟹座',
        'Leo': '獅子座', 'Vir': '處女座', 'Lib': '天秤座', 'Sco': '天蠍座',
        'Sag': '射手座', 'Cap': '摩羯座', 'Aqu': '水瓶座', 'Pis': '雙魚座'
    }
    
    # 元素對照表 (反查)
    # 這裡確保邏輯簡單：給星座名 -> 回傳元素
    sign_to_element = {
        '白羊座': 'Fire', '獅子座': 'Fire', '射手座': 'Fire',
        '金牛座': 'Earth', '處女座': 'Earth', '摩羯座': 'Earth',
        '雙子座': 'Air', '天秤座': 'Air', '水瓶座': 'Air',
        '巨蟹座': 'Water', '天蠍座': 'Water', '雙魚座': 'Water'
    }

    # 明確定義行星列表 (使用純字串 ID)
    planets_list = [
        'Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
        'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'
    ]

    # 權重設定 (使用純字串 Key，避免 KeyError)
    planet_weights = {
        'Sun': 30, 'Moon': 30, 
        'Mercury': 15, 'Venus': 15, 'Mars': 15,
        'Jupiter': 10, 'Saturn': 10, 
        'Uranus': 5, 'Neptune': 5, 'Pluto': 5
    }

    western_results = {}
    western_elements_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    sign_scores = {}
    
    # 3. 計算十大行星
    for p_id in planets_list:
        try:
            # 獲取星體物件
            obj = chart.get(p_id)
            sign_code = obj.sign
            sign_name = sign_map.get(sign_code, "Unknown")
            exact_degree = obj.lon 
            
            # 統計元素
            elem = sign_to_element.get(sign_name, "Unknown")
            if elem in western_elements_count:
                western_elements_count[elem] += 1
                
            # 統計權重 (使用 get 避免報錯，預設為 5)
            weight = planet_weights.get(p_id, 5)
            sign_scores[sign_name] = sign_scores.get(sign_name, 0) + weight
            
            western_results[p_id.lower()] = {
                "sign": sign_name,
                "element": elem,
                "deg": round(exact_degree % 30, 2)
            }
        except Exception as e:
            print(f"Error calculating {p_id}: {e}")
            continue

    # 4. 計算上升與宮位
    rising_sign = "未知"
    houses_data = []
    
    if not is_time_unknown:
        try:
            asc = chart.get(const.ASC)
            rising_sign = sign_map.get(asc.sign, "未知")
            
            # 上升星座加權
            sign_scores[rising_sign] = sign_scores.get(rising_sign, 0) + 20
            
            # 12 宮位
            for i in range(1, 13):
                house_id = getattr(const, f'HOUSE{i}')
                house = chart.get(house_id)
                h_sign = sign_map.get(house.sign, "未知")
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

    # 5. 中式八字
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
            wx = bazi_wuxing[i]
            en_wx = wuxing_map.get(wx)
            if en_wx: wuxing_count[en_wx] += 1
            
        day_master_gan = bazi_text[2][0]
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