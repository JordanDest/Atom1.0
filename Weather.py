# weather_module.py
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load the API key from the .env file
load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")

if not API_KEY:
    raise ValueError("API key is missing. Please check your .env file.")

class WeatherData:
    def __init__(self, city_name="High Point", units='imperial'):
        self.city_name = city_name
        self.units = units
        self.coordinates = self.get_coordinates()

    def get_coordinates(self):
        """Fetch the geographical coordinates of the city using the Geocoder API."""
        geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={self.city_name}&limit=1&appid={API_KEY}"
        response = requests.get(geocode_url)
        response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError(f"City not found: {self.city_name}")
        return data[0]['lat'], data[0]['lon']

    def fetch_data(self, url):
        """Generic function to fetch data from the given URL."""
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get_weather(self):
        """Fetch the current weather data using the coordinates."""
        lat, lon = self.coordinates
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units={self.units}"
        return self.fetch_data(weather_url)

    def get_forecast(self):
        """Fetch the forecast weather data using the coordinates."""
        lat, lon = self.coordinates
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units={self.units}"
        return self.fetch_data(forecast_url)

def format_weather_data(data):
    """Format the weather data for clean display."""
    description = data['weather'][0]['description']
    temp = round(data['main']['temp'])
    feels_like = round(data['main']['feels_like'])
    humidity = round(data['main']['humidity'])
    wind_speed = round(data['wind']['speed'])
    
    return f"is {temp}°F and {description}. It feels like {feels_like}°F with a humidity of {humidity}% and a wind speed of {wind_speed} mph."

def time_until_event(event_time):
    now = datetime.now()
    event_datetime = datetime.fromtimestamp(event_time)
    time_diff = event_datetime - now
    minutes_until = round(time_diff.total_seconds() / 60)
    hours_until = minutes_until // 60
    minutes_remaining = minutes_until % 60
    return hours_until, minutes_remaining, event_datetime.strftime("%I:%M %p")

def detect_rain(data):
    """Detect rain in the past three days and estimate if the grass is wet."""
    rain_total = 0
    recent_rain = 0
    threshold = 30  # mm of rain threshold to consider the grass wet
    if 'list' in data:
        for entry in data['list']:
            if 'rain' in entry:
                rain_3h = entry['rain'].get('3h', 0)
                rain_total += rain_3h
                if (datetime.now() - datetime.strptime(entry['dt_txt'], "%Y-%m-%d %H:%M:%S")).days <= 1:
                    recent_rain += rain_3h

    return f"The grass is likely {'wet' if rain_total > threshold and recent_rain > 0 else 'dry'}."

def weather_call(city="High Point"):
    """Fetch and return a consolidated weather report."""
    weather_data = WeatherData(city)
    try:
        current_weather = weather_data.get_weather()
        forecast_weather = weather_data.get_forecast()

        report = format_weather_data(current_weather)
        
        sunrise = current_weather['sys']['sunrise']
        sunset = current_weather['sys']['sunset']
        
        hours_until_sunrise, minutes_until_sunrise, sunrise_time = time_until_event(sunrise)
        hours_until_sunset, minutes_until_sunset, sunset_time = time_until_event(sunset)
        
        if hours_until_sunrise < 0:
            hours_until_sunrise += 24  # Add 24 hours if the event is on the next day
        if hours_until_sunset < 0:
            hours_until_sunset += 24  # Add 24 hours if the event is on the next day
        
        next_event = "sunrise" if hours_until_sunrise < hours_until_sunset else "sunset"
        hours_until_event_time = min(hours_until_sunrise, hours_until_sunset)
        minutes_until_event_time = minutes_until_sunrise if next_event == "sunrise" else minutes_until_sunset
        event_time_str = sunrise_time if next_event == "sunrise" else sunset_time
        
        rain_analysis = detect_rain(forecast_weather)
        
        if hours_until_event_time == 0:
            event_str = f"You can catch the next {next_event} at {event_time_str} in {minutes_until_event_time} minutes."
        else:
            event_str = f"You can catch the next {next_event} at {event_time_str} in {hours_until_event_time} hours and {minutes_until_event_time} minutes."
        
        return f"The current weather in {city}:\n{report}\n{event_str}\n{rain_analysis}"

    except Exception as e:
        return f"Sorry, I couldn't fetch the weather information for {city}. Error: {e}"
