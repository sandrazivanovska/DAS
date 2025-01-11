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

    import pandas as pd

    def fetch_data(self, stock_symbol, start_date, end_date):
        endpoint = f"{self.base_url}/fetch-data"
        payload = {
            "stock_symbol": stock_symbol,
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d')
        }

        try:
            print(f"Sending POST to {endpoint} with payload: {payload}")
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            print(f"Response received: {response.json()}")

            # Convert JSON response to DataFrame
            data = response.json()
            df = pd.DataFrame(data)
            return df
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            return {"error": f"Failed to connect to Technical Analysis Service: {str(e)}"}

    def calculate_indicators(self, data):
        endpoint = f"{self.base_url}/calculate-indicators"
        payload = {"data": data}

        try:
            print(f"Sending POST to {endpoint} with payload: {payload}")
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            print(f"Response received: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            return {"error": f"Failed to connect to Technical Analysis Service: {str(e)}"}
