import pandas as pd
from model import predict_new_bowler, calculate_bowling_kpis, normalize_and_log_transform
from config import dataset_paths
from config import feature_importance_paths

training_data = {}
feature_importance_data = {}

# Initialize training_data and feature_importance_data
training_data = {}
feature_importance_data = {}

for phase, path in dataset_paths.items():
    df = pd.read_csv(path)
    df_transformed = calculate_bowling_kpis(df)
    df_transformed = normalize_and_log_transform(df_transformed)
    training_data[phase] = df_transformed

for phase, path in feature_importance_paths.items():
    feature_importance_data[phase] = pd.read_csv(path)

# Example usage in predict_bowler
def predict_bowler(phase, bowler_stats):
    if phase not in training_data:
        return {"error": f"Invalid phase: {phase}. Valid phases are: {list(training_data.keys())}"}
    
    if phase not in feature_importance_data:
        return {"error": f"Feature importance data not found for phase: {phase}. Valid phases are: {list(feature_importance_data.keys())}"}
    
    return predict_new_bowler(phase, bowler_stats, training_data[phase], feature_importance_data[phase])