from abc import ABC, abstractmethod

class PredictionStrategy(ABC):
    @abstractmethod
    def predict(self, issuer_name, look_back, days_ahead):
        pass
