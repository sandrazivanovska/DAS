class PredictionContext:
    def __init__(self, strategy):
        self.strategy = strategy

    def set_strategy(self, strategy):
        self.strategy = strategy

    def predict(self, issuer_name, look_back, days_ahead):
        return self.strategy.predict(issuer_name, look_back, days_ahead)
