import requests
from datetime import datetime, timedelta

class SmoobuAPI:
    BASE_URL = 'https://login.smoobu.com/api'

    def __init__(self, settings_channel_id, api_key):
        self.settings_channel_id = settings_channel_id
        self.api_key = api_key
        self.headers = {
            'API-Key': self.api_key,
            'Content-Type': 'application/json'
        }

    def get_bookings(self):
        end_date = datetime.now() + timedelta(weeks=4)
        params = {
            'settingsChannelId': self.settings_channel_id,
            'from': datetime.now().strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d')
        }
        try:
            response = requests.get(f"{self.BASE_URL}/bookings", headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            bookings = []
            for booking in data.get('bookings', []):
                bookings.append({
                    'guest_name': f"{booking.get('firstName', '')} {booking.get('lastName', '')}".strip(),
                    'booking_date': booking.get('createdAt', ''),
                    'apartment_name': booking.get('appartment', {}).get('name', ''),
                    'check_in': booking.get('arrivalDate', ''),
                    'check_out': booking.get('departureDate', ''),
                    'guests': booking.get('numGuests', 0),
                    'total_price': booking.get('totalAmount', 0)
                })
            return bookings
        except requests.RequestException as e:
            print(f"Error fetching bookings: {str(e)}")
            return []

    # Add more API methods as needed
