from config import db

def get_user(user_id):
    user_ref = db.collection("users").document(user_id).get()
    return user_ref.to_dict() if user_ref.exists else None

def store_prediction(user_id, bowler_data):
    session_ref = db.collection("users").document(user_id).collection("session_data").document()
    session_ref.set(bowler_data)