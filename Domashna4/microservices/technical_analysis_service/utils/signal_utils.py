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
