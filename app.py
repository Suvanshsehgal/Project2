import gradio as gr
from logic import fertilizer_recommendation, generate_farmer_message, data

with gr.Blocks(theme=gr.themes.Soft(), title="FarmSmart Advisor") as demo:
    gr.Markdown("""
    # 🌾 FarmSmart Advisor
    *AI-powered fertilizer and farming recommendations*
    """)

    with gr.Row():
        soil_type = gr.Dropdown(
            label="1. Select Soil Type",
            choices=sorted(data['Soil_type'].unique()),
            value="Loamy"
        )
        crop_type = gr.Dropdown(
            label="2. Select Crop",
            choices=sorted(data['Crop_type'].unique()),
            value="Wheat"
        )

    with gr.Row():
        land_size = gr.Number(label="3. Land Size (m²)", value=5000)
        fallow_years = gr.Number(label="4. Fallow Years", value=1)

    use_gps = gr.Checkbox(label="📍 Use my current location", value=False)
    manual_loc = gr.Textbox(label="🌍 Or enter location (City/Region)", value="Chittoor", visible=True)
    lat = gr.Textbox(visible=False, label="Latitude")
    lon = gr.Textbox(visible=False, label="Longitude")

    # Geolocation JS
    gr.HTML("""
    <script>
        document.querySelector('input[aria-label="📍 Use my current location"]').addEventListener('click', function() {
            if (this.checked) {
                navigator.geolocation.getCurrentPosition(
                    pos => {
                        document.querySelector('input[aria-label="Latitude"]').value = pos.coords.latitude;
                        document.querySelector('input[aria-label="Longitude"]').value = pos.coords.longitude;
                    },
                    err => alert("Enable location access for accurate weather data")
                );
            }
        });
    </script>
    """)

    analyze_btn = gr.Button("Analyze Conditions", variant="primary")
    clear_btn = gr.Button("Clear")

    weather_card = gr.Markdown("## 🌦️ Weather Data\n*Waiting for analysis...*")
    advice_card = gr.Markdown("## 📜 Farmer's Advisory\n*Recommendations will appear here*")
    data_output = gr.JSON(label="Technical Data", visible=False)

    # Show/hide manual location based on GPS checkbox
    def toggle_manual_location(use_gps_value):
        return gr.update(visible=not use_gps_value)
    use_gps.change(toggle_manual_location, inputs=use_gps, outputs=manual_loc)

    def analyze(soil, crop, size, fallow, use_gps_val, lat_val, lon_val, loc_val):
        result = fertilizer_recommendation(
            soil_type=soil,
            crop_type=crop,
            land_size=size,
            fallow_years=fallow,
            use_my_location=use_gps_val,
            lat=lat_val if lat_val else None,
            lon=lon_val if lon_val else None,
            manual_location=loc_val if loc_val else None
        )
        if "error" in result:
            return (f"## ❌ Error\n{result['error']}",
                    "❗ Check your inputs or weather API setup.",
                    result)
        
        weather = result["weather"]
        weather_report = f"""
## 🌦️ Current Conditions
- Temperature: **{weather['temperature']}°C**
- Rainfall: **{weather['rainfall']} mm** (last hour)
- Humidity: **{weather['humidity']}%**
- Wind: **{weather['wind_speed']} m/s**
- Soil Temp: **{weather['soil_temp']}°C**
- Soil Moisture: **{weather['soil_moisture']}%**
"""
        return weather_report, generate_farmer_message(result), result

    analyze_btn.click(
        analyze,
        inputs=[soil_type, crop_type, land_size, fallow_years, use_gps, lat, lon, manual_loc],
        outputs=[weather_card, advice_card, data_output]
    )

    clear_btn.click(
        lambda: [
            None, None, 5000, 1, False,
            None, None, "Chittoor",
            "## 🌦️ Weather Data\n*Waiting for analysis...*",
            "## 📜 Farmer's Advisory\n*Recommendations will appear here*",
            {}
        ],
        inputs=[],
        outputs=[soil_type, crop_type, land_size, fallow_years, use_gps, lat, lon, manual_loc, weather_card, advice_card, data_output]
    )

if __name__ == "__main__":
    demo.launch()
