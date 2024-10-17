import requests
from datetime import datetime, timedelta
import json
import time
import logging

logger = logging.getLogger(__name__)

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

    def get_bookings(self, max_retries=3, initial_delay=1):
        logger.debug("Entering get_bookings method")
        start_date = datetime.now()
        end_date = start_date + timedelta(weeks=4)
        params = {
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d')
        }
        
        for attempt in range(max_retries):
            try:
                url = f"{self.BASE_URL}/reservations"
                logger.debug(f"Sending request to {url}")
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                logger.debug(f"Received response: {json.dumps(data, indent=2)}")
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
                        'type': booking.get('type', 'Unknown'),
                        'phone_number': booking.get('phone', 'N/A'),
                        'assistance_notes': booking.get('notes', 'N/A'),
                        'language': booking.get('language', 'N/A')
                    })
                logger.debug(f"Processed {len(bookings)} bookings")
                return bookings, None
            except requests.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    error_message = f"Error fetching bookings after {max_retries} attempts: {str(e)}"
                    if hasattr(e, 'response'):
                        error_message += f"\nResponse status code: {e.response.status_code}"
                        error_message += f"\nResponse content: {e.response.text[:500]}..."
                    else:
                        error_message += "\nNo response object available"
                    logger.error(error_message)
                    return [], error_message

    # Add more API methods as needed
