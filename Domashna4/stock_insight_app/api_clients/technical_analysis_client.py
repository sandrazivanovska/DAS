import pandas as pd
import requests

class TechnicalAnalysisClient:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url

    def analyze(self, stock_symbol, time_periods):
        endpoint = f"{self.base_url}/analyze"
        payload = {
            "stock_symbol": stock_symbol,
            "time_periods": time_periods
        }

        try:
            print(f"Sending POST to {endpoint} with payload: {payload}")
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            print(f"Response received: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            return {"error": f"Failed to connect to Technical Analysis Service: {str(e)}"}

