import os
from Domashna4.microservices.prediction_service.app.utils.model_utils import load_data, train_model, get_model_path
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import numpy as np

class LSTMPredictionStrategy:
    def predict(self, issuer_name, period):
        look_back = 60
        model_map = {
            1: "model_1_day.h5",
            7: "model_1_week.h5",
            30: "model_1_month.h5"
        }
        model_name = model_map.get(period)

        if not model_name:
            raise ValueError("Invalid period. Use 1, 7, or 30.")

        model_path = get_model_path(model_name)
        data = load_data()

        if not os.path.exists(model_path):
            train_model(data, look_back, epochs=20, batch_size=32, model_name=model_path)

        model = load_model(model_path)
        predictions = self._predict_future(model, data, issuer_name, look_back, period)
        return {"status": "success", "predictions": predictions.tolist()}

    def _predict_future(self, model, data, issuer_name, look_back, days_ahead):
        scaler = MinMaxScaler(feature_range=(0, 1))
        data['Цена на последна трансакција'] = scaler.fit_transform(data[['Цена на последна трансакција']])

        issuer_data = data[data['Издавач'] == issuer_name].reset_index(drop=True)
        if issuer_data.empty:
            raise ValueError(f"No data available for issuer {issuer_name}")

        issuer_id = issuer_data['issuer_id'].iloc[0]
        prices = issuer_data['Цена на последна трансакција'].values

        if len(prices) < look_back:
            raise ValueError(f"Not enough data for prediction for {days_ahead} days ahead.")

        X_prices = prices[-look_back:]
        X_prices = np.reshape(X_prices, (1, look_back, 1))
        X_issuer = np.array([[issuer_id]])

        predictions = []
        for _ in range(days_ahead):
            prediction = model.predict([X_prices, X_issuer])
            predictions.append(prediction[0][0])

            X_prices = np.append(X_prices[0][1:], prediction).reshape(1, look_back, 1)

        predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1))
        return predictions.flatten()
