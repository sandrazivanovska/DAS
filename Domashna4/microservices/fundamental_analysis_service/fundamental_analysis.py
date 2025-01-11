from flask import Flask
from routes.analyze_routes import analyze_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(analyze_bp, url_prefix='/')
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5003)
