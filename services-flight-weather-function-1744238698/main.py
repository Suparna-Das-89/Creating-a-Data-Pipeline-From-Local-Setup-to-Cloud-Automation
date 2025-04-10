import functions_framework
import pandas as pd
import sqlalchemy
from datetime import datetime, timedelta
import requests
from pytz import timezone
import os
import dotenv
import pymysql
from flask import abort



# ✅ Function to connect to MySQL database
def connection():
    schema = "gans"
    host = "34.140.234.130"
    user = os.getenv('MySQL_username')
    password = os.getenv('google_cloud_password')
    port = 3306
    
    engine = sqlalchemy.create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{schema}")
    return engine


# ✅ Function to fetch flight arrivals for given ICAO airport codes
def arrival_airport_icao(icao_list):
    headers = {
        "x-rapidapi-key": os.getenv('AeroDataBox_API_Key'),
        "x-rapidapi-host": "aerodatabox.p.rapidapi.com"  
    }
    querystring = {
        "withLeg": "false", 
        "direction": "Arrival", 
        "withCancelled": "false", 
        "withCodeshared": "false", 
        "withCargo": "false", 
        "withPrivate": "false", 
        "withLocation": "false"
    }
    
    berlin_timezone = timezone('Europe/Berlin')
    today = datetime.now(berlin_timezone).date()
    tomorrow = (today + timedelta(days=1))

    flight_items = []
    for icao in icao_list:
        times = [["00:00","11:59"], ["12:00","23:59"]]
        for time in times:
            url = f"https://aerodatabox.p.rapidapi.com/flights/airports/icao/{icao}/{tomorrow}T{time[0]}/{tomorrow}T{time[1]}"
            response = requests.get(url, headers=headers, params=querystring)
            while response.status_code == 429:
                response = requests.get(url, headers=headers, params=querystring)
            if response.status_code != 200:
                abort(response.status_code, f"Error: {response.status_code} - {response.text}")
            flights_json = response.json()
            retrieval_time = datetime.now(berlin_timezone).strftime("%Y-%m-%d %H:%M:%S")

            for item in flights_json.get('arrivals', []):
                flight_item = {
                    "arrival_airport_icao": icao,
                    "arrival_airport_name": item["movement"]["airport"]["name"],
                    "flight_number": item.get("number", None),
                    "scheduled_arrival_time": item["movement"]["scheduledTime"]["local"],
                    "revised_arrival_time": item.get("movement", {}).get("revisedTime", {}).get("local", None),
                    "airline_name": item["airline"].get("name", None),
                    "status": item["status"],
                    "retrieval_time": retrieval_time
                }
                flight_items.append(flight_item)

    flights_df = pd.DataFrame(flight_items)

    flights_df["scheduled_arrival_time"] = flights_df["scheduled_arrival_time"].astype(str).str.replace(
        r"[\+\-]\d{2}:\d{2}$", "", regex=True
    )
    flights_df["revised_arrival_time"] = flights_df["revised_arrival_time"].astype(str).str.replace(
        r"[\+\-]\d{2}:\d{2}$", "", regex=True
    )

    return flights_df


# ✅ Function to fetch weather data
def get_weather_data():
    engine = connection()

    cities_df = pd.read_sql('SELECT city_name, latitude, longitude FROM cities', con=engine)

    api_key = os.getenv('Weather_API_key')
    
    data = {
        "city": [],
        "date": [],
        "temperature": [],
        "feels_like": [],
        "wind_speed": [],
        "visibility": [],
        "weather": [],
        "rain": [],
        "snow": [],
        "time_retrieved": []
    }
    
    tz = 'Europe/Berlin'
    cities = cities_df["city_name"].tolist()
    lats = cities_df["latitude"].tolist()
    lons = cities_df["longitude"].tolist()

    for city, lat, lon in zip(cities, lats, lons):
        url = f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric'
        response = requests.get(url)
        weather_json = response.json()
        while response.status_code == 429:
            response = requests.get(url)
        if response.status_code != 200:
            abort(response.status_code, f"Error: {response.status_code} - {response.text}")
        for time_window in weather_json.get('list', []):
            data['city'].append(city)
            data['date'].append(time_window['dt_txt'])
            data['temperature'].append(time_window['main'].get('temp', None))
            data['feels_like'].append(time_window['main'].get('feels_like', None))
            data['wind_speed'].append(time_window['wind'].get('speed', None))
            data['visibility'].append(time_window.get('visibility', None))
            data['weather'].append(time_window['weather'][0].get('main', None))
            data['rain'].append(time_window.get('rain', {}).get('3h', None))
            data['snow'].append(time_window.get('snow', {}).get('3h', None))
            data['time_retrieved'].append(datetime.now(timezone(tz)))

    weather_df = pd.DataFrame(data)
    return weather_df


# ✅ Unified Cloud Function Entry Point
@functions_framework.http
def insert(request):
    dotenv.load_dotenv()
    engine = connection()  # ✅ Get DB connection

    # ✅ Insert flight data
    icao_list = ["EDDB", "EGLL", "LFPG"]  # Example ICAO codes
    flights_df = arrival_airport_icao(icao_list)
    flights_df['revised_arrival_time'] = pd.to_datetime(flights_df['revised_arrival_time'], errors="coerce")
    flights_df.to_sql(name="flights", con=engine, if_exists="append", index=False)

    # ✅ Insert weather data
    weather_df = get_weather_data()
    weather_df.to_sql(name="weather_forecast", con=engine, if_exists="append", index=False)

    return "Data successfully added"
