from flask import Blueprint, render_template
from Domashna4.stock_insight_app.model.db_singelton import DatabaseConnection

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    try:
        db = DatabaseConnection().connect()  # Singleton instance
        stocks = db.execute('''SELECT Издавач, "Цена на последна трансакција", Количина, "Вкупен промет во денари"
                                FROM stock_data ORDER BY Количина DESC LIMIT 10''').fetchall()
        return render_template('home.html', stocks=stocks)
    except Exception as e:
        return f"Error fetching data: {e}", 500
