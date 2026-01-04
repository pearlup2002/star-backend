from skyfield.api import load, Topos
from skyfield.framelib import ecliptic_frame

def calculate_positions(year, month, day, hour=12, minute=0, lat=22.3, lon=114.2, is_time_unknown=False):
    # 1. Load Data
    ts = load.timescale()
    t = ts.utc(year, month, day, hour - 8, minute) # Simple UTC conversion (assuming input is UTC+8 for HK/TW)
    eph = load('de421.bsp')
    
    # 2. Define Earth and Location
    earth = eph['earth']
    location = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
    
    # 3. Define Planets (CRITICAL FIX HERE)
    # Outer planets must use 'barycenter' in de421.bsp
    planet_map = {
        'Sun': eph['sun'],
        'Moon': eph['moon'],
        'Mercury': eph['mercury'],
        'Venus': eph['venus'],
        'Mars': eph['mars'],
        'Jupiter': eph['jupiter barycenter'],  # Fixed
        'Saturn': eph['saturn barycenter'],    # Fixed
        'Uranus': eph['uranus barycenter'],    # Fixed
        'Neptune': eph['neptune barycenter'],  # Fixed
        'Pluto': eph['pluto barycenter']       # Fixed
    }

    results = {}
    
    # 4. Calculate Positions
    for name, body in planet_map.items():
        astrometric = location.at(t).observe(body)
        _, lon_deg, _ = astrometric.frame_latlon(ecliptic_frame)
        
        # Convert 0-360 to Zodiac Sign
        lon_deg = lon_deg.degrees % 360
        sign_index = int(lon_deg / 30)
        zodiac_signs = [
            "Aries", "Taurus", "Gemini", "Cancer", 
            "Leo", "Virgo", "Libra", "Scorpio", 
            "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        degree_in_sign = lon_deg % 30
        
        # Calculate House (Simplified logic - usually requires House System lib)
        # For now, we return the sign and exact degree
        results[name.lower()] = {
            "sign": zodiac_signs[sign_index],
            "deg": round(degree_in_sign, 2),
            "abs_deg": round(lon_deg, 2)
        }

    return results