from flask import Flask
from Domashna4.stock_insight_app.controller.about_us_controller import about_us_bp
from Domashna4.stock_insight_app.controller.fundamental_analysis_controller import fundamental_analysis_bp
from Domashna4.stock_insight_app.controller.historical_informations_controller import historical_informations_bp
from Domashna4.stock_insight_app.controller.home_controller import home_bp
from Domashna4.stock_insight_app.controller.predictive_analysis_controller import predictive_analysis_bp
from Domashna4.stock_insight_app.controller.technical_analysis_controller import technical_analysis_bp
from Domashna4.stock_insight_app.controller.top_traded_stocks_controller import top_traded_stocks_bp


def create_app():
    app = Flask(__name__, template_folder='view/templates', static_folder='view/static')
    app.secret_key = "secret_key"

    app.register_blueprint(home_bp, url_prefix="/")
    app.register_blueprint(technical_analysis_bp, url_prefix="/technical-analysis")
    app.register_blueprint(fundamental_analysis_bp, url_prefix="/fundamental-analysis")
    app.register_blueprint(predictive_analysis_bp, url_prefix="/predictive-analysis")

    app.register_blueprint(historical_informations_bp, url_prefix="/historical-informations")
    app.register_blueprint(top_traded_stocks_bp, url_prefix="/")
    app.register_blueprint(about_us_bp, url_prefix="/")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)