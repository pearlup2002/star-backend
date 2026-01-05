I need to add Traditional Chinese BaZi (Eight Characters) calculation to `engine.py`.

Please import `from lunar_python import Solar` and rewrite `engine.py`.

### New Features in `calculate_positions`:
1.  **Keep Existing Logic:** Skyfield planets, Western Elements (Fire/Air...), Houses.
2.  **Add BaZi Logic:**
    - Convert input date to Solar object: `solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)`
    - Get Lunar object: `lunar = solar.getLunar()`
    - Get the 8 Characters (BaZi): Year/Month/Day/Time Ganzhi.
    - **Determine "Day Master" (日主):** This is the Heavenly Stem of the Day. Map it to an Element (e.g., Jia/Yi = Wood). This represents the user's "Self Element".
3.  **Calculate Chinese 5 Elements Ratio:**
    - Map all 8 characters (4 Stems, 4 Branches) to their Elements (Metal, Wood, Water, Fire, Earth).
    - Count them.
    - Return a dictionary: `{"Metal": 1, "Wood": 3, "Water": 2, "Fire": 1, "Earth": 1}`.
4.  **Formatting:**
    - Return specific fields: `self_element` (e.g., "火"), `bazi_text` (e.g., "癸亥年..."), and the counts.

### Mapping Reference (for your code):
- **Stems:** Jia/Yi=Wood, Bing/Ding=Fire, Wu/Ji=Earth, Geng/Xin=Metal, Ren/Gui=Water.
- **Branches:**
  - Water: Zi, Hai
  - Earth: Chou, Chen, Wei, Xu
  - Wood: Yin, Mao
  - Fire: Si, Wu
  - Metal: Shen, You

Please write the complete `engine.py` merging Western and Chinese logic.