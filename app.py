import os
from flask import Flask, render_template, request, g, flash
from flask_babel import Babel
from urllib.parse import urlparse
from smoobu_api import SmoobuAPI

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Load configuration
app.config.from_object('config')

# Initialize Smoobu API
smoobu_api = SmoobuAPI(app.config['SMOOBU_SETTINGS_CHANNEL_ID'], app.config['SMOOBU_API_KEY'])

def get_locale():
    return request.accept_languages.best_match(['en', 'de'])

babel = Babel(app, locale_selector=get_locale)

@app.route('/')
def booking_list():
    bookings = smoobu_api.get_bookings()
    if not bookings:
        flash('Error fetching bookings. Please try again later.', 'error')
    
    filter_query = request.args.get('filter', '').lower()
    if filter_query:
        bookings = [b for b in bookings if filter_query in b['guest_name'].lower() or filter_query in b['apartment_name'].lower()]
    
    return render_template('booking_list.html', bookings=bookings)

@app.route('/calendar')
def calendar_view():
    bookings = smoobu_api.get_bookings()
    return render_template('calendar_view.html', bookings=bookings)

@app.route('/print')
def print_view():
    bookings = smoobu_api.get_bookings()
    return render_template('print_view.html', bookings=bookings)

@app.context_processor
def inject_debug():
    return dict(debug=app.debug)

@app.context_processor
def inject_get_locale():
    return dict(get_locale=get_locale)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
