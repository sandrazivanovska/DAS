import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from flask import Blueprint, render_template, request, session, redirect, url_for
from Domashna4.stock_insight_app.services.fundamental_analysis_service import fetch_analysis_data
from Domashna4.stock_insight_app.utils.fundamental_chart_utils import generate_bar_chart, generate_filtered_line_chart
from Domashna4.stock_insight_app.utils.csv_utils import read_documents_from_csv

# Create the Blueprint
fundamental_analysis_bp = Blueprint('fundamental_analysis', __name__)

@fundamental_analysis_bp.route('/', methods=['GET', 'POST'])
def fundamental_analysis():
    result = None
    error_message = None
    chart_url = None

    issuer_code = request.args.get('stock') or request.form.get('issuer_code')

    if issuer_code:
        session['selected_issuer_code'] = issuer_code

        try:
            analysis_data = fetch_analysis_data(issuer_code)

            if analysis_data["status"] == "success":
                positive_count = analysis_data["positive_count"]
                negative_count = analysis_data["negative_count"]
                neutral_count = analysis_data["neutral_count"]
                recommendation = analysis_data["recommendation"]

                chart_url = generate_bar_chart(positive_count, negative_count, neutral_count)

                result = {
                    "issuer_code": issuer_code,
                    "positive_count": positive_count,
                    "negative_count": negative_count,
                    "neutral_count": neutral_count,
                    "recommendation": recommendation,
                }
            else:
                error_message = analysis_data.get("message", "Error retrieving data.")
        except Exception as e:
            error_message = f"An error occurred: {e}"
    elif request.method == 'POST' and not issuer_code:
        error_message = "Please provide a valid issuer code."

    return render_template(
        'fundamental_analysis.html',
        result=result,
        error_message=error_message,
        chart_url=chart_url
    )

@fundamental_analysis_bp.route('/visualizations', methods=['GET', 'POST'])
def visualizations_fundamental():
    chart_url = None
    error_message = None

    selected_issuer_code = session.get('selected_issuer_code')

    if request.method == 'POST':
        try:
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')

            data = read_documents_from_csv('../../microservices/fundamental_analysis_service/sentiment_analysis_results.csv', selected_issuer_code)

            chart_url = generate_filtered_line_chart(data, selected_issuer_code, start_date, end_date)
        except Exception as e:
            error_message = f"Error generating chart: {e}"

    return render_template(
        'visualizations_fundamental.html',
        chart_url=chart_url,
        issuer_code=selected_issuer_code,
        error_message=error_message
    )
