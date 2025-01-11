from flask import Blueprint, render_template

about_us_bp = Blueprint('about_us', __name__)

@about_us_bp.route('/about-us', methods=['GET'])
def about_us():

    return render_template('about_us.html')
