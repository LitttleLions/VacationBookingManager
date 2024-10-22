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

@app.route('/')
def booking_list():
    logger.debug("Entering booking_list function")
    bookings, error = smoobu_api.get_bookings()
    if error:
        logger.error(f"Error fetching bookings: {error}")
        flash(error, 'error')
        bookings = []
    else:
        logger.debug(f"Retrieved {len(bookings)} bookings from Smoobu API")
        if bookings:
            earliest_date = min(booking['check_in'] for booking in bookings)
            latest_date = max(booking['check_out'] for booking in bookings)
            logger.debug(f"Date range of bookings: from {earliest_date} to {latest_date}")

    guest_filter = request.args.get('guest_filter', '').lower()
    apartment_filter = request.args.get('apartment_filter', '').lower()
    start_date_filter = request.args.get('start_date_filter', '')
    end_date_filter = request.args.get('end_date_filter', '')

    logger.debug(f"Filters applied - Guest: {guest_filter}, Apartment: {apartment_filter}, Start Date: {start_date_filter}, End Date: {end_date_filter}")

    apartments = sorted(set(booking['apartment_name'] for booking in bookings))

    filtered_bookings = []
    for booking in bookings:
        logger.debug(f"Processing booking: {booking['guest_name']} - {booking['apartment_name']} - {booking['check_in']} to {booking['check_out']}")
        if (guest_filter in booking['guest_name'].lower() and
            (apartment_filter == '' or apartment_filter == booking['apartment_name'].lower()) and
            (not start_date_filter or booking['check_out'] >= start_date_filter) and
            (not end_date_filter or booking['check_in'] <= end_date_filter) and
            booking['guest_name'] != "Unknown Guest"):
            filtered_bookings.append(booking)
            logger.debug(f"Booking added to filtered list")
        else:
            logger.debug(f"Booking filtered out")

    logger.debug(f"Filtered bookings: {len(filtered_bookings)} out of {len(bookings)}")

    return render_template('booking_list.html', bookings=filtered_bookings,
                           guest_filter=guest_filter,
                           apartment_filter=apartment_filter,
                           start_date_filter=start_date_filter,
                           end_date_filter=end_date_filter,
                           apartments=apartments)

@app.route('/calendar')
def calendar_view():
    logger.debug("Entering calendar_view function")
    bookings, error = smoobu_api.get_bookings()
    if error:
        logger.error(f"Error fetching bookings for calendar view: {error}")
        flash(error, 'error')
        bookings = []
    else:
        logger.debug(f"Retrieved {len(bookings)} bookings for calendar view")

    guest_filter = request.args.get('guest_filter', '').lower()
    apartment_filter = request.args.get('apartment_filter', '').lower()
    start_date_filter = request.args.get('start_date_filter', '')
    end_date_filter = request.args.get('end_date_filter', '')

    current_date = datetime.strptime(request.args.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
    week_start = current_date - timedelta(days=current_date.weekday())
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    week_number = week_start.isocalendar()[1]

    apartments = sorted(set(booking['apartment_name'] for booking in bookings))

    calendar_data = {apartment: {date: [] for date in week_dates} for apartment in apartments}

    for booking in bookings:
        if (guest_filter in booking['guest_name'].lower() and
            (apartment_filter == '' or apartment_filter == booking['apartment_name'].lower()) and
            (not start_date_filter or booking['check_out'] >= start_date_filter) and
            (not end_date_filter or booking['check_in'] <= end_date_filter) and
            booking['guest_name'] != "Unknown Guest"):
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
    bookings, error = smoobu_api.get_bookings()
    if error:
        logger.error(f"Error fetching bookings for print view: {error}")
        flash(error, 'error')
        bookings = []
    else:
        logger.debug(f"Retrieved {len(bookings)} bookings for print view")

    guest_filter = request.args.get('guest_filter', '').lower()
    apartment_filter = request.args.get('apartment_filter', '')
    start_date_filter = request.args.get('start_date_filter', '')
    end_date_filter = request.args.get('end_date_filter', '')

    apartments = sorted(set(booking['apartment_name'] for booking in bookings))

    filtered_bookings = []
    for booking in bookings:
        if (guest_filter in booking['guest_name'].lower() and
            (apartment_filter == '' or apartment_filter == booking['apartment_name']) and
            (not start_date_filter or booking['check_out'] >= start_date_filter) and
            (not end_date_filter or booking['check_in'] <= end_date_filter) and
            booking['guest_name'] != "Unknown Guest"):
            booking['channel_name'] = booking.get('channel', {}).get('name', 'N/A')
            booking['assistant_notice'] = booking.get('assistance_notes', 'N/A')
            filtered_bookings.append(booking)

    logger.debug(f"Filtered bookings for print view: {len(filtered_bookings)} out of {len(bookings)}")

    return render_template('print_view_updated.html', bookings=filtered_bookings,
                           guest_filter=guest_filter,
                           apartment_filter=apartment_filter,
                           start_date_filter=start_date_filter,
                           end_date_filter=end_date_filter,
                           apartments=apartments)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)