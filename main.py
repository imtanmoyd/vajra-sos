import firebase_admin
from firebase_admin import credentials, firestore, messaging
import requests
import schedule
import time
import google.generativeai as genai

# 🚀 Step 1: Initialize Firebase
cred = credentials.Certificate("vajrasos-firebase-adminsdk-fbsvc-b5ba9d8a64.json")  # Ensure correct path
firebase_admin.initialize_app(cred)
db = firestore.client()


import json
import requests
from google.oauth2 import service_account

# Load Firebase service account credentials
FIREBASE_CREDENTIALS_PATH = "-------" # Load the Credentials file

def get_access_token():
    """Generates an OAuth 2.0 access token for Firebase Cloud Messaging."""
    credentials = service_account.Credentials.from_service_account_file(
        FIREBASE_CREDENTIALS_PATH, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    access_token = credentials.with_scopes(["https://www.googleapis.com/auth/firebase.messaging"]).token
    return access_token

def send_fcm_notification(phone, message):
    try:
        # Get access token
        access_token = get_access_token()

        # Define FCM HTTP v1 URL (replace PROJECT_ID)
        PROJECT_ID = "vajrasos"  # Replace with your Firebase project ID
        FCM_URL = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Prepare request payload
        payload = {
            "message": {
                "notification": {
                    "title": "⚠ VajraSOS Alert",
                    "body": message
                },
                "topic": phone  # Use phone as FCM topic
            }
        }

        # Send request
        response = requests.post(FCM_URL, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            print(f"✅ Notification sent to {phone}: {message}")
            return response.json()
        else:
            print(f"🔥 FCM Error: {response.text}")
            return None

    except Exception as e:
        print(f"🔥 Exception in FCM: {e}")
        return None


# 🚀 Step 2: Initialize Google Gemini API
GEMINI_API_KEY = "--------" # Custom key
genai.configure(api_key=GEMINI_API_KEY)

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
schedule.every(1).hours.do(monitor_weather)

print("🌾 VajraSOS is Running... Monitoring Weather for Alerts")
while True:
    schedule.run_pending()
    time.sleep(60)  # Wait 1 minute before checking again


from twilio.rest import Client

# 🚀 Step 2: Twilio Credentials (Replace with yours)
TWILIO_SID = "-----"
TWILIO_AUTH_TOKEN = "-----"
TWILIO_PHONE_NUMBER = "----"  # The Twilio number you get

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# 🚀 Step 3: Fetch Farmers' Phone Numbers from Firestore
def get_farmer_phone_numbers():
    try:
        farmers_ref = db.collection("farmers")  # Firestore collection
        docs = farmers_ref.stream()
        phone_numbers = [doc.to_dict().get("phone") for doc in docs if doc.to_dict().get("phone")]
        return phone_numbers
    except Exception as e:
        print(f"⚠️ Error Fetching Numbers: {e}")
        return []

# 🚀 Step 4: Send SMS using Twilio API
def send_sms(phone_number, message_text):
    try:
        message = client.messages.create(
            body=message_text,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        print(f"✅ SMS sent to {phone_number} (Message SID: {message.sid})")
    except Exception as e:
        print(f"🔥 Error sending SMS to {phone_number}: {e}")

# 🚀 Step 5: Main Execution
if __name__ == "__main__":
    farmer_numbers = get_farmer_phone_numbers()  # Fetch numbers from Firebase
    message = "⚠️ VajraSOS Alert! Heavy Rain Expected. Secure your crops!"

    if farmer_numbers:
        for number in farmer_numbers:
            send_sms(number, message)  # Send SMS individually
    else:
        print("⚠️ No farmers found in database!")
