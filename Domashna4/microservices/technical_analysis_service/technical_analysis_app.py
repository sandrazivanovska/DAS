from flask import Flask
from routes.analysis_routes import analysis_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(analysis_bp, url_prefix='/')
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001)
