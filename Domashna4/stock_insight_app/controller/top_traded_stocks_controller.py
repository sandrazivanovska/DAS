from flask import Blueprint, render_template
from Domashna4.stock_insight_app.services.top_traded_stocks_service import fetch_top_traded_stocks

top_traded_stocks_bp = Blueprint('top_traded_stocks', __name__)

@top_traded_stocks_bp.route('/top-traded-stocks', methods=['GET'])
def top_traded_stocks():

    try:
        data = fetch_top_traded_stocks()
        return render_template('top_traded_stocks.html', data=data)
    except Exception as e:
        return f"Грешка при scrap: {e}", 500
