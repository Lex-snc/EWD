from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import random
import time
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For session management
CORS(app)

# Simulated User Database
USERS = {"admin": "admin"}

# Configure Open-Meteo API caching and retry mechanism
cache_session = requests_cache.CachedSession()
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Index Route (Login Page)
@app.route('/index') # /
def index():
    return render_template("index.html")

# Login Route
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    if USERS.get(username) == password:
        return jsonify({'success': True, 'message': 'Login Successful!'})
    else:
        return jsonify({'success': False, 'message': 'Invalid username or password.'})

# Weather Data Route
@app.route('/')  #/weather
def weather():
    # Open-Meteo API Request
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 52.52,
        "longitude": 13.41,
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation_probability", "wind_speed_10m", "weather_code"],
        "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "timezone": "Asia/Singapore"
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    # Process hourly data
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_times = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )
    hourly_data = [{"time": str(t), "temperature": temp} for t, temp in zip(hourly_times, hourly_temperature_2m)]

    # Process daily data
    daily = response.Daily()
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()
    daily_times = pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    )
    daily_data = [{"date": str(d), "weather_code": wc} for d, wc in zip(daily_times, daily_weather_code)]

    return render_template("monitoring.html", hourly_data=hourly_data, daily_data=daily_data)

# Monitoring Data Route
@app.route('/monitor')
def monitor():
    # Simulate monitoring data
    water_level = round(random.uniform(0, 100), 2)
    current = round(random.uniform(0, 10), 2)
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    # Debugging prints
    print(f"Monitoring Data - Water Level: {water_level} cm, Current: {current} A, Timestamp: {timestamp}")

    # Open-Meteo API Request
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 52.52,
        "longitude": 13.41,
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation_probability", "wind_speed_10m", "weather_code"],
        "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "timezone": "Asia/Singapore"
    }

    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]

        # Process hourly data
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_times = pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        )
        hourly_data = [{"time": str(t), "temperature": temp} for t, temp in zip(hourly_times, hourly_temperature_2m)]

        # Process daily data
        daily = response.Daily()
        daily_weather_code = daily.Variables(0).ValuesAsNumpy()
        daily_times = pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left"
        )
        daily_data = [{"date": str(d), "weather_code": wc} for d, wc in zip(daily_times, daily_weather_code)]

        # Debugging prints
        print(f"Hourly Weather Data: {hourly_data[:5]}")  # Print first 5 for debugging
        print(f"Daily Weather Data: {daily_data[:5]}")  # Print first 5 for debugging

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        hourly_data, daily_data = [], []

    # Render template with both monitoring and weather data
    return render_template(
        "monitoring.html",
        water_level=water_level,
        current=current,
        timestamp=timestamp,
        hourly_data=hourly_data,
        daily_data=daily_data
    )

# Function to get location name from coordinates using reverse geocoding
def get_location_name(latitude, longitude):
    try:
        # Use Open-Meteo Geocoding API for reverse geocoding
        url = f"https://geocoding-api.open-meteo.com/v1/search?latitude={latitude}&longitude={longitude}&count=1"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if 'results' in data and len(data['results']) > 0:
            result = data['results'][0]
            location_parts = []
            
            # Build location string with available information
            if 'name' in result:
                location_parts.append(result['name'])
            
            # Add administrative area if different from name
            if 'admin1' in result and result.get('admin1') != result.get('name'):
                location_parts.append(result['admin1'])
                
            # Add country
            if 'country' in result:
                location_parts.append(result['country'])
            
            # If we have timezone information, use it
            timezone = result.get('timezone', 'auto')
            
            location_name = ", ".join(location_parts)
            print(f"Location detected: {location_name} ({latitude}, {longitude})")
            
            return {
                'name': location_name,
                'latitude': latitude,
                'longitude': longitude,
                'timezone': timezone
            }
        else:
            print(f"No location data found for coordinates: {latitude}, {longitude}")
            return {
                'name': f"Location at {latitude:.4f}, {longitude:.4f}",
                'latitude': latitude,
                'longitude': longitude,
                'timezone': 'auto'
            }
    except Exception as e:
        print(f"Error in reverse geocoding: {e}")
        return {
            'name': f"Location at {latitude:.4f}, {longitude:.4f}",
            'latitude': latitude,
            'longitude': longitude,
            'timezone': 'auto'
        }

# Real-time Weather Data Route
@app.route('/get_weather_data')
def get_weather_data():
    try:
        # Get location from request parameters or use defaults
        latitude = request.args.get('lat', 52.52)
        longitude = request.args.get('lon', 13.41)
        
        # Convert to float
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            latitude = 52.52
            longitude = 13.41
        
        # Get location name using reverse geocoding
        location_info = get_location_name(latitude, longitude)
        
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation_probability", "wind_speed_10m", "weather_code"],
            "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
            "timezone": location_info['timezone']  # Use timezone based on location
        }
        
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]

        hourly = response.Hourly()
        hourly_data = {
            "temperature": hourly.Variables(0).ValuesAsNumpy().tolist(),
            "humidity": hourly.Variables(1).ValuesAsNumpy().tolist(),
            "precipitation_prob": hourly.Variables(2).ValuesAsNumpy().tolist(),
            "wind_speed": hourly.Variables(3).ValuesAsNumpy().tolist(),
            "weather_code": hourly.Variables(4).ValuesAsNumpy().tolist(),
            "time": [str(t) for t in pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"
            )]
        }

        daily = response.Daily()
        daily_data = {
            "weather_code": daily.Variables(0).ValuesAsNumpy().tolist(),
            "temp_max": daily.Variables(1).ValuesAsNumpy().tolist(),
            "temp_min": daily.Variables(2).ValuesAsNumpy().tolist(),
            "precipitation": daily.Variables(3).ValuesAsNumpy().tolist(),
            "time": [str(t) for t in pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left"
            )]
        }

        return jsonify({
            "success": True,
            "hourly_data": hourly_data,
            "daily_data": daily_data,
            "location_name": location_info['name'],
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude
            }
        })
    except Exception as e:
        print(f"Error in get_weather_data: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)
