from flask import Blueprint, render_template, request
from datetime import datetime
from Domashna4.stock_insight_app.services.predictive_analysis_service import get_predictions

predictive_analysis_bp = Blueprint('predictive_analysis', __name__)

@predictive_analysis_bp.route('/', methods=['GET', 'POST'])
def predictive_analysis():
    stock_name = request.args.get('stock') or request.form.get('stock')
    period = request.args.get('period') or request.form.get('period')
    error_message = None
    recommendations = {}
    graph_url = None
    predictions = None
    future_date = None
    future_price = None
    current_date = datetime.now().strftime('%Y-%m-%d')

    if stock_name and period:
        try:
            (
                predictions,
                recommendations,
                graph_url,
                future_price,
                future_date,
                error_message
            ) = get_predictions(stock_name, period)

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
        graph_url=graph_url,
        future_price=future_price
    )
