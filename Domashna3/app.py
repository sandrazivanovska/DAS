import csv
import locale
import pandas as pd
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
from Domashna3.analysis.historical_analysis import get_historical_data
import sys
import os
from analysis.prediction import load_data, get_predictions
import matplotlib.pyplot as plt
import io
import base64
import matplotlib.ticker as mticker
from analysis.technical_analysis import *


locale.setlocale(locale.LC_ALL, 'mk_MK.UTF-8')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = Flask(__name__)
app.secret_key = "secret_key"

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
        stock_name = request.form.get('stock')
        selected_period = request.form.get('period')

    elif request.method == 'GET':
        stock_name = request.args.get('stock')
        selected_period = "1 ден"

    if stock_name:
        conn = get_db_connection()

        periods = {
            '1 ден': 1,
            '1 недела': 7,
            '1 месец': 30
        }

        analysis_results = analyze_stock(conn, stock_name, periods)
        conn.close()

        if analysis_results:
            data = analysis_results.get(selected_period)

    return render_template(
        'technical_analysis.html',
        stock_name=stock_name,
        period=selected_period,
        data=data
    )



def prepare_visualization_data(connection, stock_symbol):
    time_periods = {
        "1_day": 1,
        "1_week": 7,
        "1_month": 30
    }

    analysis_results = analyze_stock(connection, stock_symbol, time_periods)

    if "error" in analysis_results:
        return {"error": analysis_results["error"]}

    oscillator_values = {
        period: {
            "RSI": analysis_results[period]["oscillator_summary"]["RSI"]["value"],
            "MACD": analysis_results[period]["oscillator_summary"]["MACD"]["value"],
            "STOCH_K": analysis_results[period]["oscillator_summary"]["STOCH_K"]["value"],
        }
        for period in time_periods.keys()
    }

    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    data = fetch_data(connection, stock_symbol, start_date, end_date)
    data = calculate_indicators(data)

    trend_data = {
        "dates": data.index.strftime('%Y-%m-%d').tolist(),
        "SMA_20": data["SMA_20"].fillna(0).tolist(),
        "EMA_20": data["EMA_20"].fillna(0).tolist(),
        "WMA_20": data["WMA_50"].fillna(0).tolist(),
    }

    return {
        "oscillators": oscillator_values,
        "trend_data": trend_data,
    }



@app.route('/technical-visualizations', methods=['GET'])
def technical_visualizations():
    stock_symbol = request.args.get('stock', None)
    if not stock_symbol:
        return "Stock symbol is required.", 400

    conn = get_db_connection()

    visualization_data = prepare_visualization_data(conn, stock_symbol)
    conn.close()

    if "error" in visualization_data:
        return render_template('error.html', error_message=visualization_data["error"])

    return render_template(
        'technical_visualizations.html',
        data=visualization_data,
        stock_symbol=stock_symbol
    )


CSV_FILE_PATH = "sentiment_analysis_results.csv"

def read_documents_from_csv(file_path, issuer_code):

    try:
        data = pd.read_csv(file_path, encoding='latin1')
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')  # Convert dates
        filtered_data = data[data['Company Code'] == issuer_code]
        return filtered_data
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return pd.DataFrame()

def generate_bar_chart(positive_count, negative_count, neutral_count):
    # Rearrange the order so Neutral is in the middle
    labels = ['Positive', 'Neutral', 'Negative']
    values = [positive_count, neutral_count, negative_count]

    plt.figure(figsize=(8, 6))
    plt.bar(labels, values, color=['#5D6D7E', '#A9A9A9', '#2874A6'])  # Neutral is gray
    plt.title("Sentiment Analysis Results")
    plt.ylabel("Number of Articles")
    plt.xlabel("Sentiment")
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    return chart_url


def generate_line_chart(data, issuer_code):

    filtered_data = data[data['Company Code'] == issuer_code]
    sentiment_over_time = filtered_data.groupby(['Date', 'Sentiment']).size().unstack(fill_value=0)

    plt.figure(figsize=(10, 6))
    for sentiment in sentiment_over_time.columns:
        plt.plot(sentiment_over_time.index, sentiment_over_time[sentiment], label=sentiment, marker='o')

    plt.title(f"Sentiment Over Time for {issuer_code}", fontsize=16)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Number of Articles", fontsize=12)
    plt.legend(title="Sentiment")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    return chart_url

@app.route('/fundamental-analysis', methods=['GET', 'POST'])
def fundamental_analysis():
    result = None
    error_message = None
    chart_url = None

    issuer_code = request.args.get('stock') or request.form.get('issuer_code')

    if issuer_code:
        session['selected_issuer_code'] = issuer_code

        documents = read_documents_from_csv(CSV_FILE_PATH, issuer_code)

        if documents.empty:
            error_message = f"No documents found for issuer {issuer_code}."
        else:
            positive_count = (documents['Sentiment'] == "Positive").sum()
            negative_count = (documents['Sentiment'] == "Negative").sum()
            neutral_count = (documents['Sentiment'] == "Neutral").sum()

            # Determine Recommendation Based on Counts
            if neutral_count >= positive_count and neutral_count >= negative_count:
                recommendation = "HOLD"
            elif positive_count >= neutral_count and positive_count >= negative_count:
                recommendation = "BUY"
            elif negative_count >= neutral_count and negative_count >= positive_count:
                recommendation = "SELL"
            else:
                recommendation = "HOLD"  # Default recommendation if counts are equal

            chart_url = generate_bar_chart(positive_count, negative_count, neutral_count)

            result = {
                "issuer_code": issuer_code,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "neutral_count": neutral_count,
                "recommendation": recommendation,
            }

    elif request.method == 'POST' and not issuer_code:
        error_message = "Please provide a valid issuer code."

    return render_template(
        'fundamental_analysis.html',
        result=result,
        error_message=error_message,
        chart_url=chart_url
    )


def generate_filtered_line_chart(data, issuer_code, start_date, end_date):

    filtered_data = data[(data['Company Code'] == issuer_code) &
                         (data['Date'] >= start_date) &
                         (data['Date'] <= end_date)]

    if filtered_data.empty:
        raise ValueError(f"No data found for issuer {issuer_code} in the given date range.")

    sentiment_over_time = filtered_data.groupby(['Date', 'Sentiment']).size().unstack(fill_value=0)

    plt.figure(figsize=(10, 6))
    for sentiment in sentiment_over_time.columns:
        plt.plot(sentiment_over_time.index, sentiment_over_time[sentiment], label=sentiment, marker='o')

    plt.title(f"Sentiment Over Time for {issuer_code} ({start_date.date()} to {end_date.date()})", fontsize=16)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Number of Articles", fontsize=12)
    plt.legend(title="Sentiment")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    return chart_url

@app.route('/visualizations_fundamental', methods=['GET', 'POST'])
def visualizations_fundamental():
    selected_issuer_code = session.get('selected_issuer_code')
    data = read_documents_from_csv(CSV_FILE_PATH,  selected_issuer_code )
    chart_url = None
    error_message = None

    if not selected_issuer_code:
        return redirect(url_for('fundamental_analysis'))

    if request.method == 'POST':
        try:
            start_date = pd.Timestamp(request.form.get('start_date'))
            end_date = pd.Timestamp(request.form.get('end_date'))
            chart_url = generate_filtered_line_chart(data, selected_issuer_code, start_date, end_date)
        except Exception as e:
            error_message = f"Error generating chart: {e}"

    return render_template(
        'visualizations_fundamental.html',
        chart_url=chart_url,
        issuer_code=selected_issuer_code,
        error_message=error_message
    )



@app.route('/historical-informations', methods=['GET', 'POST'])
def historical_informations():
    data = []
    chart_data = {}
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

        # Prepare data for the chart
        if data:
            chart_data = {
                "dates": [row["Датум"] for row in data],
                "last_prices": [
                    float(row["Цена на последна трансакција"].replace('.', '').replace(',', '.'))
                    for row in data
                ],
                "max_prices": [
                    float(row["Мак."].replace('.', '').replace(',', '.'))
                    for row in data
                ],
                "min_prices": [
                    float(row["Мин."].replace('.', '').replace(',', '.'))
                    for row in data
                ],
            }

    return render_template(
        'historical_informations.html',
        data=data,
        chart_data=chart_data,
        stock_name=stock_name,
        start_date=start_date,
        end_date=end_date
    )


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

        najtrguvani_data = scrape_najtrguvani()
        return render_template('top_traded_stocks.html', data=najtrguvani_data)
    except Exception as e:
        return f"Грешка при scrap: {e}", 500

@app.route('/about-us')
def about_us():
    return render_template('about_us.html')

def get_current_price_from_db(stock_name):
    conn = get_db_connection()
    query = '''
        SELECT "Цена на последна трансакција"
        FROM stock_data
        WHERE Издавач = ?
        ORDER BY Датум DESC
        LIMIT 1
    '''
    result = conn.execute(query, (stock_name,)).fetchone()
    conn.close()
    if result:
        raw_price = result[0]
        try:

            normalized_price = float(raw_price.replace('.', '').replace(',', '.'))
            return normalized_price
        except ValueError:
            raise ValueError(f"Invalid price format in database: {raw_price}")
    return None


@app.route('/predictive-analysis', methods=['GET', 'POST'])
def predictive_analysis():
    predictions = None
    stock_name = request.args.get('stock')
    error_message = None
    recommendations = {}
    graph_url = None
    period = None
    current_date = datetime.now().strftime('%Y-%m-%d')
    future_date = None

    if request.method == 'POST':
        stock_name = request.form.get('stock')
        period = request.form.get('period')

        if not stock_name:
            error_message = "Please enter a valid issuer."
        else:
            try:
                current_price = get_current_price_from_db(stock_name)
                if current_price is None:
                    error_message = "Could not retrieve the current price from the database."
                else:
                    predictions = get_predictions(stock_name)
                    if predictions:
                        future_price = predictions.get(period)
                        if future_price:
                            recommendations[period] = "BUY" if future_price > current_price else "SELL"
                            if period == "1_day":
                                future_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                            elif period == "1_week":
                                future_date = (datetime.now() + timedelta(weeks=1)).strftime('%Y-%m-%d')
                            elif period == "1_month":
                                future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

                        dates = ['1 Day', '1 Week', '1 Month']
                        values = [
                            predictions["1_day"],
                            predictions["1_week"],
                            predictions["1_month"]
                        ]

                        plt.figure(figsize=(10, 5))
                        plt.plot(dates, values, marker='o', label='Predicted Prices')
                        plt.fill_between(
                            dates,
                            [val * 0.95 for val in values],
                            [val * 1.05 for val in values],
                            color='blue',
                            alpha=0.2,
                            label='Confidence Interval (95%)'
                        )
                        plt.title(f'Predictions for {stock_name}')
                        plt.xlabel('Time Period')
                        plt.ylabel('Price (USD)')
                        plt.legend()
                        plt.grid()

                        buf = io.BytesIO()
                        plt.savefig(buf, format='png')
                        buf.seek(0)
                        graph_url = base64.b64encode(buf.getvalue()).decode('utf8')
                        buf.close()
                        plt.close()
            except Exception as e:
                error_message = f"Error during prediction: {e}"

    return render_template(
        'predictive_analysis.html',
        stock_name=stock_name,
        predictions=predictions,
        error_message=error_message,
        recommendations=recommendations,
        period=period,
        current_date=current_date,
        future_date=future_date,
        graph_url=graph_url
    )

@app.route('/visualizations')
def visualizations():
    return render_template('visualizations.html')


if __name__ == '__main__':
    app.run(debug=True)
