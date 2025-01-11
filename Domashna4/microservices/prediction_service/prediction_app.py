from flask import Flask
from app.routes.prediction_routes import prediction_bp

app = Flask(__name__)
app.register_blueprint(prediction_bp, url_prefix='/predict')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5008, debug=True)
