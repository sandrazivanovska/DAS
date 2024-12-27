import os
from analysis.prediction import load_data, train_model_for_1_day, train_model_for_1_week, train_model_for_1_month

if __name__ == "__main__":
    print("Loading data...")
    data = load_data()

    print("Training model for 1-day prediction...")
    model_1_day, scaler_1_day = train_model_for_1_day(data, look_back=60, epochs=20, batch_size=32)
    print("1-day prediction model trained and saved.")

    print("Training model for 1-week prediction...")
    model_1_week, scaler_1_week = train_model_for_1_week(data, look_back=60, epochs=20, batch_size=32)
    print("1-week prediction model trained and saved.")

    print("Training model for 1-month prediction...")
    model_1_month, scaler_1_month = train_model_for_1_month(data, look_back=60, epochs=20, batch_size=32)
    print("1-month prediction model trained and saved.")

    print("All models trained and saved successfully.")
