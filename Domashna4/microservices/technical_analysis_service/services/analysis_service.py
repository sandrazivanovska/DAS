from datetime import datetime, timedelta
from Domashna4.microservices.technical_analysis_service.utils.database_utils import fetch_data
from Domashna4.microservices.technical_analysis_service.utils.indicator_utils import calculate_indicators
from Domashna4.microservices.technical_analysis_service.utils.signal_utils import generate_signals

def analyze_stock(stock_symbol, time_periods):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)

    df = fetch_data(stock_symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    if df.empty:
        return {"error": "No data available for the specified stock and date range."}

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

    return {
        "results": results,
        "signal_counts": signal_counts,
        "final_recommendation": final_recommendation
    }
