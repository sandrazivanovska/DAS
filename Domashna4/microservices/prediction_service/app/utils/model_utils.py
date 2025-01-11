import os
import sqlite3

import pandas as pd
from tensorflow.keras.layers import Input, LSTM, Dense, Embedding, Flatten, concatenate
from tensorflow.keras.models import Model
from sklearn.preprocessing import MinMaxScaler
import numpy as np

def get_model_path(model_name):
    return os.path.join("lstm_models", model_name)

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


def load_data():

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../..', 'stock_data.db')

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