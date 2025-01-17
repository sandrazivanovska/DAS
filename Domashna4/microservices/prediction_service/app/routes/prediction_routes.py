from flask import Blueprint, request, jsonify
from prediction_service import predict_with_strategy

prediction_bp = Blueprint('prediction', __name__)

@prediction_bp.route('', methods=['POST'])
def predict():
    data = request.get_json()
    issuer_name = data.get("issuer_name")
    period = data.get("period")

    if not issuer_name or not period:
        return jsonify({"status": "error", "message": "Missing 'issuer_name' or 'period'"}), 400

    try:
        predictions = predict_with_strategy(issuer_name, period)
        response = {
            "status": "success",
            "predictions": predictions["predictions"]
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
