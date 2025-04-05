import firebase_admin
from firebase_admin import credentials, firestore, messaging
import requests
import schedule
import time
import google.generativeai as genai

# 🚀 Step 1: Initialize Firebase
cred = credentials.Certificate("vajrasos-firebase-adminsdk-fbsvc-7056a146f5.json")  # Ensure correct path
firebase_admin.initialize_app(cred)
db = firestore.client()

# 🚀 Step 2: Initialize Google Gemini API
GEMINI_API_KEY = "GEMINI_API_KEY" # custom key
genai.configure(api_key=GEMINI_API_KEY)

models = genai.list_models()
for model in models:
    print(model.name, model.supported_generation_methods)



# 🚀 Step 3: Fetch Farmers from Firebase
def get_farmers():
    try:
        farmers_ref = db.collection("farmers").stream()
        farmers = []
        for f in farmers_ref:
            farmer_data = f.to_dict()
            if "name" in farmer_data and "phone" in farmer_data and "latitude" in farmer_data and "longitude" in farmer_data:
                farmers.append(farmer_data)
        return farmers
    except Exception as e:
        print(f"🔥 Firebase Error: {e}")
        return []

# 🚀 Step 4: Get Weather Data from Google Gemini API
def get_weather_gemini(latitude, longitude):
    try:
        prompt = f"Provide a structured weather report for latitude {latitude} and longitude {longitude}. Include temperature, rain, and wind speed."
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"🔥 Gemini API Error: {e}")
        return "Error fetching weather data"

# 🚀 Step 5: Define Weather Alert Conditions
def check_alerts(weather_data):
    weather_data = weather_data.lower()
    if "heatwave" in weather_data or "very high temperature" in weather_data:
        return "🔥 Heatwave Alert! Stay hydrated and avoid outdoor work."
    if "storm" in weather_data or "high winds" in weather_data:
        return "🌪️ Storm Alert! Take necessary precautions."
    if "heavy rain" in weather_data or "flood" in weather_data:
        return "🌧️ Heavy Rain Alert! Secure your crops and stay safe."
    return None

# 🚀 Step 6: Send Notifications via Firebase Cloud Messaging (Free)
def send_fcm_notification(phone, message):
    try:
        msg = messaging.Message(
            notification=messaging.Notification(
                title="⚠️ VajraSOS Alert",
                body=message
            ),
            topic=phone  # Use phone number as FCM topic for notifications
        )
        response = messaging.send(msg)
        return response
    except Exception as e:
        print(f"🔥 FCM Error: {e}")
        return None

# 🚀 Step 7: Monitor Weather & Send Alerts
def monitor_weather():
    farmers = get_farmers()
    if not farmers:
        print("⚠️ No farmers registered in Firebase.")
        return
    
    for farmer in farmers:
        weather_data = get_weather_gemini(farmer["latitude"], farmer["longitude"])
        alert = check_alerts(weather_data)

        if alert:
            send_fcm_notification(farmer["phone"], alert)
            print(f"✅ Alert Sent to {farmer['name']} ({farmer['phone']}): {alert}")
        else:
            print(f"✅ Weather normal for {farmer['name']}.")

# 🚀 Step 8: Automate Every Hour
monitor_weather()  # Run once immediately

# 🚀 Step 8: Automate Every Hour
schedule.every(1).hours.do(monitor_weather)

print("🌾 VajraSOS is Running... Monitoring Weather for Alerts")
while True:
    schedule.run_pending()
    time.sleep(60)
