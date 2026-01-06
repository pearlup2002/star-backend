import secrets
import random
from tarot_data import TAROT_DECK

# 定義牌陣 (Spreads)
SPREADS = {
    "single": {
        "name": "單張占卜",
        "cards_needed": 1,
        "positions": ["問題的核心/當下指引"]
    },
    "love_3": {
        "name": "愛情三牌陣",
        "cards_needed": 3,
        "positions": ["你現在的狀態", "對方的想法", "未來發展趨勢"]
    },
    "time_3": {
        "name": "聖三角 (時間流)",
        "cards_needed": 3,
        "positions": ["過去的經驗", "現在的狀況", "未來的結果"]
    },
    "choice_2": {
        "name": "二擇一牌陣",
        "cards_needed": 5, 
        # 1.現狀, 2.選擇A過程, 3.選擇B過程, 4.選擇A結果, 5.選擇B結果
        "positions": ["現狀", "選擇 A 的過程", "選擇 B 的過程", "選擇 A 的結果", "選擇 B 的結果"]
    },
}

def draw_cards(spread_type="single"):
    """
    專業洗牌與抽牌函數
    """
    # 1. 獲取牌陣定義
    spread = SPREADS.get(spread_type)
    if not spread:
        raise ValueError("Unknown spread type")
    
    count = spread['cards_needed']
    
    # 2. 深度洗牌 (使用 secrets 確保真隨機)
    # 複製一副新牌，以免影響原始數據
    deck = list(TAROT_DECK)
    
    # 使用加密級隨機數進行洗牌 (Fisher-Yates Shuffle with secrets)
    shuffled_deck = []
    while deck:
        idx = secrets.randbelow(len(deck)) # 隨機選一張
        card = deck.pop(idx)
        
        # 3. 隨機決定正逆位 (50% 機率)
        is_upright = secrets.choice([True, False])
        
        card_result = {
            "id": card["id"],
            "name_cn": card["name_cn"],
            "name_en": card["name_en"],
            "is_upright": is_upright,
            "position": "waiting", # 暫時佔位
            "meaning": card["meaning_up"] if is_upright else card["meaning_rev"]
        }
        shuffled_deck.append(card_result)
        
    # 4. 抽出前 N 張
    drawn_cards = shuffled_deck[:count]
    
    # 5. 分配位置意義
    for i, card in enumerate(drawn_cards):
        if i < len(spread['positions']):
            card['position'] = spread['positions'][i]
            
    return {
        "spread_name": spread['name'],
        "cards": drawn_cards
    }