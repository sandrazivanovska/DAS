from datetime import datetime, timedelta
from Domashna4.stock_insight_app.api_clients.prediction_client import PredictionClient

cache = {}
cache_expiry = {}
prediction_client = PredictionClient(base_url="http://localhost:5008")

def get_cached_predictions(stock_name, period, force_refresh=False):
    cache_key = f"{stock_name}_{period}"
    if not force_refresh and cache_key in cache and datetime.now() < cache_expiry.get(cache_key, datetime.min):
        print(f"Cache hit for {cache_key}")
        return cache[cache_key]

    print(f"Cache miss for {cache_key}. Fetching from microservice...")
    try:
        response = prediction_client.get_prediction(stock_name, period)
        if "error" not in response:
            predictions = response.get("predictions")
            cache[cache_key] = predictions
            cache_expiry[cache_key] = datetime.now() + timedelta(hours=24)
            return predictions
        else:
            raise Exception(response["error"])
    except Exception as e:
        print(f"Error fetching predictions: {e}")
        raise
