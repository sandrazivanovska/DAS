import locale
import traceback
from datetime import datetime, timedelta
import pandas as pd
import requests
from bs4 import BeautifulSoup
from flask import session, redirect, url_for
import sqlite3
import sys
import os
import matplotlib.pyplot as plt
import io
import base64
import matplotlib.ticker as mticker
from flask import Flask, request, render_template
from Domashna4.client_services.prediction_client import PredictionClient
from Domashna4.client_services.scraping_client import ScrapingClient
from Domashna4.client_services.technical_analysis_client import TechnicalAnalysisClient
from Domashna4.microservices.technical_analysis_service.technical_analysis_app import fetch_data, calculate_indicators
from Domashna4.client_services.fundamental_analysis_client import  FundamentalAnalysisClient

locale.setlocale(locale.LC_ALL, 'mk_MK.UTF-8')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = Flask(__name__)
app.secret_key = "secret_key"


def get_db_connection():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'stock_data.db')
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


client = TechnicalAnalysisClient(base_url="http://localhost:5001")

@app.route('/technical-analysis', methods=['GET', 'POST'])
def technical_analysis():
    data = None
    stock_name = None
    selected_period = None
    signal_counts = None
    final_recommendation = None

    if request.method == 'POST':
        stock_name = request.form.get('stock')
        selected_period = request.form.get('period')

    elif request.method == 'GET':
        stock_name = request.args.get('stock')
        selected_period = "1 ден"

    if stock_name:
        periods = {
            '1 ден': 1,
            '1 недела': 7,
            '1 месец': 30
        }

        analysis_results = client.analyze(stock_name, periods)

        if analysis_results and 'results' in analysis_results:
            data = analysis_results['results'].get(selected_period)
            signal_counts = analysis_results.get('signal_counts')
            final_recommendation = analysis_results.get('final_recommendation')

    return render_template(
        'technical_analysis.html',
        stock_name=stock_name,
        period=selected_period,
        data=data,
        signal_counts=signal_counts,
        final_recommendation=final_recommendation
    )


def prepare_visualization_data(stock_symbol, client):

    time_periods = {
        "1_day": 1,
        "1_week": 7,
        "1_month": 30
    }

    analysis_results = client.analyze(stock_symbol, time_periods)

    if "error" in analysis_results:
        return {"error": analysis_results["error"]}

    results = analysis_results.get("results", {})
    oscillator_values = {
        period: {
            "RSI": results.get(period, {}).get("oscillators", {}).get("RSI", {}).get("value", 0),
            "MACD": results.get(period, {}).get("oscillators", {}).get("MACD", {}).get("value", 0),
            "STOCH_K": results.get(period, {}).get("oscillators", {}).get("STOCH_K", {}).get("value", 0),
        }
        for period in time_periods.keys()
    }

    trend_data = analysis_results.get("trend_data", {})
    connection = get_db_connection()
    if not trend_data:
        df = fetch_data(stock_symbol, datetime.now() - timedelta(days=730), datetime.now())
        df = calculate_indicators(df)
        trend_data = {
            "dates": df.index.strftime('%Y-%m-%d').tolist(),
            "SMA_20": df["SMA_20"].fillna(0).tolist(),
            "EMA_20": df["EMA_20"].fillna(0).tolist(),
            "WMA_50": df["WMA_50"].fillna(0).tolist()
        }

    signal_counts = analysis_results.get("signal_counts", {})
    final_recommendation = analysis_results.get("final_recommendation", "HOLD")

    return {
        "oscillators": oscillator_values,
        "trend_data": trend_data,
        "signal_counts": signal_counts,
        "final_recommendation": final_recommendation,
    }

@app.route('/technical-visualizations', methods=['GET'])
def technical_visualizations():

    stock_symbol = request.args.get('stock', None)

    if not stock_symbol:
        return "Stock symbol is required.", 400

    client = TechnicalAnalysisClient(base_url="http://localhost:5001")

    visualization_data = prepare_visualization_data(stock_symbol, client)

    if "error" in visualization_data:
        return render_template('error.html', error_message=visualization_data["error"])

    return render_template(
        'technical_visualizations.html',
        data=visualization_data,
        stock_symbol=stock_symbol
    )


CSV_FILE_PATH = "microservices/fundamental_analysis_service/sentiment_analysis_results.csv"

def read_documents_from_csv(file_path, issuer_code):

    try:
        data = pd.read_csv(file_path, encoding='latin1')
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        filtered_data = data[data['Company Code'] == issuer_code]
        return filtered_data
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return pd.DataFrame()

def generate_bar_chart(positive_count, negative_count, neutral_count):
    labels = ['Positive', 'Neutral', 'Negative']
    values = [positive_count, neutral_count, negative_count]

    plt.figure(figsize=(8, 6))
    plt.bar(labels, values, color=['#5D6D7E', '#A9A9A9', '#2874A6'])
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
    client = FundamentalAnalysisClient()  # Initialize the client
    result = None
    error_message = None
    chart_url = None

    issuer_code = request.args.get('stock') or request.form.get('issuer_code')

    if issuer_code:
        session['selected_issuer_code'] = issuer_code

        try:
            response = client.fetch_fundamental_analysis(issuer_code)
            if response["status"] == "success":
                documents = response["data"]
                positive_count = sum(1 for doc in documents if doc["Sentiment"] == "Positive")
                negative_count = sum(1 for doc in documents if doc["Sentiment"] == "Negative")
                neutral_count = sum(1 for doc in documents if doc["Sentiment"] == "Neutral")

                if neutral_count >= positive_count and neutral_count >= negative_count:
                    recommendation = "HOLD"
                elif positive_count >= neutral_count and positive_count >= negative_count:
                    recommendation = "BUY"
                elif negative_count >= neutral_count and negative_count >= positive_count:
                    recommendation = "SELL"
                else:
                    recommendation = "HOLD"

                chart_url = generate_bar_chart(positive_count, negative_count, neutral_count)

                result = {
                    "issuer_code": issuer_code,
                    "positive_count": positive_count,
                    "negative_count": negative_count,
                    "neutral_count": neutral_count,
                    "recommendation": recommendation,
                }
            else:
                error_message = response.get("message", "Error retrieving data from the microservice.")
        except Exception as e:
            error_message = f"An error occurred while contacting the microservice: {e}"
            print(f"Error: {traceback.format_exc()}")
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
    client = FundamentalAnalysisClient()  # Initialize the client
    selected_issuer_code = session.get('selected_issuer_code')
    chart_url = None
    error_message = None

    if not selected_issuer_code:
        return redirect(url_for('fundamental_analysis'))

    result = client.fetch_fundamental_analysis(selected_issuer_code)

    if result["status"] == "success":
        data = result["data"]
        df = pd.DataFrame(data)
    else:
        error_message = result["message"]
        df = pd.DataFrame()

    if request.method == 'POST' and not df.empty:
        try:
            start_date = pd.Timestamp(request.form.get('start_date'))
            end_date = pd.Timestamp(request.form.get('end_date'))

            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

            filtered_df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

            chart_url = generate_filtered_line_chart(filtered_df, selected_issuer_code, start_date, end_date)
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

        if stock_name and start_date and end_date:
            try:
                conn = get_db_connection()

                query = '''
                    SELECT Датум, "Цена на последна трансакција", "Мак.", "Мин.", "Просечна цена", "%пром.", "Количина", "Промет во БЕСТ во денари", "Вкупен промет во денари"
                    FROM stock_data
                    WHERE Издавач = ? AND Датум BETWEEN ? AND ?
                    ORDER BY Датум
                '''
                data = conn.execute(query, (stock_name, start_date, end_date)).fetchall()

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

                conn.close()
            except Exception as e:
                print(f"Error fetching data: {e}")
                if conn:
                    conn.close()

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


# Кеш структура
cache = {}
cache_expiry = {}
prediction_client = PredictionClient(base_url="http://localhost:5008")

def get_cached_predictions(stock_name, period, force_refresh=False):
    cache_key = f"{stock_name}_{period}"
    if not force_refresh and cache_key in cache and datetime.now() < cache_expiry.get(cache_key, datetime.min):
        print(f"Cache hit for {cache_key}")
        return cache[cache_key]
    else:
        print(f"Cache miss for {cache_key}. Fetching from microservice...")
        try:
            response = prediction_client.get_prediction(stock_name, period)
            if "error" not in response:
                predictions = response.get("predictions")
                cache[cache_key] = predictions
                cache_expiry[cache_key] = datetime.now() + timedelta(hours=24)
                return predictions
            else:
                raise Exception(response["error"])
        except Exception as e:
            print(f"Error fetching predictions: {e}")
            raise

@app.route('/predictive-analysis', methods=['GET', 'POST'])
def predictive_analysis():
    predictions = None
    stock_name = request.args.get('stock') or request.form.get('stock')
    error_message = None
    recommendations = {}
    graph_url = None
    period = request.args.get('period') or request.form.get('period')
    current_date = datetime.now().strftime('%Y-%m-%d')
    future_date = None
    future_price = None

    period_map = {
        "1_day": 1,
        "1_week": 7,
        "1_month": 30
    }

    if stock_name and period:
        try:
            period_value = period_map.get(period)
            if not period_value:
                raise ValueError("Invalid period value. Please select a valid period.")

            predictions = get_cached_predictions(stock_name, period_value)

            if predictions:
                current_price = get_current_price_from_db(stock_name)

                if current_price is not None:
                    if period == "1_day":
                        future_price = round(predictions[0], 2) if predictions else None
                    elif period == "1_week":
                        future_price = round(predictions[-1],
                                             2) if predictions else None
                    elif period == "1_month":
                        future_price = round(predictions[-1],
                                             2) if predictions else None
                    else:
                        future_price = None

                    recommendations[period] = "BUY" if future_price > current_price else "SELL"

                    if period == "1_day":
                        future_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                    elif period == "1_week":
                        future_date = (datetime.now() + timedelta(weeks=1)).strftime('%Y-%m-%d')
                    elif period == "1_month":
                        future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')



                    full_predictions = get_cached_predictions(stock_name, 30)

                    if full_predictions:
                        one_day_prediction = full_predictions[0] if len(full_predictions) > 0 else None
                        one_week_prediction = full_predictions[6] if len(full_predictions) > 6 else None
                        one_month_prediction = full_predictions[29] if len(full_predictions) > 29 else None

                        dates = ['1 Day', '1 Week', '1 Month']
                        values = [
                            round(one_day_prediction, 2) if one_day_prediction else None,
                            round(one_week_prediction, 2) if one_week_prediction else None,
                            round(one_month_prediction, 2) if one_month_prediction else None
                        ]

                        valid_dates = [date for date, value in zip(dates, values) if value is not None]
                        valid_values = [value for value in values if value is not None]

                        plt.figure(figsize=(10, 5))
                        plt.plot(valid_dates, valid_values, marker='o', color='blue', label='Predicted Prices',
                                 zorder=5)
                        plt.fill_between(
                            valid_dates,
                            [val * 0.95 for val in valid_values],
                            [val * 1.05 for val in valid_values],
                            color='blue',
                            alpha=0.2,
                            label='Confidence Interval (95%)'
                        )
                        plt.title(f'Predictions for {stock_name}')
                        plt.xlabel('Time Period')
                        plt.ylabel('Price (USD)')
                        plt.xticks(rotation=45)
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
        period=str(period),
        current_date=current_date,
        future_date=future_date,
        graph_url=graph_url,
        future_price=future_price
    )


scraping_client = ScrapingClient()

if __name__ == '__main__':
    if os.getenv('WERKZEUG_RUN_MAIN') == 'true':
        print("Starting scraping process during app creation...")
        result = scraping_client.scrape()
        if result.get("status") == "success":
            print("Scraping completed successfully!")
        else:
            print(f"Scraping failed: {result.get('message')}")

    app.run(debug=True)