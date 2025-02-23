from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import openmeteo_requests
import json
with open ('descriptions.json', 'r') as file:
    data = json.load(file)

import requests_cache
import pandas as pd
from retry_requests import retry
app = FastAPI()
# TODO: Add all descriptions for all weather codes
params = {
	"latitude": 0.00,
	"longitude": 0.00,
	"start_date": "2000-01-01",
	"end_date": "2000-01-01",
	"daily": "weather_code",
	"timezone": "GMT"
}


@app.get("/api")
def root(lat: float= 0.00, lon: float= 0.00, day: str = '2000-12-31'):
    params['longitude'] = lon
    params['latitude'] = lat
    params['start_date'] = day
    params['end_date'] = day
    code = api_call(params)
    weatherCode = code['day']['description']
    string = f'{{"day": {{"weatherCode": "{weatherCode}"}}}}'
    obj = json.loads(string)
    return code

app.mount("/",StaticFiles(directory="web", html=True),name="static")


# Setup the Open-Meteo API client with cache and retry on error

def api_call(params):
	cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
	retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
	openmeteo = openmeteo_requests.Client(session = retry_session)

	# Make sure all required weather variables are listed here
	# The order of variables in hourly or daily is important to assign them correctly below
	url = "https://archive-api.open-meteo.com/v1/archive"

	responses = openmeteo.weather_api(url, params=params)

	# Process first location. Add a for-loop for multiple locations or weather models
	response = responses[0]
	print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
	print(f"Elevation {response.Elevation()} m asl")
	#print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
	#print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

	# Process daily data. The order of variables needs to be the same as requested.
	daily = response.Daily()
	daily_weather_code = daily.Variables(0).ValuesAsNumpy()

	daily_data = {"date": pd.date_range(
		start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
		end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
		freq = pd.Timedelta(seconds = daily.Interval()),
		inclusive = "left"
	)}

	daily_data["weather_code"] = daily_weather_code

	daily_dataframe = pd.DataFrame(data = daily_data)

	wc = str(int(daily_weather_code[0]))
	return data[wc]
     
	 


