import firebase_admin
from firebase_admin import credentials, firestore, messaging
import schedule
import time
import google.generativeai as genai

# 🚀 Step 1: Initialize Firebase
def initialize_firebase():
    try:
        cred = credentials.Certificate("vajrasos-firebase-adminsdk-fbsvc-7056a146f5.json")
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(f"🔥 Firebase initialization error: {e}")
        raise

# 🚀 Step 2: Initialize Google Gemini API
def initialize_gemini(api_key):
    try:
        genai.configure(api_key=api_key)
        # Verify available models
        available_models = [m.name for m in genai.list_models()]
        
        # Use one of the available Gemini models
        gemini_model_name = 'models/gemini-1.5-flash'
        
        if gemini_model_name not in available_models:
            print(f"⚠️ Available models: {available_models}")
            raise ValueError("Gemini model not available")
        
        return genai.GenerativeModel(gemini_model_name)
    except Exception as e:
        print(f"🔥 Gemini initialization error: {e}")
        raise
# 🚀 Step 3: Fetch Farmers from Firebase
def get_farmers(db):
    try:
        farmers_ref = db.collection("farmers").stream()
        farmers = []
        for doc in farmers_ref:
            farmer_data = doc.to_dict()
            required_fields = ["name", "phone", "latitude", "longitude"]
            if all(field in farmer_data for field in required_fields):
                farmers.append(farmer_data)
        return farmers
    except Exception as e:
        print(f"🔥 Error fetching farmers: {e}")
        return []

# 🚀 Step 4: Get Weather Data from Google Gemini API
def get_weather_gemini(model, latitude, longitude):
    try:
        prompt = (
            f"Provide a concise weather report for coordinates {latitude},{longitude}. "
            "Include: temperature (in Celsius), precipitation chance (%), wind speed (km/h), "
            "and any significant weather alerts. Format briefly for SMS alerts."
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"🔥 Error getting weather data: {e}")
        return None

# 🚀 Step 5: Define Weather Alert Conditions
def check_alerts(weather_data):
    if not weather_data:
        return None
    
    weather_data = weather_data.lower()
    alerts = {
        "heat": "🔥 Heatwave Alert! Stay hydrated and avoid outdoor work.",
        "storm": "🌪️ Storm Alert! Take necessary precautions.",
        "high wind": "💨 High Wind Alert! Secure loose objects.",
        "heavy rain": "🌧️ Heavy Rain Alert! Prepare for possible flooding.",
        "flood": "🛑 Flood Alert! Move to higher ground if necessary.",
        "frost": "❄️ Frost Alert! Protect sensitive crops.",
        "drought": "🏜️ Drought Alert! Conserve water resources."
    }
    
    for keyword, alert_message in alerts.items():
        if keyword in weather_data:
            return alert_message
    return None

# 🚀 Step 6: Send Notifications via Firebase Cloud Messaging
def send_fcm_notification(phone, message):
    try:
        # Note: FCM topics have restrictions on format
        # Convert phone to valid topic name by removing non-alphanumeric chars
        topic = ''.join(c for c in phone if c.isalnum())
        
        message = messaging.Message(
            notification=messaging.Notification(
                title="🌾 Farm Weather Alert",
                body=message
            ),
            topic=topic
        )
        response = messaging.send(message)
        print(f"📤 Notification sent to {phone} (topic: {topic})")
        return response
    except Exception as e:
        print(f"🔥 Error sending notification: {e}")
        return None

# 🚀 Step 7: Main Monitoring Function
def monitor_weather(db, gemini_model):
    print("\n🔄 Checking weather for all farmers...")
    farmers = get_farmers(db)
    
    if not farmers:
        print("⚠️ No farmers found in database")
        return
    
    for farmer in farmers:
        try:
            print(f"\n👨‍🌾 Checking weather for {farmer['name']} ({farmer['phone']})")
            weather_data = get_weather_gemini(
                gemini_model, 
                farmer['latitude'], 
                farmer['longitude']
            )
            
            if weather_data:
                print(f"🌤️ Weather data: {weather_data[:100]}...")  # Truncate for display
                alert = check_alerts(weather_data)
                
                if alert:
                    print(f"⚠️ ALERT: {alert}")
                    send_fcm_notification(farmer['phone'], alert)
                else:
                    print("✅ No alerts for this location")
            else:
                print("⚠️ Could not retrieve weather data")
                
        except Exception as e:
            print(f"🔥 Error processing farmer {farmer['name']}: {e}")

# 🚀 Main Execution
def main():
    # Configuration
    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"  # Replace with your actual API key
    
    try:
        # Initialize services
        db = initialize_firebase()
        gemini_model = initialize_gemini(GEMINI_API_KEY)
        
        # Initial run
        monitor_weather(db, gemini_model)
        
        # Schedule hourly runs
        schedule.every(1).hours.do(monitor_weather, db, gemini_model)
        
        print("\n🌾 VajraSOS is running. Monitoring weather for alerts...")
        print("Press Ctrl+C to stop\n")
        
        while True:
            schedule.run_pending()
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
    except Exception as e:
        print(f"\n🔥 Fatal error: {e}")

if __name__ == "__main__":
    main()