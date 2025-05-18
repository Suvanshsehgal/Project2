import pandas as pd
import requests
from dotenv import load_dotenv
import os
from functools import lru_cache

load_dotenv()
API_KEY = os.getenv("API_KEY")

# Debug print to verify API key loading
print(f"[DEBUG] Loaded API_KEY: {API_KEY}")

# Load soil-crop dataset
data = pd.read_csv("chittor_final1.csv")

@lru_cache(maxsize=100)
def get_weather_data(location):
    try:
        if not API_KEY:
            return {'status': 'error', 'message': 'API key not set or loaded properly.'}

        if isinstance(location, tuple):
            url = f"http://api.openweathermap.org/data/2.5/weather?lat={location[0]}&lon={location[1]}&appid={API_KEY}&units=metric"
        else:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}&units=metric"

        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            return {'status': 'error', 'message': f"Weather API error {response.status_code}: {data.get('message', 'Unknown error')}"}

        return {
            'status': 'ok',
            'temperature': data['main']['temp'],
            'rainfall': data.get('rain', {}).get('1h', 0),
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed'],
            'soil_temp': max(10, data['main']['temp'] - 2),
            'soil_moisture': min(100, data['main']['humidity'] + 10)
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def generate_farmer_message(recommendation):
    weather = recommendation["weather"]
    fertilizers = recommendation["fertilizers"]
    land_size = recommendation["land_size_m2"]
    fallow_years = recommendation["fallow_years"]

    weather_advice = []
    if weather['rainfall'] > 10:
        weather_advice.append("🚨 **Heavy rain warning!** Avoid all field work today.")
    elif weather['rainfall'] > 5:
        weather_advice.append("🌧️ **Rain expected.** Delay fertilizer application.")
    else:
        weather_advice.append("☀️ **Dry conditions.** Water crops if needed.")

    if weather['wind_speed'] > 8:
        weather_advice.append("💨 **Strong winds!** No spraying today.")
    elif weather['wind_speed'] > 5:
        weather_advice.append("🌬️ **Breezy conditions.** Spray carefully.")

    soil_advice = []
    if weather['soil_temp'] < 15:
        soil_advice.append("❄️ **Cold soil.** Delay planting warm-season crops.")
    elif weather['soil_temp'] > 30:
        soil_advice.append("🔥 **Hot soil.** Water deeply in early morning.")

    if weather['soil_moisture'] > 85:
        soil_advice.append("💧 **Waterlogged soil.** Improve drainage.")
    elif weather['soil_moisture'] < 40:
        soil_advice.append("🏜️ **Dry soil.** Irrigate soon.")

    fert_advice = []
    if "Urea" in fertilizers:
        fert_advice.append("🔵 **Apply Urea** (140kg/acre for nitrogen)")
    if "Single Super Phosphate" in fertilizers:
        fert_advice.append("🟢 **Apply SSP** (50kg/acre for phosphorus)")
    if "Muriate of Potash" in fertilizers:
        fert_advice.append("🟣 **Apply MOP** (40kg/acre for potassium)")

    fallow_msg = ""
    if fallow_years >= 2:
        fallow_msg = "⚠️ **Long fallow period!** Plant green manure crops."

    message = f"""
🌱 **FARMER ADVISORY** 🌱
========================
**FIELD CONDITIONS:**
- Land: {land_size}m² | Fallow: {fallow_years} year(s)
- Soil Temp: {weather['soil_temp']}°C | Moisture: {weather['soil_moisture']}%

**WEATHER ALERTS:**
{chr(10).join(weather_advice)}

**SOIL CARE:**
{chr(10).join(soil_advice) if soil_advice else "✅ Soil conditions normal"}

**FERTILIZER PLAN:**
{chr(10).join(fert_advice) if fert_advice else "✅ No fertilizers needed now"}

**SPECIAL NOTES:**
{fallow_msg if fallow_msg else "No critical issues detected"}
"""
    return message

def fertilizer_recommendation(soil_type, crop_type, land_size, fallow_years,
                              use_my_location=False, lat=None, lon=None, manual_location=None):
    filtered = data[(data['Soil_type'] == soil_type) & (data['Crop_type'] == crop_type)]
    if filtered.empty:
        return {'error': 'No data for this soil-crop combination.'}

    if use_my_location and lat and lon:
        weather = get_weather_data((lat, lon))
    elif manual_location:
        weather = get_weather_data(manual_location)
    else:
        weather = {
            'status': 'ok',
            'temperature': 25,
            'rainfall': 0,
            'humidity': 60,
            'wind_speed': 2,
            'soil_temp': 23,
            'soil_moisture': 50
        }

    if weather['status'] != 'ok':
        return {'error': f"Weather API error: {weather['message']}"}

    row = filtered.iloc[0]
    recommendation = {
        'fertilizers': [],
        'land_size_m2': land_size,
        'fallow_years': fallow_years,
        'weather': weather
    }

    if row['Avail_N'] < 280:
        recommendation['fertilizers'].append("Urea")
    if row['Avail_P'] < 10:
        recommendation['fertilizers'].append("Single Super Phosphate")
    if row['Exch_K'] < 110:
        recommendation['fertilizers'].append("Muriate of Potash")

    return recommendation
