from Domashna4.microservices.technical_analysis_service.utils.database_utils import fetch_data
from Domashna4.microservices.technical_analysis_service.utils.indicator_utils import calculate_indicators
from Domashna4.stock_insight_app.api_clients.technical_analysis_client import TechnicalAnalysisClient
from datetime import datetime, timedelta

client = TechnicalAnalysisClient(base_url="http://localhost:5001")

def perform_technical_analysis(stock_name, selected_period=None):
    periods = {'1 ден': 1, '1 недела': 7, '1 месец': 30}
    selected_period_days = periods.get(selected_period, 1)

    # Fetch analysis results from the microservice
    analysis_results = client.analyze(stock_name, periods)

    if not analysis_results or "error" in analysis_results:
        return {"error": analysis_results.get("error", "Analysis failed.")}

    # Extract data and calculate additional indicators if necessary
    if not analysis_results.get('trend_data'):
        df = fetch_data(stock_name, datetime.now() - timedelta(days=730), datetime.now())
        df = calculate_indicators(df)
        trend_data = {
            "dates": df.index.strftime('%Y-%m-%d').tolist(),
            "SMA_20": df["SMA_20"].fillna(0).tolist(),
            "EMA_20": df["EMA_20"].fillna(0).tolist(),
            "WMA_50": df["WMA_50"].fillna(0).tolist(),
        }
        analysis_results['trend_data'] = trend_data

    return {
        "data": analysis_results['results'].get(selected_period),
        "signal_counts": analysis_results.get("signal_counts"),
        "final_recommendation": analysis_results.get("final_recommendation"),
        "visualization_data": analysis_results.get("trend_data"),
    }

def prepare_visualization_data(stock_symbol):
    client = TechnicalAnalysisClient(base_url="http://localhost:5001")

    time_periods = {
        "1_day": 1,
        "1_week": 7,
        "1_month": 30
    }

    # Fetch data from the microservice
    analysis_results = client.analyze(stock_symbol, time_periods)

    if "error" in analysis_results:
        return {"error": analysis_results["error"]}

    # Extract oscillator values from analysis results
    results = analysis_results.get("results", {})
    oscillator_values = {
        period: {
            "RSI": results.get(period, {}).get("oscillators", {}).get("RSI", {}).get("value", 0),
            "MACD": results.get(period, {}).get("oscillators", {}).get("MACD", {}).get("value", 0),
            "STOCH_K": results.get(period, {}).get("oscillators", {}).get("STOCH_K", {}).get("value", 0),
        }
        for period in time_periods.keys()
    }

    # Use trend data from analysis_results if available
    trend_data = analysis_results.get("trend_data", {})
    if not trend_data:
        # If trend data is not available, raise an error or return an empty dataset
        return {"error": "Trend data not available in analysis results."}

    # Extract signal counts and final recommendation from analysis_results
    signal_counts = analysis_results.get("signal_counts", {})
    final_recommendation = analysis_results.get("final_recommendation", "HOLD")

    # Return the visualization-ready data
    return {
        "oscillators": oscillator_values,
        "trend_data": trend_data,
        "signal_counts": signal_counts,
        "final_recommendation": final_recommendation,
    }
