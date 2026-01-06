from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from lunar_python import Solar

def calculate_positions(year, month, day, hour=12, minute=0, lat=22.3, lon=114.2, is_time_unknown=False):
    # 1. 建立星盤
    date_str = f"{year:04d}/{month:02d}/{day:02d}"
    time_str = f"{hour:02d}:{minute:02d}"
    date = Datetime(date_str, time_str, '+08:00')
    pos = GeoPos(lat, lon)
    chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS)

    # 基礎對照
    ZODIAC_NAMES = ["白羊座", "金牛座", "雙子座", "巨蟹座", "獅子座", "處女座", "天秤座", "天蠍座", "射手座", "摩羯座", "水瓶座", "雙魚座"]
    sign_to_element = {
        '白羊座': 'Fire', '獅子座': 'Fire', '射手座': 'Fire',
        '金牛座': 'Earth', '處女座': 'Earth', '摩羯座': 'Earth',
        '雙子座': 'Air', '天秤座': 'Air', '水瓶座': 'Air',
        '巨蟹座': 'Water', '天蠍座': 'Water', '雙魚座': 'Water'
    }

    # 【權重調整】讓上升星座和命主星權重更高，符合真實體感
    planet_weights = {
        'Sun': 25, 'Moon': 25, 
        'Mercury': 10, 'Venus': 10, 'Mars': 15, # 火星加權(因可能為命主星)
        'Jupiter': 8, 'Saturn': 8, 
        'Uranus': 5, 'Neptune': 5, 'Pluto': 5
    }
    
    planets_list = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    western_elements = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    sign_scores = {}

    # 計算行星
    western_results = {}
    for p_id in planets_list:
        try:
            obj = chart.get(p_id)
            idx = int(obj.lon / 30) % 12
            sign = ZODIAC_NAMES[idx]
            
            # 統計元素
            elem = sign_to_element.get(sign)
            if elem: western_elements[elem] += 1
            
            # 統計分數
            w = planet_weights.get(p_id, 5)
            sign_scores[sign] = sign_scores.get(sign, 0) + w
            
            western_results[p_id.lower()] = {"sign": sign, "element": elem, "deg": round(obj.lon % 30, 2)}
        except: continue

    # 計算上升與宮位
    rising_sign = "未知"
    houses_data = []
    if not is_time_unknown:
        try:
            asc = chart.get(const.ASC)
            asc_idx = int(asc.lon / 30) % 12
            rising_sign = ZODIAC_NAMES[asc_idx]
            
            # 【關鍵】上升星座權重由 20 提升至 30 (與日月同重，甚至更高)
            # 這會讓天蠍座(上升)的分數超過金牛座(太陽)
            sign_scores[rising_sign] = sign_scores.get(rising_sign, 0) + 30
            
            for i in range(1, 13):
                h = chart.get(getattr(const, f'HOUSE{i}'))
                h_idx = int(h.lon / 30) % 12
                houses_data.append({"house": i, "sign": ZODIAC_NAMES[h_idx]})
        except: pass

    # 排序十大星座
    total_score = sum(sign_scores.values())
    distribution = []
    if total_score > 0:
        for s, score in sign_scores.items():
            pct = (score / total_score) * 100
            distribution.append({"sign": s, "percent": round(pct, 1)})
        distribution.sort(key=lambda x: x['percent'], reverse=True)

    # --- 八字修復 ---
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    bazi = lunar.getBaZi() # ['甲', '子', '乙', '丑'...] (共8字)
    
    # 建立八字文字
    bazi_text = [
        lunar.getYearInGanZhi(), lunar.getMonthInGanZhi(),
        lunar.getDayInGanZhi(), lunar.getTimeInGanZhi()
    ]
    
    # 五行統計 (修復 0% 問題)
    wuxing_cnt = {"Metal": 0, "Wood": 0, "Water": 0, "Fire": 0, "Earth": 0}
    # 這裡必須包含所有可能的繁體字
    wx_map = {
        "金": "Metal", "木": "Wood", "水": "Water", "火": "Fire", "土": "Earth"
    }
    
    # 使用 lunar 自帶的五行轉換
    limit = 6 if is_time_unknown else 8
    # getBaZiWuXing() 回傳的是 ['木', '水'...]
    bazi_wx_list = lunar.getBaZiWuXing() 
    
    for i in range(limit):
        if i < len(bazi_wx_list):
            char_wx = bazi_wx_list[i] # 這是中文 '金'
            en_key = wx_map.get(char_wx)
            if en_key: wuxing_cnt[en_key] += 1

    # 日主 (日干)
    day_gan = bazi_text[2][0] # 取日柱第一個字
    gan_map = {"甲":"Wood", "乙":"Wood", "丙":"Fire", "丁":"Fire", "戊":"Earth", "己":"Earth", "庚":"Metal", "辛":"Metal", "壬":"Water", "癸":"Water"}
    self_elem = gan_map.get(day_gan, "未知")

    return {
        "western": {"planets": western_results, "elements": western_elements, "rising": rising_sign, "distribution": distribution, "houses": houses_data},
        "chinese": {"bazi_text": bazi_text, "self_element": self_elem, "five_elements": wuxing_cnt}
    }