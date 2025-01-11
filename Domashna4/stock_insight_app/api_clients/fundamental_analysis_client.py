import requests

class FundamentalAnalysisClient:
    def __init__(self, base_url="http://localhost:5003"):

        self.base_url = base_url

    def fetch_fundamental_analysis(self, issuer_code):

        try:
            payload = {"issuer_code": issuer_code}
            response = requests.post(f"{self.base_url}/analyze_document", json=payload)

            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                return {
                    "status": "success",
                    "data": data.get("data", []),
                    "message": None
                }
            else:
                return {
                    "status": "error",
                    "data": [],
                    "message": data.get("message", "Unknown error from the microservice.")
                }

        except requests.exceptions.HTTPError as http_err:
            return {
                "status": "error",
                "data": [],
                "message": f"HTTP error occurred: {http_err}"
            }

        except requests.exceptions.ConnectionError as conn_err:
            return {
                "status": "error",
                "data": [],
                "message": f"Connection error occurred: {conn_err}"
            }

        except requests.exceptions.Timeout as timeout_err:
            return {
                "status": "error",
                "data": [],
                "message": f"Timeout error occurred: {timeout_err}"
            }

        except requests.exceptions.RequestException as req_err:
            return {
                "status": "error",
                "data": [],
                "message": f"An error occurred: {req_err}"
            }
