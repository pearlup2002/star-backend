from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from lunar_python import Solar

def calculate_positions(year, month, day, hour=12, minute=0, lat=22.3, lon=114.2, is_time_unknown=False):
    # --- 1. 西方占星 (使用 Flatlib/Swiss Ephemeris) ---
    
    # 處理時區：Flatlib 需要 UTC 時間字串或帶時區的字串
    # 這裡我們簡單處理：假設輸入是 +08:00 (可根據需要調整)
    date_str = f"{year:04d}/{month:02d}/{day:02d}"
    time_str = f"{hour:02d}:{minute:02d}"
    
    # 建立時間物件 (假設 +08:00)
    date = Datetime(date_str, time_str, '+08:00')
    pos = GeoPos(lat, lon)
    
    # 建立星盤 (Chart)
    # 如果知道時間，使用 Placidus 宮位制 (專業標準)
    # 如果不知道時間，這裡先算出來，後面再隱藏敏感數據
    chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS)

    # 星座中英對照表 (Flatlib 回傳的是 3字母縮寫)
    sign_map = {
        'Ari': '白羊座', 'Tau': '金牛座', 'Gem': '雙子座', 'Can': '巨蟹座',
        'Leo': '獅子座', 'Vir': '處女座', 'Lib': '天秤座', 'Sco': '天蠍座',
        'Sag': '射手座', 'Cap': '摩羯座', 'Aqu': '水瓶座', 'Pis': '雙魚座'
    }
    
    # 元素對照表
    element_map = {
        'Fire': ['白羊座', '獅子座', '射手座'],
        'Earth': ['金牛座', '處女座', '摩羯座'],
        'Air': ['雙子座', '天秤座', '水瓶座'],
        'Water': ['巨蟹座', '天蠍座', '雙魚座']
    }
    
    # 反向查找元素的 helper
    def get_element(sign_name):
        for elem, signs in element_map.items():
            if sign_name in signs:
                return elem
        return "Unknown"

    # 需要計算的星體列表
    planets_list = [
        const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
        const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
    ]

    western_results = {}
    western_elements_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    sign_scores = {} # 權重統計
    
    # 權重設定
    planet_weights = {
        const.SUN: 30, const.MOON: 30, 
        const.MERCURY: 15, const.VENUS: 15, const.MARS: 15,
        const.JUPITER: 10, const.SATURN: 10, 
        const.URANUS: 5, const.NEPTUNE: 5, const.PLUTO: 5
    }

    # 1. 遍歷十大行星
    for p_id in planets_list:
        obj = chart.get(p_id)
        sign_code = obj.sign
        sign_name = sign_map.get(sign_code)
        exact_degree = obj.lon # 黃道經度 0-360
        
        # 統計元素
        elem = get_element(sign_name)
        if elem in western_elements_count:
            western_elements_count[elem] += 1
            
        # 統計權重
        weight = planet_weights.get(p_id, 5)
        sign_scores[sign_name] = sign_scores.get(sign_name, 0) + weight
        
        western_results[p_id.lower()] = {
            "sign": sign_name,
            "element": elem,
            "deg": round(exact_degree % 30, 2) # 顯示落在該星座的第幾度
        }

    # 2. 計算上升星座 (Ascendant) & 宮位
    rising_sign = "未知"
    houses_data = []
    
    if not is_time_unknown:
        # 獲取上升點
        asc = chart.get(const.ASC)
        rising_sign = sign_map.get(asc.sign)
        
        # 上升星座加權 (重要性等同日月)
        sign_scores[rising_sign] = sign_scores.get(rising_sign, 0) + 20
        
        # 獲取 12 宮位 (Placidus)
        # Flatlib 的 houses 是從 House1 到 House12
        for i in range(1, 13):
            house = chart.get(getattr(const, f'HOUSE{i}'))
            h_sign = sign_map.get(house.sign)
            houses_data.append({
                "house": i,
                "sign": h_sign
            })

    # 3. 計算星座比例 (Distribution)
    total_score = sum(sign_scores.values())
    distribution = []
    if total_score > 0:
        for sign, score in sign_scores.items():
            percent = (score / total_score) * 100
            distribution.append({"sign": sign, "percent": round(percent, 1)})
        distribution.sort(key=lambda x: x['percent'], reverse=True)

    # --- 2. 中式八字與五行 (Lunar Python) ---
    # 注意：這裡依然使用 Lunar Python，這是目前 Python 算八字最準的庫
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    
    bazi_text = [
        lunar.getYearInGanZhi(), lunar.getMonthInGanZhi(),
        lunar.getDayInGanZhi(), lunar.getTimeInGanZhi()
    ]
    
    # 五行統計
    wuxing_count = {"Metal": 0, "Wood": 0, "Water": 0, "Fire": 0, "Earth": 0}
    wuxing_map = {"金": "Metal", "木": "Wood", "水": "Water", "火": "Fire", "土": "Earth"}
    bazi_wuxing = lunar.getBaZiWuXing() # ['金', '土'...]
    
    # 未知時間處理：不計入時柱 (最後兩個字)
    limit = 6 if is_time_unknown else 8
    for i in range(limit):
        wx = bazi_wuxing[i]
        en_wx = wuxing_map.get(wx)
        if en_wx: wuxing_count[en_wx] += 1
        
    day_master_gan = bazi_text[2][0] # 日干
    # 簡易日主五行對照
    gan_wuxing = {
        "甲": "Wood", "乙": "Wood", "丙": "Fire", "丁": "Fire", "戊": "Earth",
        "己": "Earth", "庚": "Metal", "辛": "Metal", "壬": "Water", "癸": "Water"
    }
    self_element = gan_wuxing.get(day_master_gan, "Unknown")

    return {
        "western": {
            "planets": western_results,
            "elements": western_elements_count,
            "rising": rising_sign,
            "distribution": distribution,
            "houses": houses_data # 新增：準確的宮位列表
        },
        "chinese": {
            "bazi_text": bazi_text,
            "self_element": self_element,
            "five_elements": wuxing_count
        }
    }