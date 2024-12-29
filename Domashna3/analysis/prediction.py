import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from keras.layers import Flatten
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential, Model, load_model
from tensorflow.keras.layers import Input, Embedding, LSTM, Dense, concatenate

def get_model_path(model_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, model_name)

def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path_new = os.path.join(base_dir, '../..', 'Domashna1', 'stock_data.db')
    conn = sqlite3.connect(db_path_new)

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

def train_model(data, look_back, epochs, batch_size, model_path):
    scaler = MinMaxScaler(feature_range=(0, 1))
    data['Цена на последна трансакција'] = scaler.fit_transform(data[['Цена на последна трансакција']])

    X_prices, X_issuers, Y_prices = create_dataset(data, look_back)
    X_prices = np.reshape(X_prices, (X_prices.shape[0], X_prices.shape[1], 1))
    X_issuers = np.reshape(X_issuers, (X_issuers.shape[0], 1))

    X_prices_train, X_prices_val, X_issuers_train, X_issuers_val, Y_prices_train, Y_prices_val = train_test_split(
        X_prices, X_issuers, Y_prices, test_size=0.3, random_state=42
    )

    model = build_model(num_issuers=data['issuer_id'].nunique(), look_back=look_back)
    history = model.fit(
        [X_prices_train, X_issuers_train], Y_prices_train,
        validation_data=([X_prices_val, X_issuers_val], Y_prices_val),
        epochs=epochs,
        batch_size=batch_size,
        verbose=1
    )

    model.save(model_path)

    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Training and Validation Loss')
    plt.legend()
    plt.show()

    return model, scaler

def train_model_for_1_day(data, look_back=60, epochs=20, batch_size=32):
    return train_model(data, look_back, epochs, batch_size, get_model_path('model_1_day.h5'))

def train_model_for_1_week(data, look_back=60, epochs=20, batch_size=32):
    return train_model(data, look_back, epochs, batch_size, get_model_path('model_1_week.h5'))

def train_model_for_1_month(data, look_back=60, epochs=20, batch_size=32):
    return train_model(data, look_back, epochs, batch_size, get_model_path('model_1_month.h5'))

def load_fresh_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path_new = os.path.join(base_dir, '../..', 'Domashna1', 'stock_data.db')
    conn = sqlite3.connect(db_path_new)
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

def predict_for_future(issuer_name, look_back, days_ahead, model_path):
    data = load_fresh_data()

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

def get_predictions(issuer_name):
    prediction_1_day = predict_for_future(
        issuer_name=issuer_name,
        look_back=60,
        days_ahead=1,
        model_path=get_model_path('../lstm_models/model_1_day.h5')
    )
    prediction_1_week = predict_for_future(
        issuer_name=issuer_name,
        look_back=60,
        days_ahead=7,
        model_path=get_model_path('../lstm_models/model_1_week.h5')
    )
    prediction_1_month = predict_for_future(
        issuer_name=issuer_name,
        look_back=60,
        days_ahead=30,
        model_path=get_model_path('../lstm_models/model_1_month.h5')
    )

    if isinstance(prediction_1_day, str):
        return {
            "1_day": prediction_1_day,
            "1_week": "N/A",
            "1_month": "N/A"
        }

    return {
        "1_day": prediction_1_day[-1],
        "1_week": prediction_1_week[-1] if len(prediction_1_week) > 0 else "N/A",
        "1_month": prediction_1_month[-1] if len(prediction_1_month) > 0 else "N/A"
    }
