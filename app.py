import os
import json
import logging
from flask import session
from flask import Flask, render_template, request, flash, g, jsonify, current_app
from flask_babel import Babel, gettext as _
from datetime import datetime, timedelta, date
from smoobu_api import SmoobuAPI
from config import SMOOBU_SETTINGS_CHANNEL_ID, SMOOBU_API_KEY, BABEL_DEFAULT_LOCALE, BABEL_DEFAULT_TIMEZONE

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a real secret key
app.config['BABEL_DEFAULT_LOCALE'] = 'de'
app.config['BABEL_DEFAULT_TIMEZONE'] = BABEL_DEFAULT_TIMEZONE

babel = Babel(app)
smoobu_api = SmoobuAPI(SMOOBU_SETTINGS_CHANNEL_ID, SMOOBU_API_KEY)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def refresh_translations():
    if hasattr(current_app, 'babel'):
        current_app.babel.refresh()

def get_locale():
    # First check URL parameters
    lang = request.args.get('lang')
    if lang in ['en', 'de']:
        session['lang'] = lang
        refresh_translations()
        return lang
    
    # Then check session
    if 'lang' in session:
        return session.get('lang')
        
    # Finally default to German
    session['lang'] = 'de'
    return 'de'

babel.init_app(app, locale_selector=get_locale)

def fetch_and_filter_bookings(guest_filter='', apartment_filter='', start_date_filter='', end_date_filter=''):
    # Validate date filters
    try:
        if start_date_filter:
            datetime.strptime(start_date_filter, '%Y-%m-%d')
        if end_date_filter:
            datetime.strptime(end_date_filter, '%Y-%m-%d')
        
        if start_date_filter and end_date_filter:
            if start_date_filter > end_date_filter:
                logger.error("Invalid date range: start date is after end date")
                return [], "Invalid date range: start date must be before or equal to end date"
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        return [], "Invalid date format. Please use YYYY-MM-DD format"

    logger.info(f"Fetching bookings with filters - Guest: {guest_filter}, Apartment: {apartment_filter}, "
                f"Start Date: {start_date_filter}, End Date: {end_date_filter}")

    bookings, error = smoobu_api.get_bookings(
        guest_filter=guest_filter,
        apartment_filter=apartment_filter,
        start_date_filter=start_date_filter,
        end_date_filter=end_date_filter
    )
    if error:
        logger.error(f"Error fetching bookings: {error}")
        return [], error

    logger.info(f"Retrieved {len(bookings)} bookings from Smoobu API")
    if bookings:
        earliest_date = min(booking['check_in'] for booking in bookings)
        latest_date = max(booking['check_out'] for booking in bookings)
        logger.info(f"Date range of bookings: from {earliest_date} to {latest_date}")
        
        # Log booking statistics
        booking_stats = {
            'total': len(bookings),
            'with_guest_name': sum(1 for b in bookings if b.get('guest_name', 'Unknown Guest') != 'Unknown Guest'),
            'with_phone': sum(1 for b in bookings if b.get('phone_number')),
            'with_assistant_notice': sum(1 for b in bookings if b.get('assistantNotice'))
        }
        logger.debug(f"Booking statistics: {json.dumps(booking_stats, indent=2)}")
        
        if len(bookings) > 0:
            logger.debug(f"Sample booking structure: {json.dumps(bookings[0], indent=2)}")

    return bookings if bookings else [], None

@app.route('/')
def booking_list():
    logger.debug("Entering booking_list function")
    # Get filters from request args or session
    guest_filter = request.args.get('guest_filter', session.get('guest_filter', ''))
    apartment_filter = request.args.get('apartment_filter', session.get('apartment_filter', ''))
    start_date_filter = request.args.get('start_date_filter', session.get('start_date_filter', ''))
    end_date_filter = request.args.get('end_date_filter', session.get('end_date_filter', ''))
    
    # Store current filter values in session
    session['guest_filter'] = guest_filter
    session['apartment_filter'] = apartment_filter
    session['start_date_filter'] = start_date_filter
    session['end_date_filter'] = end_date_filter

    logger.debug(f"Filters applied - Guest: {guest_filter}, Apartment: {apartment_filter}, "
                f"Start Date: {start_date_filter}, End Date: {end_date_filter}")

    filtered_bookings, error = fetch_and_filter_bookings(guest_filter, apartment_filter, start_date_filter, end_date_filter)
    if error:
        flash(error, 'error')
        filtered_bookings = []

    # Get list of apartments from normalized bookings
    all_bookings, _ = smoobu_api.get_bookings()
    apartments = sorted(set(booking.get('apartment_name') for booking in all_bookings if booking.get('apartment_name')))

    return render_template('booking_list.html', bookings=filtered_bookings,
                           guest_filter=guest_filter,
                           apartment_filter=apartment_filter,
                           start_date_filter=start_date_filter,
                           end_date_filter=end_date_filter,
                           apartments=apartments)

@app.route('/calendar')
def calendar_view():
    logger.debug("Entering calendar_view function")
    # Get filters from request args or session
    guest_filter = request.args.get('guest_filter', session.get('guest_filter', ''))
    apartment_filter = request.args.get('apartment_filter', session.get('apartment_filter', ''))
    start_date_filter = request.args.get('start_date_filter', session.get('start_date_filter', ''))
    end_date_filter = request.args.get('end_date_filter', session.get('end_date_filter', ''))
    
    # Store current filter values in session
    session['guest_filter'] = guest_filter
    session['apartment_filter'] = apartment_filter
    session['start_date_filter'] = start_date_filter
    session['end_date_filter'] = end_date_filter

    logger.debug(f"Received filters - Start date: {start_date_filter}, End date: {end_date_filter}")

    try:
        # Get current date and calculate week dates
        if request.args.get('date'):
            display_date = datetime.strptime(request.args.get('date'), '%Y-%m-%d')
        elif start_date_filter:
            display_date = datetime.strptime(start_date_filter, '%Y-%m-%d')
        else:
            display_date = datetime.now()

        week_start = display_date - timedelta(days=display_date.weekday())
        prev_week = (week_start - timedelta(weeks=1)).strftime('%Y-%m-%d')
        next_week = (week_start + timedelta(weeks=1)).strftime('%Y-%m-%d')

        week_start = display_date - timedelta(days=display_date.weekday())
        prev_week = (week_start - timedelta(weeks=1)).strftime('%Y-%m-%d')
        next_week = (week_start + timedelta(weeks=1)).strftime('%Y-%m-%d')
        logger.debug(f"Calculated week start: {week_start.strftime('%Y-%m-%d')}")
        
        week_dates = [week_start + timedelta(days=i) for i in range(7)]
    except ValueError as e:
        logger.error(f"Error processing dates in calendar view: {e}")
        flash("Invalid date format", "error")
        return redirect(url_for('calendar_view'))
    logger.debug(f"Generated week dates from {week_dates[0].strftime('%Y-%m-%d')} to {week_dates[-1].strftime('%Y-%m-%d')}")
    
    week_number = week_start.isocalendar()[1]
    logger.info(f"Week number for display: {week_number}")

    logger.info(f"Calendar view - Week start: {week_start}, Week number: {week_number}")

    filtered_bookings, error = fetch_and_filter_bookings(guest_filter, apartment_filter, start_date_filter, end_date_filter)
    if error:
        flash(error, 'error')
        filtered_bookings = []
        logger.error(f"Error fetching bookings for calendar view: {error}")

    # Get list of apartments from normalized bookings
    all_bookings, _ = smoobu_api.get_bookings()
    apartments = sorted(set(booking.get('apartment_name') for booking in all_bookings if booking.get('apartment_name')))
    logger.info(f"Available apartments: {apartments}")

    # Initialize calendar data structure
    calendar_data = {apartment: {date: [] for date in week_dates} for apartment in apartments}
    logger.debug(f"Initialized calendar data structure for {len(apartments)} apartments")

    # Process bookings for calendar view
    for booking in filtered_bookings:
        try:
            check_in = datetime.strptime(booking['check_in'], '%Y-%m-%d')
            check_out = datetime.strptime(booking['check_out'], '%Y-%m-%d')
            apartment_name = booking['apartment_name']

            logger.debug(f"Processing booking: {booking['guest_name']} "
                        f"({check_in.strftime('%Y-%m-%d')} - {check_out.strftime('%Y-%m-%d')}) "
                        f"in {apartment_name}")

            for date in week_dates:
                if check_in <= date < check_out:
                    calendar_data[apartment_name][date].append(booking)
                    logger.debug(f"Added booking to calendar: {date.strftime('%Y-%m-%d')} - {apartment_name}")

        except (KeyError, ValueError) as e:
            logger.error(f"Error processing booking for calendar view: {e}")
            logger.error(f"Problematic booking data: {json.dumps(booking, indent=2)}")
            continue

    # Filter apartments that have bookings
    apartments_with_bookings = [apartment for apartment in apartments 
                              if any(calendar_data[apartment].values())]
    logger.info(f"Apartments with bookings: {len(apartments_with_bookings)}")

    prev_week = (week_start - timedelta(weeks=1)).strftime('%Y-%m-%d')
    next_week = (week_start + timedelta(weeks=1)).strftime('%Y-%m-%d')
    today = date.today()

    return render_template('calendar_view.html',
                           apartments=apartments_with_bookings,
                           calendar_data=calendar_data,
                           week_dates=week_dates,
                           week_number=week_number,
                           current_date=display_date,
                           prev_week=prev_week,
                           next_week=next_week,
                           guest_filter=guest_filter,
                           apartment_filter=apartment_filter,
                           start_date_filter=start_date_filter,
                           end_date_filter=end_date_filter,
                           today=today,
                           timedelta=timedelta)

@app.route('/print')
def print_view():
    logger.debug("Entering print_view function")
    # Get filters from request args or session
    guest_filter = request.args.get('guest_filter', session.get('guest_filter', ''))
    apartment_filter = request.args.get('apartment_filter', session.get('apartment_filter', ''))
    start_date_filter = request.args.get('start_date_filter', session.get('start_date_filter', ''))
    end_date_filter = request.args.get('end_date_filter', session.get('end_date_filter', ''))
    
    # Store current filter values in session
    session['guest_filter'] = guest_filter
    session['apartment_filter'] = apartment_filter
    session['start_date_filter'] = start_date_filter
    session['end_date_filter'] = end_date_filter
    
    logger.info(f"Print view filters - Guest: {guest_filter}, Apartment: {apartment_filter}, "
                f"Start Date: {start_date_filter}, End Date: {end_date_filter}")

    filtered_bookings, error = fetch_and_filter_bookings(guest_filter, apartment_filter, start_date_filter, end_date_filter)
    if error:
        logger.error(f"Error in print view: {error}")
        flash(error, 'error')
        filtered_bookings = []

    # Get list of apartments from normalized bookings
    all_bookings, _ = smoobu_api.get_bookings()
    if all_bookings:
        logger.debug(f"Total bookings before apartment filtering: {len(all_bookings)}")
        if len(all_bookings) > 0:
            logger.debug(f"Sample booking data: {json.dumps(all_bookings[0], indent=2)}")
    
    apartments = sorted(set(booking.get('apartment_name') for booking in all_bookings if booking.get('apartment_name')))
    logger.info(f"Available apartments: {apartments}")

    # Log filtered bookings details
    logger.info(f"Total filtered bookings for print view: {len(filtered_bookings)}")
    if filtered_bookings:
        date_range = {
            'earliest': min(booking['check_in'] for booking in filtered_bookings),
            'latest': max(booking['check_out'] for booking in filtered_bookings)
        }
        logger.info(f"Date range of filtered bookings: {date_range}")
        if len(filtered_bookings) > 0:
            logger.debug(f"Sample filtered booking: {json.dumps(filtered_bookings[0], indent=2)}")

    return render_template('print_view_updated.html', bookings=filtered_bookings,
                           guest_filter=guest_filter,
                           apartment_filter=apartment_filter,
                           start_date_filter=start_date_filter,
                           end_date_filter=end_date_filter,
                           apartments=apartments)

@app.route('/test_booking_template')
def test_booking_template():
    # Create sample booking data matching the expected structure
    sample_bookings = [{
        'guest_name': 'Test Guest',
        'check_in': '2024-12-01',
        'check_out': '2024-12-07',
        'apartment_name': 'Test Apartment',
        'channel_name': 'Direct',
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