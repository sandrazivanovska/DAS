from flask import Flask, render_template, request
import sqlite3
from analysis.technical import calculate_rsi, calculate_macd, calculate_ema, calculate_sma, calculate_stochastic, get_signal, calculate_signal
from analysis.fundamental import get_fundamental_metrics
from analysis.historical import get_historical_data
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = Flask(__name__)

def get_db_connection():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, '../..', 'Domashna1', 'stock_data.db')
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
    if request.method == 'POST':
        stock_name = request.form['stock']
        conn = get_db_connection()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=35)
        stock_data = conn.execute('''SELECT Датум, "Цена на последна трансакција"
                                     FROM stock_data WHERE Издавач = ? AND Датум BETWEEN ? AND ? ORDER BY Датум ASC''',
                                  (stock_name, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchall()
        conn.close()

        prices = [float(row["Цена на последна трансакција"].replace('.', '').replace(',', '.')) for row in stock_data]
        dates = [row["Датум"] for row in stock_data]

        if prices:
            rsi_value = calculate_rsi(prices)
            macd_value, signal_value = calculate_macd(prices)
            ema_50 = calculate_ema(prices, 50)[-1]
            sma_100 = calculate_sma(prices, 100)
            stochastic_value = calculate_stochastic(prices)

            summary_indicators = [
                {"name": "RSI", "1_day": calculate_signal(prices, dates, start_date, 1), "1_week": calculate_signal(prices, dates, start_date, 7), "1_month": calculate_signal(prices, dates, start_date, 30)},
                {"name": "MACD", "1_day": calculate_signal(prices, dates, start_date, 1), "1_week": calculate_signal(prices, dates, start_date, 7), "1_month": calculate_signal(prices, dates, start_date, 30)},
                {"name": "EMA (50)", "1_day": calculate_signal(prices, dates, start_date, 1), "1_week": calculate_signal(prices, dates, start_date, 7), "1_month": calculate_signal(prices, dates, start_date, 30)},
                {"name": "SMA (100)", "1_day": calculate_signal(prices, dates, start_date, 1), "1_week": calculate_signal(prices, dates, start_date, 7), "1_month": calculate_signal(prices, dates, start_date, 30)},
                {"name": "Stochastic Oscillator", "1_day": calculate_signal(prices, dates, start_date, 1), "1_week": calculate_signal(prices, dates, start_date, 7), "1_month": calculate_signal(prices, dates, start_date, 30)},
            ]

            data = {
                "calculated_indicators": [
                    {"name": "RSI", "value": round(rsi_value, 2), "signal": get_signal(rsi_value)},
                    {"name": "MACD", "value": round(macd_value, 2), "signal": get_signal(macd_value)},
                    {"name": "EMA (50)", "value": round(ema_50, 2), "signal": get_signal(ema_50)},
                    {"name": "SMA (100)", "value": round(sma_100, 2), "signal": get_signal(sma_100)},
                    {"name": "Stochastic Oscillator", "value": f"{round(stochastic_value, 2)}%", "signal": get_signal(stochastic_value)},
                ],
                "summary_indicators": summary_indicators,
            }
        else:
            data = None

    return render_template('technical_analysis.html', stock_name=stock_name, data=data)

@app.route('/fundamental-analysis', methods=['GET', 'POST'])
def fundamental_analysis():
    data = None
    stock_name = None

    if request.method == 'POST':
        stock_name = request.form['stock']
        conn = get_db_connection()
        financial_data_raw = conn.execute('''SELECT "Цена на последна трансакција", "Мак.", "Мин.", "Просечна цена", "Количина", "Промет во БЕСТ во денари", "Вкупен промет во денари"
                                              FROM stock_data WHERE Издавач = ?''', (stock_name,)).fetchall()
        conn.close()

        financial_data = get_fundamental_metrics(financial_data_raw)

        #This table will be properly implemented in the next assigment because it involves scraping news (now is just hard-coded)
        data = {
            "financial": financial_data,
            "sentiment": [
                {"Датум": "2024-11-01", "News Title": "Good performance", "Source": "news.com", "Sentiment": "Positive", "Recommendation": "Buy"},
                {"Датум": "2024-11-02", "News Title": "Market uncertainty", "Source": "marketwatch.com", "Sentiment": "Neutral", "Recommendation": "Hold"}
            ]
        }

    return render_template('fundamental_analysis.html', stock_name=stock_name, data=data)

@app.route('/historical-informations', methods=['GET', 'POST'])
def historical_informations():
    data = []
    stock_name = None
    start_date = None
    end_date = None

    if request.method == 'POST':
        stock_name = request.form.get('stock')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        conn = get_db_connection()
        data = get_historical_data(conn, stock_name, start_date, end_date)
        conn.close()

    return render_template('historical_informations.html', data=data, stock_name=stock_name, start_date=start_date, end_date=end_date)

@app.route('/top-traded-stocks')
def top_traded_stocks():
    conn = get_db_connection()
    # SQL query to get the top 10 traded stocks sorted by quantity
    data = conn.execute('''
        SELECT Издавач, AVG("Просечна цена") AS avg_price, 
               AVG("%пром.") AS percent_change, 
               SUM("Промет во БЕСТ во денари") AS total_turnover
        FROM stock_data
        GROUP BY Издавач
        ORDER BY total_turnover DESC
        LIMIT 10
    ''').fetchall()
    conn.close()
    return render_template('top_traded_stocks.html', data=data)

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
