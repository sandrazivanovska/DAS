import requests
from bs4 import BeautifulSoup
from .abstract_filter import Filter

class IssuerFilter(Filter):

    def get_issuers(self):
        url = 'https://www.mse.mk/en/stats/symbolhistory/REPL'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        issuers = [option.get('value') for option in soup.find_all('option') if
                   option.get('value') and not any(char.isdigit() for char in option.get('value'))]

        return issuers

    def process(self, data_list):
        return self.get_issuers()


