import os
from flask import Flask, render_template, request, g, flash
from flask_babel import Babel
from urllib.parse import urlparse
from smoobu_api import SmoobuAPI
from datetime import datetime, timedelta, date

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
    bookings, error = smoobu_api.get_bookings()
    if error:
        flash(error, 'error')
    
    if not bookings:
        flash("No bookings available at the moment. The Smoobu API might be undergoing maintenance. Please try again later.", 'warning')
    
    guest_filter = request.args.get('guest_filter', '').lower()
    apartment_filter = request.args.get('apartment_filter', '').lower()
    date_filter = request.args.get('date_filter', date.today().strftime('%Y-%m-%d'))
    
    filtered_bookings = []
    current_date = date.today()
    for booking in bookings:
        if booking['type'].lower() == 'cancellation':
            continue
        
        if guest_filter and guest_filter not in booking['guest_name'].lower():
            continue
        
        if apartment_filter and apartment_filter not in booking['apartment_name'].lower():
            continue
        
        booking_end_date = datetime.strptime(booking['check_out'], '%Y-%m-%d').date()
        if booking_end_date < current_date:
            continue
        
        filtered_bookings.append(booking)
    
    filtered_bookings.sort(key=lambda x: datetime.strptime(x['check_in'], '%Y-%m-%d'))
    
    return render_template('booking_list.html', bookings=filtered_bookings, 
                           guest_filter=guest_filter, 
                           apartment_filter=apartment_filter, 
                           date_filter=date_filter)

@app.route('/calendar')
def calendar_view():
    bookings, error = smoobu_api.get_bookings()
    if error:
        flash(error, 'error')
    return render_template('calendar_view.html', bookings=bookings)

@app.route('/print')
def print_view():
    bookings, error = smoobu_api.get_bookings()
    if error:
        flash(error, 'error')
    return render_template('print_view.html', bookings=bookings)

@app.context_processor
def inject_debug():
    return dict(debug=app.debug)

@app.context_processor
def inject_get_locale():
    return dict(get_locale=get_locale)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
