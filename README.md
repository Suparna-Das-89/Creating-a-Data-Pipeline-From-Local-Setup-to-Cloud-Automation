# Gans e-Scooter Sharing System

Gans is an ambitious startup developing an **e-scooter-sharing system** with the goal of operating in the most populous cities worldwide. Similar to its established competitors like **TIER** in Europe and **Bird** from California, Gans promotes **sustainable mobility** through Battery Electric Vehicles (BEVs), distinguishing itself from Internal Combustion Engine Vehicles (ICEVs). While many companies focus on eco-friendly marketing to attract users, Gans recognizes that **operational success** lies in ensuring scooters are available **where and when users need them**.

## Project Overview
To address this challenge, we built a data pipeline and automation workflow that:
- Scrapes demographic and geographic data of target cities
- Collects real-time weather and airport activity via APIs
- Inserts the data into a centralized SQL database
- Automates data processing using Google Cloud Functions and Scheduler

---

## 1. Web Scraping City Data
We began by scraping the **country**, **latitude**, and **longitude** of major cities like:
- Berlin
- Hamburg
- Munich

To achieve this, we used **BeautifulSoup**, a Python library ideal for beginners in web scraping. Although there are other tools like Scrapy and Selenium, BeautifulSoup gave us the foundation to efficiently extract structured data from Wikipedia pages.

## 2. Creating the Database
After collecting city data, we created a **MySQL database** named `Gans`, with tables such as:
- `cities` (stores city name, country, coordinates)
- `city_population` (stores population data scraped from Wikipedia)

Once the tables were defined, we used **SQLAlchemy** to connect Python to MySQL and insert data into our tables using `pandas.DataFrame.to_sql()`. SQLAlchemy infers data types and handles table creation if it doesn’t exist. For manual adjustments, we used MySQL Workbench with `ALTER TABLE` and `MODIFY` clauses.

---

## 3. API Integration
To enrich our dataset, we worked with external APIs:

### Weather Data - OpenWeatherMap API
We retrieved live weather data from OpenWeatherMap by:
- Constructing precise API URLs
- Parsing JSON responses
- Storing temperature, humidity, and other relevant data into a `weather` table in SQL

### Airport Data - AeroDataBox API
We used AeroDataBox to fetch airport data near our cities by using the latitude and longitude coordinates. API responses were normalized and stored in the `airports` table, containing fields like:
- `arrival_airport_icao`
- `arrival_airport_name`
- `latitude`
- `longitude`
- `city_id`

All responses were validated using HTTP status codes (e.g., 200 for success, 429 for rate limiting) and handled gracefully within the script.

---

## 4. Moving to the Cloud
With our local pipeline ready, we migrated it to the cloud:

### Google Cloud SQL
- Created a **Cloud SQL instance** and replicated our local schema.
- Used the **Migration Wizard** in MySQL Workbench to migrate local data to GCP.

### Cloud Functions
We deployed Python scripts to **Google Cloud Functions**, where each function acts as a microservice:
- One function fetches **daily weather and flight data**
- Another function retrieves **yearly population and airport data**

### Automation via Cloud Scheduler
To automate execution:
- The daily function is scheduled to run **every day** via **Cloud Scheduler**.
- The yearly function (population + airports) runs **every 10th of April at 01:00 AM**, using the Unix cron format: `0 1 10 4 *`

---

## Final Outcome
With this system in place, Gans can:
- Track population growth and airport traffic
- Predict user demand based on weather and nearby flights
- Strategically **deploy scooters** in high-demand areas, ensuring operational efficiency

This seamless integration of scraping, APIs, databases, and cloud services empowers Gans to stay ahead in the competitive e-scooter market.

---

## Technologies Used
- **Python** (BeautifulSoup, Requests, Pandas)
- **SQLAlchemy** (Database connection)
- **MySQL / Google Cloud SQL** (Data storage)
- **OpenWeatherMap & AeroDataBox APIs**
- **Google Cloud Functions & Scheduler**
- **MySQL Workbench** (Schema design & data migration)

---

## Repository Structure
```
📁 gans-escooter-system
├── 📁 scripts
│   ├── population_scraper.py
│   ├── airport_data_fetcher.py
│   ├── weather_and_flights.py
├── 📁 cloud
│   ├── main_function.py
│   ├── requirements.txt
│   └── cron_jobs.yaml
├── 📁 sql
│   └── schema.sql
└── README.md
```


