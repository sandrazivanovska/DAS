import talib

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
