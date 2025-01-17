from lstm_strategy import LSTMPredictionStrategy

def predict_with_strategy(issuer_name, period):
    strategy = LSTMPredictionStrategy()
    return strategy.predict(issuer_name, period)
