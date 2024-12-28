import pandas as pd
import talib
from datetime import datetime, timedelta


def fetch_data(connection, stock_symbol, start_date, end_date):
    query = '''SELECT Датум, "Цена на последна трансакција", "Мак.", "Мин.", Количина
               FROM stock_data
               WHERE Издавач = ? AND Датум BETWEEN ? AND ?
               ORDER BY Датум ASC'''
    df = pd.read_sql_query(query, connection, params=(
        stock_symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))

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


def summarize_period(df, indicators, signals):
    summary = {
        "oscillator_summary": {
            osc: {
                "value": round(df[osc].mean(), 2),
                "signal": df[f'{osc}_SIGNAL'].mode()[0]
            } for osc in ['RSI', 'CCI', 'WILLR', 'STOCH_K', 'MACD']
        },
        "moving_average_summary": {
            ma: {
                "value": round(df[ma].mean(), 2),
                "signal": df[f'{ma}_SIGNAL'].mode()[0]
            } for ma in ['SMA_20', 'EMA_20', 'WMA_50', 'TRIMA_50', 'KAMA_30']
        }
    }
    return summary


def analyze_stock(connection, stock_symbol, time_periods):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)

    data = fetch_data(connection, stock_symbol, start_date, end_date)
    if data.empty:
        return {"error": "No data available for the specified stock and date range."}

    data = generate_signals(calculate_indicators(data))

    def calculate_recommendation(period_data):
        summary = summarize_period(period_data, data, data)
        signal_counts = {signal: sum(
            osc['signal'] == signal for osc in summary['oscillator_summary'].values()
        ) + sum(
            ma['signal'] == signal for ma in summary['moving_average_summary'].values()
        ) for signal in ['BUY', 'SELL', 'HOLD']}
        summary['signal_counts'] = signal_counts
        summary['final_recommendation'] = (
            max(signal_counts, key=signal_counts.get)
            if signal_counts['BUY'] != signal_counts['SELL'] else 'HOLD'
        )
        return summary

    results = {
        period_name: (
            calculate_recommendation(data.tail(days))
            if not data.tail(days).empty else
            {"error": f"No data available for the last {days} days."}
        )
        for period_name, days in time_periods.items()
    }

    return results