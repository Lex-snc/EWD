from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import random
import time
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

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
@app.route('/')
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
@app.route('/weather')
def weather():
    # Open-Meteo API Request
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 52.52,
        "longitude": 13.41,
        "hourly": "temperature_2m",
        "daily": "weather_code",
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
        "hourly": "temperature_2m",
        "daily": "weather_code",
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

if __name__ == '__main__':
    app.run(debug=True)
