from flask import Blueprint, request, jsonify
from Domashna4.microservices.technical_analysis_service.services.analysis_service import analyze_stock


analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        stock_symbol = data['stock_symbol']
        time_periods = data['time_periods']

        response = analyze_stock(stock_symbol, time_periods)
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
