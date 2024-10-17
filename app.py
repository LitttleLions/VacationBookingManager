import os
from flask import Flask, render_template, request, g, flash
from flask_babel import Babel
from urllib.parse import urlparse
from smoobu_api import SmoobuAPI
from datetime import datetime, timedelta, date
import calendar

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

app.config.from_object('config')

smoobu_api = SmoobuAPI(app.config['SMOOBU_SETTINGS_CHANNEL_ID'], app.config['SMOOBU_API_KEY'])

def get_locale():
    return request.accept_languages.best_match(['en', 'de'])

babel = Babel(app, locale_selector=get_locale)

@app.template_filter('month_name')
def month_name_filter(month_number):
    return datetime(2000, month_number, 1).strftime('%B')

@app.route('/')
def booking_list():
    # ... existing booking_list function ...
    return render_template('booking_list.html')  # Placeholder return statement

@app.route('/calendar')
def calendar_view():
    bookings, error = smoobu_api.get_bookings()
    if error:
        flash(error, 'error')

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

    for booking in bookings:
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
                           next_two_weeks=next_two_weeks)

@app.route('/print')
def print_view():
    # ... existing print_view function ...
    return render_template('print_view.html')  # Placeholder return statement

@app.context_processor
def inject_debug():
    return dict(debug=app.debug)

@app.context_processor
def inject_get_locale():
    return dict(get_locale=get_locale)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
