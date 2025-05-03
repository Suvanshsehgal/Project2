import gradio as gr
from logic import fertilizer_recommendation, generate_farmer_message, data

with gr.Blocks(theme=gr.themes.Soft(), title="FarmSmart Advisor") as demo:
    # Header
    gr.Markdown("""
    # 🌾 FarmSmart Advisor
    *AI-powered fertilizer and farming recommendations*
    """)

    # Input Section
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
        land_size = gr.Number(
            label="3. Land Size (m²)",
            value=5000
        )
        fallow_years = gr.Number(
            label="4. Fallow Years",
            value=1
        )

    # Location Section
    use_gps = gr.Checkbox(
        label="📍 Use my current location",
        value=False
    )
    manual_loc = gr.Textbox(
        label="🌍 Or enter location (City/Region)",
        visible=True,
        value="Chittoor"
    )

    # Hidden GPS inputs
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

    # Buttons
    with gr.Row():
        analyze_btn = gr.Button("Analyze Conditions", variant="primary")
        clear_btn = gr.Button("Clear")

    # Output Section
    weather_card = gr.Markdown("## 🌦️ Weather Data\n*Waiting for analysis...*")
    advice_card = gr.Markdown("## 📜 Farmer's Advisory\n*Recommendations will appear here*")
    data_output = gr.JSON(label="Technical Data", visible=False)

    # Dynamic UI
    use_gps.change(
        lambda x: gr.update(visible=not x),
        inputs=use_gps,
        outputs=manual_loc
    )

    # Main function
    def analyze(soil, crop, size, fallow, use_gps, lat, lon, loc):
        try:
            result = fertilizer_recommendation(
                soil_type=soil,
                crop_type=crop,
                land_size=size,
                fallow_years=fallow,
                use_my_location=use_gps,
                lat=lat,
                lon=lon,
                manual_location=loc
            )

            if "error" in result:
                return (
                    f"## ❌ Error\n{result['error']}",
                    "❗ Check your inputs or weather API setup.",
                    result
                )

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

            return (
                weather_report,
                generate_farmer_message(result),
                result
            )
        except Exception as e:
            return (
                f"## ❌ Unexpected Error\n{str(e)}",
                "🚫 Something went wrong. Please try again.",
                {}
            )

    # Event handlers
    analyze_btn.click(
        fn=analyze,
        inputs=[soil_type, crop_type, land_size, fallow_years, use_gps, lat, lon, manual_loc],
        outputs=[weather_card, advice_card, data_output]
    )

    clear_btn.click(
        fn=lambda: [
            None,  # soil_type
            None,  # crop_type
            5000,  # land_size
            1,     # fallow_years
            False, # use_gps
            "",    # lat
            "",    # lon
            "",    # manual_loc
            "## 🌦️ Weather Data\n*Waiting for analysis...*",
            "## 📜 Farmer's Advisory\n*Recommendations will appear here*",
            None   # data_output
        ],
        outputs=[
            soil_type, crop_type, land_size, fallow_years, use_gps,
            lat, lon, manual_loc, weather_card, advice_card, data_output
        ]
    )

demo.launch()
