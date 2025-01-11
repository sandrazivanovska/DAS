import requests

def fetch_analysis_data(issuer_code):
    try:
        response = requests.get(
            'http://localhost:5003/api/sentiment-analysis',
            params={'issuer_code': issuer_code}
        )

        if response.status_code != 200:
            return {"status": "error", "message": response.json().get('message', 'Unknown error')}

        data = response.json().get('data', [])

        if not data:
            return {"status": "error", "message": "No data found for the given issuer code."}

        positive_count = len([item for item in data if item['Sentiment'] == 'Positive'])
        negative_count = len([item for item in data if item['Sentiment'] == 'Negative'])
        neutral_count = len([item for item in data if item['Sentiment'] == 'Neutral'])

        if neutral_count >= positive_count and neutral_count >= negative_count:
            recommendation = "HOLD"
        elif positive_count >= neutral_count and positive_count >= negative_count:
            recommendation = "BUY"
        elif negative_count >= neutral_count and negative_count >= positive_count:
            recommendation = "SELL"
        else:
            recommendation = "HOLD"

        return {
            "status": "success",
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "recommendation": recommendation,
        }
    except Exception as e:
        return {"status": "error", "message": f"Error fetching analysis data: {e}"}
