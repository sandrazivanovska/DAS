import requests

class ScrapingClient:
    def __init__(self, base_url="http://127.0.0.1:5006"):
        self.base_url = base_url

    def scrape(self):

        try:
            response = requests.post(f"{self.base_url}/scrape")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
