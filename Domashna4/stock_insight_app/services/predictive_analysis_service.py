import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta
from Domashna4.stock_insight_app.utils.prediction_cache_utils import get_cached_predictions
from Domashna4.stock_insight_app.utils.database_utils import get_current_price_from_db
from Domashna4.stock_insight_app.utils.prediction_chart_utils import generate_prediction_chart


def get_predictions(stock_name, period):
    period_map = {
        "1_day": 1,
        "1_week": 7,
        "1_month": 30
    }

    if period not in period_map:
        raise ValueError("Invalid period value. Please select a valid period.")

    period_value = period_map[period]
    predictions = get_cached_predictions(stock_name, period_value)
    recommendations = {}
    graph_url = None
    future_date = None
    future_price = None
    error_message = None

    if predictions:
        current_price = get_current_price_from_db(stock_name)

        if current_price is not None:
            if period == "1_day":
                future_price = round(predictions[0], 2) if predictions else None
            elif period in ["1_week", "1_month"]:
                future_price = round(predictions[-1], 2) if predictions else None

            recommendations[period] = "BUY" if future_price > current_price else "SELL"

            future_date = (datetime.now() + timedelta(days=period_value)).strftime('%Y-%m-%d')

        # Fetch full predictions for chart generation
        full_predictions = get_cached_predictions(stock_name, 30)

        if full_predictions:
            graph_url = generate_prediction_chart(full_predictions)

    return predictions, recommendations, graph_url, future_price, future_date, error_message


