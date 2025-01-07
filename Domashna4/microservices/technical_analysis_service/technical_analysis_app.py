from flask import Flask, request, jsonify
import pandas as pd
import talib
from datetime import datetime, timedelta
import sqlite3
import os

app = Flask(__name__)

def fetch_data(stock_symbol, start_date, end_date):

    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, '../..', 'stock_data.db')
    conn = sqlite3.connect(db_path)

    query = '''
    SELECT Датум, "Цена на последна трансакција", "Мак.", "Мин.", Количина
    FROM stock_data
    WHERE Издавач = ? AND Датум BETWEEN ? AND ?
    ORDER BY Датум ASC
    '''
    df = pd.read_sql_query(query, conn, params=(stock_symbol, start_date, end_date))
    conn.close()

    df['Датум'] = pd.to_datetime(df['Датум'])
    df.set_index('Датум', inplace=True)

    for col in ['Цена на последна трансакција', 'Мак.', 'Мин.']:
        df[col] = df[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)

    return df.sort_index()

def calculate_indicators(df):

    high, low, close = df['Мак.'], df['Мин.'], df['Цена на последна трансакција']

    indicators = {
        'RSI': talib.RSI(close, timeperiod=14),
        'STOCH_K': talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)[0],
        'MACD': talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)[0],
        'CCI': talib.CCI(high, low, close, timeperiod=14),
        'WILLR': talib.WILLR(high, low, close, timeperiod=14),
        'SMA_20': talib.SMA(close, timeperiod=20),
        'EMA_20': talib.EMA(close, timeperiod=20),
        'WMA_50': talib.WMA(close, timeperiod=50),
        'TRIMA_50': talib.TRIMA(close, timeperiod=50),
        'KAMA_30': talib.KAMA(close, timeperiod=30)
    }

    for key, values in indicators.items():
        df[key] = values

    return df

def generate_signals(df):

    oscillators = ['RSI', 'CCI', 'WILLR', 'STOCH_K', 'MACD']
    for osc in oscillators:
        df[f'{osc}_SIGNAL'] = df[osc].apply(
            lambda value: 'SELL' if value > 70 else 'BUY' if value < 30 else 'HOLD'
        )

    moving_averages = ['SMA_20', 'EMA_20', 'WMA_50', 'TRIMA_50', 'KAMA_30']
    for ma in moving_averages:
        df[f'{ma}_SIGNAL'] = df.apply(
            lambda row: 'BUY' if row['Цена на последна трансакција'] > row[ma]
            else 'SELL' if row['Цена на последна трансакција'] < row[ma]
            else 'HOLD',
            axis=1
        )

    return df

@app.route('/analyze', methods=['POST'])
def analyze():

    try:
        data = request.json
        stock_symbol = data['stock_symbol']
        time_periods = data['time_periods']

        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)

        df = fetch_data(stock_symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        if df.empty:
            return jsonify({"error": "No data available for the specified stock and date range."}), 404

        df = generate_signals(calculate_indicators(df))

        results = {}
        signal_counts = {"BUY": 0, "SELL": 0, "HOLD": 0}

        for period_name, days in time_periods.items():
            period_data = df.tail(days)
            if period_data.empty:
                results[period_name] = {"error": f"No data available for the last {days} days."}
            else:
                oscillators = {
                    osc: {
                        "value": round(period_data[osc].mean(), 2),
                        "signal": period_data[f'{osc}_SIGNAL'].mode()[0]
                    } for osc in ['RSI', 'CCI', 'WILLR', 'STOCH_K', 'MACD']
                }

                moving_averages = {
                    ma: {
                        "value": round(period_data[ma].mean(), 2),
                        "signal": period_data[f'{ma}_SIGNAL'].mode()[0]
                    } for ma in ['SMA_20', 'EMA_20', 'WMA_50', 'TRIMA_50', 'KAMA_30']
                }

                for signal in oscillators.values():
                    signal_counts[signal["signal"]] += 1

                for signal in moving_averages.values():
                    signal_counts[signal["signal"]] += 1

                results[period_name] = {
                    "oscillators": oscillators,
                    "moving_averages": moving_averages
                }

        if signal_counts["BUY"] > signal_counts["SELL"]:
            final_recommendation = "BUY"
        elif signal_counts["SELL"] > signal_counts["BUY"]:
            final_recommendation = "SELL"
        else:
            final_recommendation = "HOLD"

        return jsonify({
            "results": results,
            "signal_counts": signal_counts,
            "final_recommendation": final_recommendation
        })

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
