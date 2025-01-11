from flask import Blueprint, render_template, request
from Domashna4.stock_insight_app.services.historical_informations_service import fetch_historical_data

historical_informations_bp = Blueprint('historical_informations', __name__)

@historical_informations_bp.route('/', methods=['GET', 'POST'])
def historical_informations():
    data = []
    chart_data = {}
    stock_name = None
    start_date = None
    end_date = None
    error_message = None

    if request.method == 'POST':
        stock_name = request.form.get('stock')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        if stock_name and start_date and end_date:
            try:
                data, chart_data = fetch_historical_data(stock_name, start_date, end_date)
            except Exception as e:
                error_message = f"Error fetching data: {e}"

    return render_template(
        'historical_informations.html',
        data=data,
        chart_data=chart_data,
        stock_name=stock_name,
        start_date=start_date,
        end_date=end_date,
        error_message=error_message
    )
