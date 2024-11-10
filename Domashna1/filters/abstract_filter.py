from abc import ABC, abstractmethod

class Filter(ABC):
    @abstractmethod
    def process(self, data_list):
        pass

    def __init__(self):
        super().__init__()


