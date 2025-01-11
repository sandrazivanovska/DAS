from Domashna4.microservices.fundamental_analysis_service.utils.csv_utils import read_csv_file
from Domashna4.microservices.fundamental_analysis_service.utils.sentiment_utils import classify_sentiment


def analyze_sentiment(document):

    return classify_sentiment(document["Content"])


def get_documents_by_issuer(issuer_code):

    documents = read_csv_file()
    return [doc for doc in documents if doc["Company Code"] == issuer_code]
