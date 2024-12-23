import pandas as pd
import talib
from datetime import datetime, timedelta

def perform_technical_analysis(stock_name, conn):
    # Опсег на датуми
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    # Читање податоци од базата
    query = '''SELECT Датум, "Цена на последна трансакција", "Мак.", "Мин.", Количина
               FROM stock_data
               WHERE Издавач = ? AND Датум BETWEEN ? AND ?
               ORDER BY Датум ASC'''
    stock_data = pd.read_sql_query(query, conn, params=(stock_name, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))

    if stock_data.empty:
        return None

    # Форматирање на податоците
    stock_data['Датум'] = pd.to_datetime(stock_data['Датум'])
    stock_data.set_index('Датум', inplace=True)
    stock_data['Цена на последна трансакција'] = stock_data['Цена на последна трансакција'].apply(
        lambda x: float(x.replace('.', '').replace(',', '.')))
    stock_data['Мак.'] = stock_data['Мак.'].apply(lambda x: float(x.replace('.', '').replace(',', '.')))
    stock_data['Мин.'] = stock_data['Мин.'].apply(lambda x: float(x.replace('.', '').replace(',', '.')))

    # Проверка за доволно податоци
    if len(stock_data) < 50:
        return None

    # Пресметка на технички индикатори
    prices = stock_data['Цена на последна трансакција']
    high = stock_data['Мак.']
    low = stock_data['Мин.']

    stock_data['RSI'] = talib.RSI(prices, timeperiod=14)
    stock_data['MACD'], _, stock_data['MACD_hist'] = talib.MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9)
    stock_data['%K'], _ = talib.STOCH(high, low, prices, fastk_period=14, slowk_period=3, slowd_period=3)
    stock_data['Williams_%R'] = talib.WILLR(high, low, prices, timeperiod=14)
    stock_data['CCI'] = talib.CCI(high, low, prices, timeperiod=14)
    stock_data['SMA_20'] = talib.SMA(prices, timeperiod=20)
    stock_data['EMA_20'] = talib.EMA(prices, timeperiod=20)
    stock_data['SMA_50'] = talib.SMA(prices, timeperiod=50)
    stock_data['EMA_50'] = talib.EMA(prices, timeperiod=50)
    stock_data['BB_middle'] = talib.BBANDS(prices, timeperiod=20)[1]

    # Функција за генерирање на сигнал
    def generate_signal(indicator, value):
        if indicator == 'RSI':
            return 'Buy' if value < 30 else 'Sell' if value > 70 else 'Hold'
        elif indicator == 'MACD':
            return 'Buy' if value > 0 else 'Sell'
        elif indicator == 'Stochastic Oscillator':
            return 'Buy' if value < 20 else 'Sell' if value > 80 else 'Hold'
        elif indicator == 'Williams_%R':
            return 'Buy' if value < -80 else 'Sell' if value > -20 else 'Hold'
        elif indicator == 'CCI':
            return 'Buy' if value < -100 else 'Sell' if value > 100 else 'Hold'
        else:
            return 'Hold'

    # Подготовка на резултати
    latest_data = stock_data.tail(1).iloc[0]
    oscillators = {
        "RSI": (latest_data['RSI'], generate_signal('RSI', latest_data['RSI'])),
        "MACD": (latest_data['MACD'], generate_signal('MACD', latest_data['MACD'])),
        "Stochastic Oscillator": (latest_data['%K'], generate_signal('Stochastic Oscillator', latest_data['%K'])),
        "Williams %R": (latest_data['Williams_%R'], generate_signal('Williams_%R', latest_data['Williams_%R'])),
        "CCI": (latest_data['CCI'], generate_signal('CCI', latest_data['CCI']))
    }
    moving_averages = {
        "SMA 20": (latest_data['SMA_20'], "Buy" if latest_data['SMA_20'] > latest_data['Цена на последна трансакција'] else "Sell"),
        "EMA 20": (latest_data['EMA_20'], "Buy" if latest_data['EMA_20'] > latest_data['Цена на последна трансакција'] else "Sell"),
        "SMA 50": (latest_data['SMA_50'], "Buy" if latest_data['SMA_50'] > latest_data['Цена на последна трансакција'] else "Sell"),
        "EMA 50": (latest_data['EMA_50'], "Buy" if latest_data['EMA_50'] > latest_data['Цена на последна трансакција'] else "Sell"),
        "Bollinger Bands (Middle)": (latest_data['BB_middle'], "Hold")
    }

    # Генерирање на финален препорака
    all_recommendations = [rec for _, rec in oscillators.values()] + [rec for _, rec in moving_averages.values()]
    final_recommendation = max(set(all_recommendations), key=all_recommendations.count)

    return {
        "oscillators": oscillators,
        "moving_averages": moving_averages,
        "final_recommendation": final_recommendation
    }
