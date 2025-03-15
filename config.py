# config.py
import firebase_admin
from firebase_admin import credentials, firestore

def initialize_firebase():
    cred = credentials.Certificate("C:/Users/sanju/OneDrive/Documents/iit lectures/Final Year 1st Sem/Flask/final-year-project-1f05b-firebase-adminsdk-fbsvc-fa21fb3ad9.json")
    firebase_admin.initialize_app(cred)

# Initialize Firebase
initialize_firebase()

# Initialize Firestore
db = firestore.client()

# Dataset Paths
dataset_paths = {
    "Powerplay": "C:/Users/sanju/OneDrive/Documents/iit lectures/Final Year 1st Sem/Flask/Cluster Results and Other data files/WeightedDataSetPowerplay_Clusters.csv",
    "MiddleOvers": "C:/Users/sanju/OneDrive/Documents/iit lectures/Final Year 1st Sem/Flask/Cluster Results and Other data files/WeightedDataSetMiddleovers_Clusters.csv",
    "DeathOvers": "C:/Users/sanju/OneDrive/Documents/iit lectures/Final Year 1st Sem/Flask/Cluster Results and Other data files/WeightedDataSetDeath_Clusters.csv"

}
feature_importance_paths = {
    "Powerplay": "C:/Users/sanju/OneDrive/Documents/iit lectures/Final Year 1st Sem/Flask/Cluster Results and Other data files/Powerplay_Feature_Importance.csv",
    "MiddleOvers": "C:/Users/sanju/OneDrive/Documents/iit lectures/Final Year 1st Sem/Flask/Cluster Results and Other data files/MiddleOvers_Feature_Importance.csv",
    "DeathOvers": "C:/Users/sanju/OneDrive/Documents/iit lectures/Final Year 1st Sem/Flask/Cluster Results and Other data files/DeathOvers_Feature_Importance.csv"
}