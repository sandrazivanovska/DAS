import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .abstract_filter import Filter


class DataFetchFilter(Filter):

    async def process(self, data_list):
        all_data = []
        async with aiohttp.ClientSession() as session:
            tasks = []
            for issuer, last_date in data_list:
                end_date = datetime.today().date()
                current_start = last_date
                while current_start <= end_date:
                    current_end = min(current_start + timedelta(days=365), end_date)
                    task = self.fetch_data(session, issuer, current_start, current_end)
                    tasks.append(task)
                    current_start = current_end + timedelta(days=1)

            results = await asyncio.gather(*tasks)
            for result in results:
                all_data.extend(result)
        return all_data

    async def fetch_data(self, session, issuer, start_date, end_date):
        url = f"https://www.mse.mk/en/stats/symbolhistory/{issuer}"
        params = {
            "FromDate": start_date.strftime("%m/%d/%Y"),
            "ToDate": end_date.strftime("%m/%d/%Y")
        }
        async with session.get(url, params=params) as response:
            if response.status == 200:
                html = await response.text()
                data = self.parse_table_data(html, issuer)
                if not data:
                    print(f"No data for {issuer} from {start_date} to {end_date}")
                return data
            else:
                print(f"Failed to fetch data for {issuer} from {start_date} to {end_date}")
                return []

    def parse_table_data(self, html, issuer):
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('div', class_='panel-body')
        if not table or not table.find('tbody'):
            return []

        data_rows = []
        for row in table.find('tbody').find_all('tr'):
            cells = row.find_all('td')
            if len(cells) < 9:
                continue

            volume = int(cells[6].text.strip().replace(',', '') or 0)
            if volume == 0:
                continue

            date = datetime.strptime(cells[0].text.strip(), '%m/%d/%Y').strftime('%Y-%m-%d')
            last_trade_price = "{:,.2f}".format(float(cells[1].text.strip().replace(',', '') or 0)).replace(",", "X").replace(".", ",").replace("X", ".")
            max_price = "{:,.2f}".format(float(cells[2].text.strip().replace(',', '') or 0)).replace(",", "X").replace(".", ",").replace("X", ".")
            min_price = "{:,.2f}".format(float(cells[3].text.strip().replace(',', '') or 0)).replace(",", "X").replace(".", ",").replace("X", ".")
            avg_price = "{:,.2f}".format(float(cells[4].text.strip().replace(',', '') or 0)).replace(",", "X").replace(".", ",").replace("X", ".")
            chg = "{:,.2f}".format(float(cells[5].text.strip().replace(',', '') or 0)).replace(",", "X").replace(".", ",").replace("X", ".")
            turnover_best = "{:,.2f}".format(float(cells[7].text.strip().replace(',', '') or 0)).replace(",", "X").replace(".", ",").replace("X", ".")
            turnover_denars = "{:,.2f}".format(float(cells[8].text.strip().replace(',', '') or 0)).replace(",", "X").replace(".", ",").replace("X", ".")

            data_rows.append((issuer, last_trade_price, max_price, min_price, avg_price, chg, volume, turnover_best, turnover_denars, date))

        return data_rows
