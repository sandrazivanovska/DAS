import locale
import requests
from bs4 import BeautifulSoup

def scrape_top_traded_stocks():

    url = "https://www.mse.mk/mk"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'table table-bordered table-condensed table-striped'})
    data = []

    if not table:
        raise ValueError("Table not found on the webpage.")

    for row in table.find_all('tr')[1:]:
        cells = row.find_all('td')
        if cells:
            try:
                issuer = cells[0].find('a').get_text(strip=True)
                avg_price = float(cells[1].text.strip().replace('.', '').replace(',', '.'))
                percent_change = float(cells[2].text.strip().replace(',', '.').replace('%', ''))
                total_turnover = float(cells[3].text.strip().replace('.', '').replace(',', '.'))
                avg_price = locale.format_string('%.2f', avg_price, grouping=True)
                total_turnover = locale.format_string('%.2f', total_turnover, grouping=True)
            except ValueError:
                avg_price = percent_change = total_turnover = None

            data.append({
                "issuer": issuer,
                "avg_price": avg_price,
                "percent_change": f"{percent_change}%" if percent_change is not None else "N/A",
                "total_turnover": total_turnover,
            })

    return data
