import logging
from flask import Flask, render_template, request, flash, g, jsonify
import json
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

def fetch_and_filter_bookings(guest_filter='', apartment_filter='', start_date_filter='', end_date_filter=''):
    bookings, error = smoobu_api.get_bookings(
        guest_filter=guest_filter,
        apartment_filter=apartment_filter,
        start_date_filter=start_date_filter,
        end_date_filter=end_date_filter
    )
    if error:
        logger.error(f"Error fetching bookings: {error}")
        return [], error

    logger.debug(f"Retrieved {len(bookings)} bookings from Smoobu API")
    if bookings:
        earliest_date = min(booking['arrival'] for booking in bookings)
        latest_date = max(booking['departure'] for booking in bookings)
        logger.debug(f"Date range of bookings: from {earliest_date} to {latest_date}")

    return bookings, None

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
    apartments = sorted(set(booking['apartment']['name'] for booking in all_bookings))

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
    apartments = sorted(set(booking['apartment']['name'] for booking in all_bookings))

    calendar_data = {apartment: {date: [] for date in week_dates} for apartment in apartments}

    for booking in filtered_bookings:
        check_in = datetime.strptime(booking['arrival'], '%Y-%m-%d')
        check_out = datetime.strptime(booking['departure'], '%Y-%m-%d')
        for date in week_dates:
            if check_in <= date < check_out:
                calendar_data[booking['apartment']['name']][date].append(booking)

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
    apartments = sorted(set(booking['apartment']['name'] for booking in all_bookings))

    logger.debug(f"Filtered bookings for print view: {len(filtered_bookings)}")

    return render_template('print_view_updated.html', bookings=filtered_bookings,
                           guest_filter=guest_filter,
                           apartment_filter=apartment_filter,
                           start_date_filter=start_date_filter,
                           end_date_filter=end_date_filter,
                           apartments=apartments)

@app.route('/test_future_bookings')
def test_future_bookings():
    start_date = "2024-01-01"
    end_date = "2074-12-31"  # Extended to 50 years in the future
    bookings, error = smoobu_api.get_bookings_for_period(start_date, end_date)
    if error:
        return jsonify({"error": error}), 500
    
    # Log detailed information about the fetched bookings
    logger.info(f"Fetched {len(bookings)} bookings for period {start_date} to {end_date}")
    if bookings:
        earliest_date = min(booking['arrival'] for booking in bookings)
        latest_date = max(booking['departure'] for booking in bookings)
        logger.info(f"Date range of fetched bookings: from {earliest_date} to {latest_date}")
    
    # Group bookings by year
    bookings_by_year = {}
    for booking in bookings:
        year = datetime.strptime(booking['arrival'], '%Y-%m-%d').year
        if year not in bookings_by_year:
            bookings_by_year[year] = []
        bookings_by_year[year].append(booking)
    
    # Prepare summary data
    summary = {
        "total_bookings": len(bookings),
        "earliest_date": earliest_date if bookings else None,
        "latest_date": latest_date if bookings else None,
        "bookings_by_year": {year: len(year_bookings) for year, year_bookings in bookings_by_year.items()},
    }
    
    return jsonify({
        "summary": summary,
        "bookings": bookings,
        "date_range": {
            "start": start_date,
            "end": end_date
        }
    })

@app.route('/test_booking_template')
def test_booking_template():
    # Create sample booking data matching the expected structure
    sample_bookings = [{
        'guest_name': 'Test Guest',
        'arrival': '2024-12-01',
        'departure': '2024-12-07',
        'apartment': {'name': 'Test Apartment'},
        'channel': {'name': 'Direct'},
        'phone_number': '+1234567890',
        'guests': 2,
        'assistantNotice': 'Test notice',
        'language': 'en'
    }]
    
    logger.debug(f"Rendering test template with sample booking: {json.dumps(sample_bookings[0], indent=2)}")
    
    return render_template('booking_list.html',
                         bookings=sample_bookings,
                         guest_filter='',
                         apartment_filter='',
                         start_date_filter='',
                         end_date_filter='',
                         apartments=['Test Apartment'])
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
import logging
from flask import Flask, render_template, request, flash, g, jsonify
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

def fetch_and_filter_bookings(guest_filter='', apartment_filter='', start_date_filter='', end_date_filter=''):
    bookings, error = smoobu_api.get_bookings(
        guest_filter=guest_filter,
        apartment_filter=apartment_filter,
        start_date_filter=start_date_filter,
        end_date_filter=end_date_filter
    )
    if error:
        logger.error(f"Error fetching bookings: {error}")
        return [], error

    logger.debug(f"Retrieved {len(bookings)} bookings from Smoobu API")
    if bookings:
        earliest_date = min(booking['arrival'] for booking in bookings)
        latest_date = max(booking['departure'] for booking in bookings)
        logger.debug(f"Date range of bookings: from {earliest_date} to {latest_date}")
        
        # Log detailed structure of first booking as example
        if len(bookings) > 0:
            logger.debug(f"Sample booking structure before mapping: {json.dumps(bookings[0], indent=2)}")
            
        # Map fields to match template expectations
        mapped_bookings = []
        for booking in bookings:
            # Skip blocked bookings
            if booking.get('is-blocked-booking', False):
                continue

            # Construct guest name from available fields
            guest_name = (
                booking.get('guest-name') or
                f"{booking.get('firstname', '').strip()} {booking.get('lastname', '').strip()}".strip() or
                'Unknown Guest'
            )

            # Map API fields to our application fields
            mapped_booking = {
                'check_in': booking['arrival'],
                'check_out': booking['departure'],
                'guest_name': guest_name,
                'apartment_name': booking['apartment']['name'],
                'channel_name': booking.get('channel', {}).get('name', 'Direct'),
                'phone_number': booking.get('phone', ''),
                'guests': int(booking.get('adults', 0) or 0) + int(booking.get('children', 0) or 0),
                'assistantNotice': booking.get('assistant-notice', ''),
                'language': booking.get('language', 'en'),
                'total_price': booking.get('price', ''),
                'assistant_notice': booking.get('assistant-notice', '')  # For print view
            }
            
            # Apply guest filter if provided
            if guest_filter and guest_filter.lower() not in guest_name.lower():
                continue
                
            # Apply apartment filter if provided
            if apartment_filter and apartment_filter.lower() != mapped_booking['apartment_name'].lower():
                continue
                
            mapped_bookings.append(mapped_booking)
        
        # Log mapped booking structure
        if mapped_bookings:
            logger.debug(f"Sample mapped booking structure: {json.dumps(mapped_bookings[0], indent=2)}")
            logger.debug(f"Total mapped bookings: {len(mapped_bookings)}")

    return mapped_bookings if bookings else [], None

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
    apartments = sorted(set(booking['apartment']['name'] for booking in all_bookings))

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
    apartments = sorted(set(booking['apartment']['name'] for booking in all_bookings))

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
    apartments = sorted(set(booking['apartment']['name'] for booking in all_bookings))

    logger.debug(f"Filtered bookings for print view: {len(filtered_bookings)}")

    return render_template('print_view_updated.html', bookings=filtered_bookings,
                           guest_filter=guest_filter,
                           apartment_filter=apartment_filter,
                           start_date_filter=start_date_filter,
                           end_date_filter=end_date_filter,
                           apartments=apartments)

@app.route('/test_future_bookings')
def test_future_bookings():
    start_date = "2024-01-01"
    end_date = "2074-12-31"  # Extended to 50 years in the future
    bookings, error = smoobu_api.get_bookings_for_period(start_date, end_date)
    if error:
        return jsonify({"error": error}), 500
    
    # Log detailed information about the fetched bookings
    logger.info(f"Fetched {len(bookings)} bookings for period {start_date} to {end_date}")
    if bookings:
        earliest_date = min(booking['arrival'] for booking in bookings)
        latest_date = max(booking['departure'] for booking in bookings)
        logger.info(f"Date range of fetched bookings: from {earliest_date} to {latest_date}")
    
    # Group bookings by year
    bookings_by_year = {}
    for booking in bookings:
        year = datetime.strptime(booking['arrival'], '%Y-%m-%d').year
        if year not in bookings_by_year:
            bookings_by_year[year] = []
        bookings_by_year[year].append(booking)
    
    # Prepare summary data
    summary = {
        "total_bookings": len(bookings),
        "earliest_date": earliest_date if bookings else None,
        "latest_date": latest_date if bookings else None,
        "bookings_by_year": {year: len(year_bookings) for year, year_bookings in bookings_by_year.items()},
    }
    
    return jsonify({
        "summary": summary,
        "bookings": bookings,
        "date_range": {
            "start": start_date,
            "end": end_date
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

