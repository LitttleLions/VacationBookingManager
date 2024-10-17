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

    # Get the current year and month
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))

    # Get the first day of the month and the number of days in the month
    first_day = date(year, month, 1)
    _, num_days = monthrange(year, month)

    # Create a list of dates for the month
    month_dates = [date(year, month, day) for day in range(1, num_days + 1)]

    # Get unique apartment names
    apartments = list(set(booking['apartment_name'] for booking in bookings))
    apartments.sort()

    # Organize bookings by apartment and date
    calendar_data = {apartment: {d: [] for d in month_dates} for apartment in apartments}
    for booking in bookings:
        check_in = datetime.strptime(booking['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(booking['check_out'], '%Y-%m-%d').date()
        apartment = booking['apartment_name']
        
        if apartment in apartments:
            for d in month_dates:
                if check_in <= d < check_out:
                    calendar_data[apartment][d].append(booking)

    # Calculate previous and next month
    prev_month = date(year, month, 1) - timedelta(days=1)
    next_month = date(year, month, num_days) + timedelta(days=1)

    return render_template('calendar_view.html', 
                           year=year, 
                           month=month,
                           month_dates=month_dates,
                           apartments=apartments,
                           calendar_data=calendar_data,
                           prev_month=prev_month,
                           next_month=next_month)

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
