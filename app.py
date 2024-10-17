import logging
from flask import Flask, render_template, request, flash, g
from flask_babel import Babel, gettext as _
from datetime import datetime, timedelta
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

    guest_filter = request.args.get('guest_filter', '').lower()
    apartment_filter = request.args.get('apartment_filter', '').lower()
    date_filter = request.args.get('date_filter', '')

    logger.debug(f"Filters applied - Guest: {guest_filter}, Apartment: {apartment_filter}, Date: {date_filter}")

    filtered_bookings = []
    for booking in bookings:
        logger.debug(f"Processing booking: {booking['guest_name']} - {booking['apartment_name']} - {booking['check_in']} to {booking['check_out']}")
        if (guest_filter in booking['guest_name'].lower() and
            apartment_filter in booking['apartment_name'].lower() and
            (not date_filter or (booking['check_in'] <= date_filter <= booking['check_out']))):
            filtered_bookings.append(booking)
            logger.debug(f"Booking added to filtered list")
        else:
            logger.debug(f"Booking filtered out")

    logger.debug(f"Filtered bookings: {len(filtered_bookings)} out of {len(bookings)}")

    return render_template('booking_list.html', bookings=filtered_bookings,
                           guest_filter=guest_filter,
                           apartment_filter=apartment_filter,
                           date_filter=date_filter)

@app.route('/calendar')
def calendar_view():
    # ... (calendar view implementation)
    pass

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
    return render_template('print_view.html', bookings=bookings)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)