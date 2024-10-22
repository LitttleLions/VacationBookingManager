import logging
from flask import Flask, render_template, request, flash, g
from flask_babel import Babel, gettext as _
from datetime import datetime, timedelta, date
from smoobu_api import SmoobuAPI
from config import SMOOBU_SETTINGS_CHANNEL_ID, SMOOBU_API_KEY, BABEL_DEFAULT_LOCALE, BABEL_DEFAULT_TIMEZONE

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a real secret key
app.config['BABEL_DEFAULT_LOCALE'] = BABEL_DEFAULT_LOCALE
app.config['BABEL_DEFAULT_TIMEZONE'] = BABEL_DEFAULT_TIMEZONE

babel = Babel(app)
smoobu_api = SmoobuAPI(SMOOBU_SETTINGS_CHANNEL_ID, SMOOBU_API_KEY)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_locale():
    return request.args.get('lang', 'en')

babel.init_app(app, locale_selector=get_locale)

def filter_bookings(bookings, guest_filter, apartment_filter, start_date_filter, end_date_filter):
    filtered_bookings = []
    for booking in bookings:
        if (guest_filter.lower() in booking['guest_name'].lower() and
            (apartment_filter == '' or apartment_filter.lower() == booking['apartment_name'].lower()) and
            (not start_date_filter or booking['check_out'] >= start_date_filter) and
            (not end_date_filter or booking['check_in'] <= end_date_filter) and
            booking['guest_name'] != "Unknown Guest"):
            filtered_bookings.append(booking)
    return filtered_bookings

def fetch_and_filter_bookings(guest_filter='', apartment_filter='', start_date_filter='', end_date_filter=''):
    bookings, error = smoobu_api.get_bookings()
    if error:
        logger.error(f"Error fetching bookings: {error}")
        return [], error

    logger.debug(f"Retrieved {len(bookings)} bookings from Smoobu API")
    if bookings:
        earliest_date = min(booking['check_in'] for booking in bookings)
        latest_date = max(booking['check_out'] for booking in bookings)
        logger.debug(f"Date range of bookings: from {earliest_date} to {latest_date}")

    filtered_bookings = filter_bookings(bookings, guest_filter, apartment_filter, start_date_filter, end_date_filter)
    logger.debug(f"Filtered bookings: {len(filtered_bookings)} out of {len(bookings)}")

    return filtered_bookings, None

@app.route('/')
def booking_list():
    logger.debug("Entering booking_list function")
    guest_filter = request.args.get('guest_filter', '')
    apartment_filter = request.args.get('apartment_filter', '')
    start_date_filter = request.args.get('start_date_filter', '')
    end_date_filter = request.args.get('end_date_filter', '')

    logger.debug(f"Filters applied - Guest: {guest_filter}, Apartment: {apartment_filter}, Start Date: {start_date_filter}, End Date: {end_date_filter}")

    filtered_bookings, error = fetch_and_filter_bookings(guest_filter, apartment_filter, start_date_filter, end_date_filter)
    if error:
        flash(error, 'error')
        filtered_bookings = []

    all_bookings, _ = smoobu_api.get_bookings()
    apartments = sorted(set(booking['apartment_name'] for booking in all_bookings))

    return render_template('booking_list.html', bookings=filtered_bookings,
                           guest_filter=guest_filter,
                           apartment_filter=apartment_filter,
                           start_date_filter=start_date_filter,
                           end_date_filter=end_date_filter,
                           apartments=apartments)

@app.route('/calendar')
def calendar_view():
    logger.debug("Entering calendar_view function")
    guest_filter = request.args.get('guest_filter', '')
    apartment_filter = request.args.get('apartment_filter', '')
    start_date_filter = request.args.get('start_date_filter', '')
    end_date_filter = request.args.get('end_date_filter', '')

    current_date = datetime.strptime(request.args.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
    week_start = current_date - timedelta(days=current_date.weekday())
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    week_number = week_start.isocalendar()[1]

    filtered_bookings, error = fetch_and_filter_bookings(guest_filter, apartment_filter, start_date_filter, end_date_filter)
    if error:
        flash(error, 'error')
        filtered_bookings = []

    all_bookings, _ = smoobu_api.get_bookings()
    apartments = sorted(set(booking['apartment_name'] for booking in all_bookings))

    calendar_data = {apartment: {date: [] for date in week_dates} for apartment in apartments}

    for booking in filtered_bookings:
        check_in = datetime.strptime(booking['check_in'], '%Y-%m-%d')
        check_out = datetime.strptime(booking['check_out'], '%Y-%m-%d')
        for date in week_dates:
            if check_in <= date < check_out:
                calendar_data[booking['apartment_name']][date].append(booking)

    apartments_with_bookings = [apartment for apartment in apartments if any(calendar_data[apartment].values())]

    prev_week = (week_start - timedelta(weeks=1)).strftime('%Y-%m-%d')
    next_week = (week_start + timedelta(weeks=1)).strftime('%Y-%m-%d')

    today = date.today()

    return render_template('calendar_view.html',
                           apartments=apartments_with_bookings,
                           calendar_data=calendar_data,
                           week_dates=week_dates,
                           week_number=week_number,
                           current_date=current_date,
                           prev_week=prev_week,
                           next_week=next_week,
                           guest_filter=guest_filter,
                           apartment_filter=apartment_filter,
                           start_date_filter=start_date_filter,
                           end_date_filter=end_date_filter,
                           today=today)

@app.route('/print')
def print_view():
    logger.debug("Entering print_view function")
    guest_filter = request.args.get('guest_filter', '')
    apartment_filter = request.args.get('apartment_filter', '')
    start_date_filter = request.args.get('start_date_filter', '')
    end_date_filter = request.args.get('end_date_filter', '')

    filtered_bookings, error = fetch_and_filter_bookings(guest_filter, apartment_filter, start_date_filter, end_date_filter)
    if error:
        flash(error, 'error')
        filtered_bookings = []

    all_bookings, _ = smoobu_api.get_bookings()
    apartments = sorted(set(booking['apartment_name'] for booking in all_bookings))

    logger.debug(f"Filtered bookings for print view: {len(filtered_bookings)}")

    return render_template('print_view_updated.html', bookings=filtered_bookings,
                           guest_filter=guest_filter,
                           apartment_filter=apartment_filter,
                           start_date_filter=start_date_filter,
                           end_date_filter=end_date_filter,
                           apartments=apartments)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
