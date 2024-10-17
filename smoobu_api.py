import requests
from datetime import datetime, timedelta
import json

class SmoobuAPI:
    BASE_URL = 'https://login.smoobu.com/api'

    def __init__(self, settings_channel_id, api_key):
        self.settings_channel_id = settings_channel_id
        self.api_key = api_key
        self.headers = {
            'API-Key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def get_bookings(self):
        start_date = datetime.now()
        end_date = start_date + timedelta(weeks=4)
        params = {
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d')
        }
        try:
            url = f"{self.BASE_URL}/reservations"
            print(f"Debug: Accessing URL: {url}")
            print(f"Debug: Headers: {json.dumps(self.headers, indent=2)}")
            print(f"Debug: Params: {json.dumps(params, indent=2)}")
            
            response = requests.get(url, headers=self.headers, params=params)
            
            print(f"Debug: Response status code: {response.status_code}")
            print(f"Debug: Response headers: {json.dumps(dict(response.headers), indent=2)}")
            print(f"Debug: Response content: {response.text[:500]}...")  # Print first 500 characters
            
            response.raise_for_status()
            
            try:
                data = response.json()
                print(f"Debug: Parsed JSON data: {json.dumps(data, indent=2)[:1000]}...")  # Print first 1000 characters of parsed JSON
            except ValueError as json_error:
                error_message = f"Error decoding JSON: {str(json_error)}"
                error_message += f"\nResponse status code: {response.status_code}"
                error_message += f"\nResponse headers: {json.dumps(dict(response.headers), indent=2)}"
                error_message += f"\nRaw response content: {response.text[:1000]}..."  # Print first 1000 characters
                print(error_message)
                return [], error_message
            
            bookings = []
            for booking in data.get('bookings', []):
                adults = booking.get('adults', 0) or 0
                children = booking.get('children', 0) or 0
                bookings.append({
                    'guest_name': f"{booking.get('firstname', '')} {booking.get('lastname', '')}".strip() or "Unknown Guest",
                    'booking_date': booking.get('created-at', ''),
                    'apartment_name': booking.get('apartment', {}).get('name', ''),
                    'check_in': booking.get('arrival', ''),
                    'check_out': booking.get('departure', ''),
                    'guests': adults + children,
                    'total_price': booking.get('total-amount', 0),
                    'status': booking.get('status', 'Unknown'),
                    'type': booking.get('type', 'Unknown')
                })
            print(f"Debug: Processed bookings: {json.dumps(bookings, indent=2)}")
            return bookings, None
        except requests.RequestException as e:
            error_message = f"Error fetching bookings: {str(e)}"
            if hasattr(e, 'response'):
                error_message += f"\nResponse status code: {e.response.status_code}"
                error_message += f"\nResponse headers: {json.dumps(dict(e.response.headers), indent=2)}"
                error_message += f"\nResponse content: {e.response.text[:1000]}..."  # Print first 1000 characters
            else:
                error_message += "\nNo response object available"
            print(error_message)
            return [], error_message

    # Add more API methods as needed
