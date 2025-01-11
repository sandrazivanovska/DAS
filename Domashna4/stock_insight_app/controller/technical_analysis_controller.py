from flask import Blueprint, render_template, request
from Domashna4.stock_insight_app.services.technical_analysis_service import perform_technical_analysis
from Domashna4.stock_insight_app.services.technical_analysis_service import prepare_visualization_data

technical_analysis_bp = Blueprint('technical_analysis', __name__)

@technical_analysis_bp.route('/', methods=['GET', 'POST'])
def technical_analysis():
    print("Request received for technical analysis.")
    stock_name = request.form.get('stock') if request.method == 'POST' else request.args.get('stock')
    print(f"Stock name: {stock_name}")

    selected_period = request.form.get('period') if request.method == 'POST' else "1 ден"
    print(f"Selected period: {selected_period}")

    if not stock_name:
        return render_template('technical_analysis.html', error_message="Please provide a stock name.")

    analysis_results = perform_technical_analysis(stock_name, selected_period)
    print(f"Analysis results: {analysis_results}")

    return render_template(
        'technical_analysis.html',
        stock_name=stock_name,
        period=selected_period,
        data=analysis_results.get('data'),
        signal_counts=analysis_results.get('signal_counts'),
        final_recommendation=analysis_results.get('final_recommendation'),
    )


@technical_analysis_bp.route('/technical-visualizations', methods=['GET'])
def technical_visualizations():
    stock_symbol = request.args.get('stock')

    if not stock_symbol:
        return "Stock symbol is required.", 400

    visualization_data = prepare_visualization_data(stock_symbol)

    if "error" in visualization_data:
        return render_template('error.html', error_message=visualization_data["error"])

    return render_template(
        'technical_visualizations.html',
        stock_symbol=stock_symbol,
        data={
            "oscillators": visualization_data.get("oscillators"),
            "trend_data": visualization_data.get("trend_data")
        }
    )


