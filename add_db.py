import firebase_admin
from firebase_admin import credentials, firestore

# 🚀 Step 1: Initialize Firebase with your service account key
cred = credentials.Certificate("vajrasos-firebase-adminsdk-fbsvc-e161844074.json")  # Ensure correct path
firebase_admin.initialize_app(cred)
db = firestore.client()

# 🚀 Step 2: Define Farmers Data
farmers = [
    {"name": "name1", "phone": "no1", "latitude": 23.8103, "longitude": 90.4125},
    {"name": "name2", "phone": "no2", "latitude": 25.5941, "longitude": 85.1376},
    {"name": "name3", "phone": "no3", "latitude": 28.7041, "longitude": 77.1025}
]

# 🚀 Step 3: Upload Farmers Data
for farmer in farmers:
    db.collection("farmers").add(farmer)
    print(f"✅ Farmer {farmer['name']} added successfully!")

print("🌾 All farmers have been added to Firestore!")
