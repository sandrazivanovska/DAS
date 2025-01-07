import os
import sqlite3
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from keras.layers import Flatten
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model, Model
from tensorflow.keras.layers import Input, Embedding, LSTM, Dense, concatenate

MODEL_DIR = "lstm_models"
LOOK_BACK = 60
DEFAULT_EPOCHS = 20
DEFAULT_BATCH_SIZE = 32

app = Flask(__name__)

def get_model_path(model_name):
    return os.path.join(MODEL_DIR, model_name)

def load_data():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..', 'stock_data.db')
    conn = sqlite3.connect(db_path)

    query = """
    SELECT Датум, `Цена на последна трансакција`, Издавач
    FROM stock_data
    WHERE `Цена на последна трансакција` IS NOT NULL
    ORDER BY Издавач, Датум ASC;
    """
    data = pd.read_sql_query(query, conn)
    conn.close()

    data['Цена на последна трансакција'] = data['Цена на последна трансакција'].str.replace('.', '', regex=False)
    data['Цена на последна трансакција'] = data['Цена на последна трансакција'].str.replace(',', '.', regex=False)
    data['Цена на последна трансакција'] = data['Цена на последна трансакција'].astype(float)
    data['Датум'] = pd.to_datetime(data['Датум'])
    data = data.sort_values(by=['Издавач', 'Датум'])
    data['issuer_id'] = data['Издавач'].astype('category').cat.codes
    return data

def create_dataset(data, look_back=60):
    X_prices, X_issuers, Y_prices = [], [], []
    for issuer_id in data['issuer_id'].unique():
        issuer_data = data[data['issuer_id'] == issuer_id].reset_index(drop=True)
        prices = issuer_data['Цена на последна трансакција'].values
        for i in range(len(prices) - look_back):
            X_prices.append(prices[i:i+look_back])
            X_issuers.append(issuer_id)
            Y_prices.append(prices[i+look_back])
    return np.array(X_prices), np.array(X_issuers), np.array(Y_prices)

def build_model(num_issuers, look_back=60):
    input_prices = Input(shape=(look_back, 1), name='prices_input')
    lstm_out = LSTM(50, return_sequences=True)(input_prices)
    lstm_out = LSTM(50, return_sequences=False)(lstm_out)

    input_issuer = Input(shape=(1,), name='issuer_input')
    embedding = Embedding(input_dim=num_issuers, output_dim=10)(input_issuer)
    embedding_out = Flatten()(embedding)

    concat = concatenate([lstm_out, embedding_out])
    dense_out = Dense(25, activation='relu')(concat)
    output = Dense(1)(dense_out)

    model = Model(inputs=[input_prices, input_issuer], outputs=output)
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

def train_model(data, look_back, epochs, batch_size, model_name):
    model_path = get_model_path(model_name)

    scaler = MinMaxScaler(feature_range=(0, 1))
    data['Цена на последна трансакција'] = scaler.fit_transform(data[['Цена на последна трансакција']])

    X_prices, X_issuers, Y_prices = create_dataset(data, look_back)
    X_prices = np.reshape(X_prices, (X_prices.shape[0], X_prices.shape[1], 1))
    X_issuers = np.reshape(X_issuers, (X_issuers.shape[0], 1))

    model = build_model(num_issuers=data['issuer_id'].nunique(), look_back=look_back)
    model.fit(
        [X_prices, X_issuers], Y_prices,
        epochs=epochs,
        batch_size=batch_size,
        verbose=1
    )
    model.save(model_path)
    print(f"Model saved at {model_path}")
    return model

def predict_for_future(issuer_name, look_back, days_ahead, model_name):
    model_path = get_model_path(model_name)
    data = load_data()

    if not os.path.exists(model_path):
        print(f"Model {model_name} not found. Training...")
        train_model(data, look_back=look_back, epochs=DEFAULT_EPOCHS, batch_size=DEFAULT_BATCH_SIZE, model_name=model_name)

    model = load_model(model_path)

    scaler = MinMaxScaler(feature_range=(0, 1))
    data['Цена на последна трансакција'] = scaler.fit_transform(data[['Цена на последна трансакција']])

    issuer_data = data[data['Издавач'] == issuer_name].reset_index(drop=True)
    if issuer_data.empty:
        return f"No data available for issuer {issuer_name}."

    issuer_id = issuer_data['issuer_id'].iloc[0]
    prices = issuer_data['Цена на последна трансакција'].values

    if len(prices) < look_back:
        return f"Not enough data for prediction for {days_ahead} days ahead."

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

@app.route('/predict', methods=['POST'])
def predict():

    data = request.get_json()
    issuer_name = data.get("issuer_name")
    period = data.get("period")

    if not issuer_name or not period:
        return jsonify({"status": "error", "message": "Missing 'issuer_name' or 'period'"}), 400

    model_map = {
        1: "model_1_day.h5",
        7: "model_1_week.h5",
        30: "model_1_month.h5"
    }
    model_name = model_map.get(period)

    if not model_name:
        return jsonify({"status": "error", "message": "Invalid period. Use 1, 7, or 30."}), 400

    predictions = predict_for_future(issuer_name, LOOK_BACK, period, model_name)

    if isinstance(predictions, str):
        return jsonify({"status": "error", "message": predictions}), 400

    return jsonify({"status": "success", "predictions": predictions.tolist()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5008, debug=True)
