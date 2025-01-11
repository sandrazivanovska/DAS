import os

from flask import Blueprint, request, jsonify

import pandas as pd

from Domashna4.microservices.fundamental_analysis_service.services.sentiment_service import get_documents_by_issuer

analyze_bp = Blueprint("analyze", __name__)

@analyze_bp.route("/analyze_document", methods=["POST"])
def analyze_document():
    try:
        data = request.json
        issuer_code = data.get("issuer_code")
        if not issuer_code:
            return jsonify({"status": "error", "message": "Issuer code is required."}), 400

        documents = get_documents_by_issuer(issuer_code)
        if not documents:
            return jsonify({"status": "error", "message": f"No documents found for issuer {issuer_code}."}), 404

        return jsonify({"status": "success", "data": documents})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@analyze_bp.route("/api/sentiment-analysis", methods=["GET"])
def get_sentiment_data():
    try:
        issuer_code = request.args.get('issuer_code')
        if not issuer_code:
            return jsonify({"status": "error", "message": "Issuer code is required."}), 400

        csv_path = os.path.join(os.path.dirname(__file__), "../sentiment_analysis_results.csv")
        data = pd.read_csv(csv_path)

        print("CSV Columns:", data.columns)

        filtered_data = data[data['Company Code'] == issuer_code]

        if filtered_data.empty:
            return jsonify({"status": "error", "message": f"No data found for issuer {issuer_code}."}), 404

        return jsonify({"status": "success", "data": filtered_data.to_dict(orient='records')})
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

