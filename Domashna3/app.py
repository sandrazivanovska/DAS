import locale

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request
import sqlite3
from analysis.technical import perform_technical_analysis
import sys
import os
from datetime import datetime, timedelta
locale.setlocale(locale.LC_ALL, 'mk_MK.UTF-8')


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = Flask(__name__)

def get_db_connection():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, '..', 'Domashna1', 'stock_data.db')
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection failed: {e}")
        raise

@app.route('/')
def home():
    conn = get_db_connection()
    stocks = conn.execute('''SELECT Издавач, "Цена на последна трансакција", Количина, "Вкупен промет во денари"
                             FROM stock_data ORDER BY Количина DESC LIMIT 10''').fetchall()
    conn.close()
    return render_template('home.html', stocks=stocks)


@app.route('/technical-analysis', methods=['GET', 'POST'])
def technical_analysis():
    data = None
    stock_name = None
    selected_period = None

    if request.method == 'POST':
        stock_name = request.form['stock']
        selected_period = request.form['period']

        conn = get_db_connection()
        analysis_results = perform_technical_analysis(stock_name, conn)
        conn.close()

        if analysis_results:
            data = analysis_results

    return render_template(
        'technical_analysis.html',
        stock_name=stock_name,
        period=selected_period,
        data=data
    )



# @app.route('/fundamental-analysis', methods=['GET', 'POST'])
# def fundamental_analysis():
#     data = None
#     stock_name = None
#
#     if request.method == 'POST':
#         stock_name = request.form['stock']
#         conn = get_db_connection()
#         financial_data_raw = conn.execute('''SELECT "Цена на последна трансакција", "Мак.", "Мин.", "Просечна цена", "Количина", "Промет во БЕСТ во денари", "Вкупен промет во денари"
#                                               FROM stock_data WHERE Издавач = ?''', (stock_name,)).fetchall()
#         conn.close()
#
#         financial_data = get_fundamental_metrics(financial_data_raw)
#
#         #This table will be properly implemented in the next assigment because it involves scraping news (now is just hard-coded)
#         data = {
#             "financial": financial_data,
#             "sentiment": [
#                 {"Датум": "2024-11-01", "News Title": "Good performance", "Source": "news.com", "Sentiment": "Positive", "Recommendation": "Buy"},
#                 {"Датум": "2024-11-02", "News Title": "Market uncertainty", "Source": "marketwatch.com", "Sentiment": "Neutral", "Recommendation": "Hold"}
#             ]
#         }
#
#     return render_template('fundamental_analysis.html', stock_name=stock_name, data=data)

# @app.route('/historical-informations', methods=['GET', 'POST'])
# def historical_informations():
#     data = []
#     stock_name = None
#     start_date = None
#     end_date = None
#
#     if request.method == 'POST':
#         stock_name = request.form.get('stock')
#         start_date = request.form.get('start_date')
#         end_date = request.form.get('end_date')
#
#         conn = get_db_connection()
#         data = get_historical_data(conn, stock_name, start_date, end_date)
#         conn.close()
#
#     return render_template('historical_informations.html', data=data, stock_name=stock_name, start_date=start_date, end_date=end_date)
#
#

def scrape_najtrguvani():
    url = "https://www.mse.mk/mk"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'table table-bordered table-condensed table-striped'})
    data = []
    for row in table.find_all('tr')[1:]:
        cells = row.find_all('td')
        if cells:
            try:
                issuer = cells[0].find('a').get_text(strip=True)
                avg_price = float(cells[1].text.strip().replace('.', '').replace(',', '.'))
                percent_change = float(cells[2].text.strip().replace(',', '.').replace('%', ''))
                total_turnover = float(cells[3].text.strip().replace('.', '').replace(',', '.'))
                # Форматирај ги бројките
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




@app.route('/top-traded-stocks')
def top_traded_stocks():
    try:
        # Повик до scrap функцијата
        najtrguvani_data = scrape_najtrguvani()
        return render_template('top_traded_stocks.html', data=najtrguvani_data)
    except Exception as e:
        return f"Грешка при scrap: {e}", 500

@app.route('/about-us')
def about_us():
    return render_template('about_us.html')

@app.route('/predictive-analysis')
def predictive_analysis():
    return render_template('predictive_analysis.html')

@app.route('/visualizations')
def visualizations():
    return render_template('visualizations.html')


if __name__ == '__main__':
    app.run(debug=True)
