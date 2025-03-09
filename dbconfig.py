import firebase_admin
from firebase_admin import credentials, firestore, auth

# Load Firebase credentials
cred = credentials.Certificate("C:/Users/sanju/OneDrive/Documents/iit lectures/Final Year 1st Sem/Flask/final-year-project-1f05b-firebase-adminsdk-fbsvc-fa21fb3ad9.json")

firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()
