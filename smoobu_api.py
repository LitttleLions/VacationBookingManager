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
        response = requests.get(f"{self.BASE_URL}/bookings", headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            # Handle error
            return []

    # Add more API methods as needed
