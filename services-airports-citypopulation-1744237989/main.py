import functions_framework
from flask import abort
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from sqlalchemy import create_engine
import os
import dotenv
import time

dotenv.load_dotenv()

# ✅ DB connection
def connection():
    schema = "gans"
    host = "34.140.234.130"
    user = os.getenv('MySQL_username')
    password = os.getenv('google_cloud_password')
    port = 3306
    engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{schema}")
    return engine

# ✅ Scrape city population from Wikipedia
def cities_population(cities):
    populations = []
    years_datas_received = []

    for city in cities:
        url = f"https://en.wikipedia.org/wiki/{city}"
        response = requests.get(url)
        while response.status_code == 429:
            time.sleep(1)
            response = requests.get(url)

        if response.status_code != 200:
            print(f"Error fetching {city}: {response.status_code}")
            populations.append(None)
            years_datas_received.append(None)
            continue

        soup = BeautifulSoup(response.content, "html.parser")
        try:
            population = soup.find(string="Population").find_next("td").text.strip()
            year_data_received = soup.find(string="Population").find_next("div").text.strip()
            year_data_received = re.findall(r"\d{4}", year_data_received)[0]
        except Exception:
            population = None
            year_data_received = None

        populations.append(population)
        years_datas_received.append(year_data_received)

    return pd.DataFrame({
        "population": populations,
        "year_data_received": years_datas_received
    })

# ✅ Fetch nearby airports using AeroDataBox API
def get_airports(latitudes, longitudes, city_ids):
    headers = {
        "X-RapidAPI-Key": os.getenv("AeroDataBox_API_Key"),
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
    }

    querystring = {"withFlightInfoOnly": "true"}
    all_airports = []

    for lat, lon, city_id in zip(latitudes, longitudes, city_ids):
        url = f"https://aerodatabox.p.rapidapi.com/airports/search/location/{lat}/{lon}/km/50/16"
        response = requests.get(url, headers=headers, params=querystring)
        while response.status_code == 429:
            time.sleep(1)
            response = requests.get(url, headers=headers, params=querystring)

        if response.status_code != 200:
            print(f"Error fetching airport data for {lat}, {lon}: {response.status_code}")
            continue

        data = response.json()
        airports = pd.json_normalize(data.get('items', []))

        if not airports.empty:
            airports = airports[["icao", "name", "location.lat", "location.lon"]]
            airports.columns = [
                "arrival_airport_icao", "arrival_airport_name", "latitude", "longitude"
            ]
            airports["city_id"] = city_id
            all_airports.append(airports)

    return pd.concat(all_airports, ignore_index=True) if all_airports else pd.DataFrame()

# ✅ Cloud Function entry point
@functions_framework.http
def insert(request):
    engine = connection()

    # ✅ Get cities from DB
    cities_df = pd.read_sql('SELECT city_id, city_name, latitude, longitude FROM cities', con=engine)
    city_names = cities_df["city_name"].tolist()

    # ✅ Scrape and insert city population
    population_scraped_df = cities_population(city_names)
    population_scraped_df["city_name"] = city_names
    merged_df = pd.merge(cities_df, population_scraped_df, on="city_name", how="left")
    merged_df["population"] = merged_df["population"].str.replace(",", "").str.extract(r"(\d+)")
    merged_df[["city_id", "population", "year_data_received"]].to_sql(
        name="city_population",
        con=engine,
        if_exists="append",
        index=False
    )

    # ✅ Fetch and insert airport data
    airport_df = get_airports(
        cities_df["latitude"].tolist(),
        cities_df["longitude"].tolist(),
        cities_df["city_id"].tolist()
    )

    if not airport_df.empty:
        # Get existing ICAO codes to avoid duplicates
        existing_icaos = pd.read_sql("SELECT arrival_airport_icao FROM airports", con=engine)
        existing_icaos_set = set(existing_icaos["arrival_airport_icao"].dropna().tolist())

        # Filter out duplicates
        airport_df = airport_df[~airport_df["arrival_airport_icao"].isin(existing_icaos_set)]

        # Insert only new ones
        if not airport_df.empty:
            airport_df.to_sql(name="airports", con=engine, if_exists="append", index=False)

    return "City population and airport data successfully added."
