import os
from flask import Flask, render_template, request, g, flash
from flask_babel import Babel
from urllib.parse import urlparse
from smoobu_api import SmoobuAPI
from datetime import datetime, timedelta, date
from calendar import monthrange

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Load configuration
app.config.from_object('config')

# Initialize Smoobu API
smoobu_api = SmoobuAPI(app.config['SMOOBU_SETTINGS_CHANNEL_ID'], app.config['SMOOBU_API_KEY'])

def get_locale():
    return request.accept_languages.best_match(['en', 'de'])

babel = Babel(app, locale_selector=get_locale)

# Custom filter for month names
@app.template_filter('month_name')
def month_name_filter(month_number):
    return datetime(2000, month_number, 1).strftime('%B')

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

    # Get the current date or the date from the query parameters
    current_date = datetime.strptime(request.args.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date()

    # Calculate the start of the current week (Monday)
    start_of_week = current_date - timedelta(days=current_date.weekday())
    
    # Calculate the end of the next week (Sunday)
    end_of_next_week = start_of_week + timedelta(days=13)

    # Create a list of dates for two weeks
    two_week_dates = [start_of_week + timedelta(days=i) for i in range(14)]

    # Get unique apartment names
    apartments = list(set(booking['apartment_name'] for booking in bookings))
    apartments.sort()

    # Organize bookings by apartment and date
    calendar_data = {apartment: {d: [] for d in two_week_dates} for apartment in apartments}
    for booking in bookings:
        check_in = datetime.strptime(booking['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(booking['check_out'], '%Y-%m-%d').date()
        apartment = booking['apartment_name']
        
        if apartment in apartments:
            for d in two_week_dates:
                if check_in <= d < check_out and booking['guest_name'] != "Unknown Guest":
                    calendar_data[apartment][d].append(booking)

    # Calculate previous and next two weeks
    prev_two_weeks = start_of_week - timedelta(days=14)
    next_two_weeks = start_of_week + timedelta(days=14)

    return render_template('calendar_view.html', 
                           current_date=current_date,
                           two_week_dates=two_week_dates,
                           apartments=apartments,
                           calendar_data=calendar_data,
                           prev_two_weeks=prev_two_weeks,
                           next_two_weeks=next_two_weeks)

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
