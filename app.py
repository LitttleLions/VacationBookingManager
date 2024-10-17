import os
from flask import Flask, render_template, request, g, flash
from flask_babel import Babel
from urllib.parse import urlparse
from smoobu_api import SmoobuAPI
from datetime import datetime, timedelta, date
import calendar
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

app.config.from_object('config')

smoobu_api = SmoobuAPI(app.config['SMOOBU_SETTINGS_CHANNEL_ID'], app.config['SMOOBU_API_KEY'])

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_locale():
    return request.accept_languages.best_match(['en', 'de'])

babel = Babel(app, locale_selector=get_locale)

@app.template_filter('month_name')
def month_name_filter(month_number):
    return datetime(2000, month_number, 1).strftime('%B')

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
        if (guest_filter in booking['guest_name'].lower() and
            apartment_filter in booking['apartment_name'].lower() and
            (not date_filter or (booking['check_in'] <= date_filter <= booking['check_out']))):
            filtered_bookings.append(booking)

    logger.debug(f"Filtered bookings: {len(filtered_bookings)} out of {len(bookings)}")

    return render_template('booking_list.html', bookings=filtered_bookings,
                           guest_filter=guest_filter,
                           apartment_filter=apartment_filter,
                           date_filter=date_filter)

@app.route('/calendar')
def calendar_view():
    logger.debug("Entering calendar_view function")
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

    current_date = datetime.strptime(request.args.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date()

    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_next_week = start_of_week + timedelta(days=13)

    two_week_dates = [start_of_week + timedelta(days=i) for i in range(14)]
    week1_dates = two_week_dates[:7]
    week2_dates = two_week_dates[7:]

    week1_number = week1_dates[0].isocalendar()[1]
    week2_number = week2_dates[0].isocalendar()[1]

    apartments = list(set(booking['apartment_name'] for booking in bookings))
    apartments.sort()

    calendar_data = {apartment: {d: [] for d in two_week_dates} for apartment in apartments}
    colors = ['orange', 'blue', 'teal']
    color_index = 0

    filtered_bookings = []
    for booking in bookings:
        if (guest_filter in booking['guest_name'].lower() and
            apartment_filter in booking['apartment_name'].lower() and
            (not date_filter or (booking['check_in'] <= date_filter <= booking['check_out']))):
            filtered_bookings.append(booking)

    for booking in filtered_bookings:
        check_in = datetime.strptime(booking['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(booking['check_out'], '%Y-%m-%d').date()
        apartment = booking['apartment_name']
        
        if apartment in apartments:
            for d in two_week_dates:
                if check_in <= d < check_out and booking['guest_name'] != "Unknown Guest":
                    booking['color'] = colors[color_index]
                    calendar_data[apartment][d].append(booking)
            color_index = (color_index + 1) % len(colors)

    prev_two_weeks = start_of_week - timedelta(days=14)
    next_two_weeks = start_of_week + timedelta(days=14)

    logger.debug(f"Calendar view prepared for {len(apartments)} apartments")

    return render_template('calendar_view.html', 
                           current_date=current_date,
                           two_week_dates=two_week_dates,
                           week1_dates=week1_dates,
                           week2_dates=week2_dates,
                           week1_number=week1_number,
                           week2_number=week2_number,
                           apartments=apartments,
                           calendar_data=calendar_data,
                           prev_two_weeks=prev_two_weeks,
                           next_two_weeks=next_two_weeks,
                           guest_filter=guest_filter,
                           apartment_filter=apartment_filter,
                           date_filter=date_filter)

@app.route('/print')
def print_view():
    logger.debug("Entering print_view function")
    bookings, error = smoobu_api.get_bookings()
    if error:
        logger.error(f"Error fetching bookings: {error}")
        flash(error, 'error')
        bookings = []
    else:
        logger.debug(f"Retrieved {len(bookings)} bookings for print view")
    return render_template('print_view.html', bookings=bookings)

@app.context_processor
def inject_debug():
    return dict(debug=app.debug)

@app.context_processor
def inject_get_locale():
    return dict(get_locale=get_locale)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)