DROP DATABASE IF EXISTS gans;

CREATE DATABASE gans;

USE gans;
DROP table cities;
CREATE TABLE cities(
	city_id INT AUTO_INCREMENT,
	city_name VARCHAR(255) NOT NULL,
    country VARCHAR(255),
    -- Use For latitude & longitude (precise GPS data) → DECIMAL(9,6)
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    PRIMARY KEY (city_id)	
);
drop table city_population;
CREATE TABLE city_population(
	population_id INT AUTO_INCREMENT PRIMARY KEY,
	city_id INT,
	population BIGINT,
	year_data_received INT,
	FOREIGN KEY (city_id) REFERENCES cities(city_id)
);


DROP TABLE weather_forecast;
CREATE TABLE weather_forecast(
weather_id INT AUTO_INCREMENT,
city VARCHAR(255) NOT NULL,
date DATETIME,
temperature INT,
feels_like INT,
wind_speed INT,
visibility INT,
weather VARCHAR(255),
rain INT,
snow INT,
time_retrieved DATETIME,
PRIMARY KEY (weather_id)
);   

DROP TABLE flights;
CREATE TABLE flights(
flight_id INT AUTO_INCREMENT,
flight_number VARCHAR(225),
-- departure_icao VARCHAR(225),
arrival_airport_icao VARCHAR(225),
arrival_airport_name VARCHAR(225),
scheduled_arrival_time DATETIME,
revised_arrival_time DATETIME,
airline_name VARCHAR(225),
retrieval_time DATETIME,
PRIMARY KEY (flight_id)
);
DROP TABLE airports;
CREATE TABLE airports(
arrival_airport_icao VARCHAR(225),
arrival_airport_name VARCHAR(225),
latitude decimal,
longitude decimal,
city_id int,
PRIMARY KEY (arrival_airport_icao),
FOREIGN KEY (city_id) references cities(city_id)
);   

CREATE TABLE cities_airports(
city_id INT,
arrival_airport_icao VARCHAR(225),
FOREIGN KEY (city_id) REFERENCES cities(city_id),
FOREIGN KEY (arrival_airport_icao) REFERENCES airports(arrival_airport_icao)
);

