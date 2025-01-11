from Domashna4.stock_insight_app.utils.scraping_top_traded_utils import scrape_top_traded_stocks

def fetch_top_traded_stocks():
    """
    Fetches top traded stocks using the scraping utility.
    """
    try:
        return scrape_top_traded_stocks()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch top traded stocks: {e}")
