import requests

class PredictionClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_prediction(self, stock_name, period):
        url = f"{self.base_url}/predict"
        try:
            response = requests.post(url, json={"issuer_name": stock_name, "period": period})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with the prediction service: {e}")
            return {"error": str(e)}
