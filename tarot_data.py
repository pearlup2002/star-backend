# 78 張韋特塔羅牌定義
# 為了避免檔案太長，這裡先用代碼自動生成結構，你可以之後再慢慢補全中文含義
TAROT_DECK = []

# 1. 大阿爾克那 (Major Arcana)
majors = [
    "愚者", "魔術師", "女祭司", "皇后", "皇帝", "教皇", "戀人", "戰車",
    "力量", "隱士", "命運之輪", "正義", "吊人", "死神", "節制", "惡魔",
    "高塔", "星星", "月亮", "太陽", "審判", "世界"
]
majors_en = [
    "The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor", 
    "The Hierophant", "The Lovers", "The Chariot", "Strength", "The Hermit", 
    "Wheel of Fortune", "Justice", "The Hanged Man", "Death", "Temperance", 
    "The Devil", "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World"
]

for i in range(22):
    TAROT_DECK.append({
        "id": i,
        "name_en": majors_en[i],
        "name_cn": majors[i],
        "meaning_up": f"{majors[i]} (正位)", 
        "meaning_rev": f"{majors[i]} (逆位)"
    })

# 2. 小阿爾克那 (Minor Arcana)
suits = [
    {"en": "Wands", "cn": "權杖"}, {"en": "Cups", "cn": "聖杯"},
    {"en": "Swords", "cn": "寶劍"}, {"en": "Pentacles", "cn": "錢幣"}
]
ranks = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Page", "Knight", "Queen", "King"]

id_counter = 22
for suit in suits:
    for rank in ranks:
        TAROT_DECK.append({
            "id": id_counter,
            "name_en": f"{rank} of {suit['en']}",
            "name_cn": f"{suit['cn']} {rank}",
            "meaning_up": f"{suit['cn']} {rank} (正位)",
            "meaning_rev": f"{suit['cn']} {rank} (逆位)"
        })
        id_counter += 1