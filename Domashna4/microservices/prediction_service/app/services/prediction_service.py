from Domashna4.microservices.prediction_service.app.strategies.lstm_strategy import LSTMPredictionStrategy

def predict_with_strategy(issuer_name, period):
    strategy = LSTMPredictionStrategy()
    return strategy.predict(issuer_name, period)
