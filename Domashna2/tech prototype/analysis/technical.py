# analysis/technical.py
from datetime import timedelta
from datetime import datetime


def calculate_signal(prices, dates, start_date, period_days):

    target_date = start_date + timedelta(days=period_days)  # Датумот после специфичен период
    filtered_prices = [p for d, p in zip(dates, prices) if datetime.strptime(d, '%Y-%m-%d') <= target_date]

    if len(filtered_prices) < 2:
        return "N/A"  # Недоволно податоци

    latest_price = filtered_prices[-1]
    previous_price = filtered_prices[0]

    if latest_price > previous_price:
        return "Buy"
    elif latest_price < previous_price:
        return "Sell"
    else:
        return "Hold"

def calculate_rsi(prices, period=14):
    gains = [max(prices[i] - prices[i - 1], 0) for i in range(1, len(prices))]
    losses = [abs(min(prices[i] - prices[i - 1], 0)) for i in range(1, len(prices))]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(prices, short_period=12, long_period=26, signal_period=9):
    short_ema = calculate_ema(prices, short_period)
    long_ema = calculate_ema(prices, long_period)
    macd = [s - l for s, l in zip(short_ema, long_ema)]
    signal = calculate_ema(macd, signal_period)
    return macd[-1], signal[-1]

def calculate_ema(prices, period):
    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]
    for price in prices[period:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])
    return ema

def calculate_sma(prices, period):
    return sum(prices[-period:]) / period

def calculate_stochastic(prices, period=14):
    lowest_low = min(prices[-period:])
    highest_high = max(prices[-period:])
    current_close = prices[-1]
    return ((current_close - lowest_low) / (highest_high - lowest_low)) * 100

def get_signal(value):
    if value > 70:
        return "Sell"
    elif value < 30:
        return "Buy"
    else:
        return "Hold"
