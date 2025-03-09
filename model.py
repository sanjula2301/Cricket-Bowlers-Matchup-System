import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# **Precomputed Means and Standard Deviations**
precomputed_means = {
    "BWI": 0.3431, "DBP": 40.6230, "BP": 14.3196, "ECON": 7.4214,
    "BA": 22.2653, "SR": 17.8246, "SPI": 1.9847, "BBI": 47.7514
}

precomputed_stds = {
    "BWI": 0.4748, "DBP": 14.2323, "BP": 8.7720, "ECON": 2.6252,
    "BA": 17.7893, "SR": 12.8118, "SPI": 3.4352, "BBI": 64.4984
}

# **Step 1: Compute Bowling KPIs from Raw Match Stats**
def calculate_bowling_kpis(df):
    df_new = df.copy()
    df_new["BA"] = np.where(df["Wkt"] > 0, df["Runs Conceded"] / df["Wkt"], 0)
    df_new["SR"] = np.where(df["Wkt"] > 0, df["No of Balls"] / df["Wkt"], 0)
    df_new["BBI"] = np.where(df["Innings"] > 0, df["No of Balls"] / df["Innings"], 0)
    df_new["ECON"] = np.where(df["No of Balls"] > 0, (df["Runs Conceded"] / df["No of Balls"]) * 6, 0)
    df_new["BWI"] = np.where(df["Wkt"] >= 4, 1, 0)
    df_new["SPI"] = np.where(
        (df["Innings"] - df_new["BWI"]) > 0,
        (df["Wkt"] - df_new["BWI"]) / (df["Innings"] - df_new["BWI"]),
        0
    )
    df_new["DBP"] = np.where(df["No of Balls"] > 0, (df["Dot balls"] / df["No of Balls"]) * 100, 0)
    df_new["BP"] = np.where(df["No of Balls"] > 0, ((df["4s"] + df["6s"]) / df["No of Balls"]) * 100, 0)
    return df_new

# **Step 2: Normalize and Log Transform KPIs**
def normalize_and_log_transform(df):
    df_new = df.copy()
    df_new['BA_log'] = np.log1p(df_new['BA'])
    df_new['SR_log'] = np.log1p(df_new['SR'])
    df_new['SPI_log'] = np.log1p(df_new['SPI'])
    df_new['BBI_log'] = np.log1p(df_new['BBI'])
    df_new['BWI_normalized'] = (df_new['BWI'] - precomputed_means['BWI']) / precomputed_stds['BWI']
    df_new['DBP_normalized'] = (df_new['DBP'] - precomputed_means['DBP']) / precomputed_stds['DBP']
    df_new['BP_normalized'] = (df_new['BP'] - precomputed_means['BP']) / precomputed_stds['BP']
    df_new['Econ_normalized'] = (df_new['ECON'] - precomputed_means['ECON']) / precomputed_stds['ECON']
    return df_new


def predict_new_bowler(phase_name, new_bowler_raw, training_df, feature_importance_combined):
    print(f"\n🔹 Processing new bowler for phase: {phase_name}")

    # Convert input bowler stats to DataFrame
    new_bowler_df = pd.DataFrame([new_bowler_raw])

    # Step 1: Compute KPIs
    new_bowler_df = calculate_bowling_kpis(new_bowler_df)

    # Step 2: Normalize & Apply Log Transformation
    new_bowler_df = normalize_and_log_transform(new_bowler_df)

    # Define KPI Features
    numeric_features = ["BWI_normalized", "DBP_normalized", "BP_normalized", "Econ_normalized",
                        "BA_log", "SR_log", "SPI_log", "BBI_log"]

    # Step 3: Extract Training Features & Labels
    X_train = training_df[numeric_features]
    y_train = training_df['Cluster']

    # Step 4: Train Random Forest Classifier
    rf_model = RandomForestClassifier(n_estimators=200, random_state=42)
    rf_model.fit(X_train, y_train)

    # Step 5: Predict the cluster for the new bowler
    predicted_cluster = rf_model.predict(new_bowler_df[numeric_features])[0]
    print(f"✅ Predicted Cluster for New Bowler in {phase_name}: {predicted_cluster}")

    # Step 6: Ensure feature importance data is properly structured
    if "Feature" not in feature_importance_combined.columns:
        raise ValueError("Error: 'Feature' column missing in feature importance data")

    # Convert feature importance to dictionary format
    feature_importance_combined = feature_importance_combined.set_index("Feature")

    # Step 7: Compute DPPI Score using the feature importance of the predicted cluster
    DPPI_Bowl_score = sum(
        new_bowler_df[feature].values[0] * feature_importance_combined.loc[feature, "Importance"].values[0]
        for feature in numeric_features
    )

    print(f"🔹 Predicted DPPI Score for New Bowler in {phase_name}: {DPPI_Bowl_score:.2f}")

    # Step 8: Return predictions and feature importance
    return {
        "phase_name": phase_name,
        "predicted_cluster": int(predicted_cluster),
        "DPPI_Bowl_score": round(DPPI_Bowl_score, 2),
        "feature_importance": feature_importance_combined.reset_index().to_dict(orient="records")
    }