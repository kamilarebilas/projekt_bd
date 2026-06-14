import json 
import time 
from urllib.parse import urlencode 
from urllib.request import urlopen 
from sqlalchemy import text 
from db import get_engine 

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast" 
AIR_QUALITY_API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality" 
TIMEZONE = "Europe/Warsaw" 

def fetch_json(url, params): 
    query_string = urlencode(params) 
    full_url = f"{url}?{query_string}" 
    
    with urlopen(full_url, timeout=30) as response: 
        data = response.read().decode("utf-8") 
        return json.loads(data) 
    

def get_locations(engine): 
    query = text(""" SELECT id, city_name, latitude, longitude 
                 FROM locations 
                 ORDER BY id; """) 
    
    with engine.connect() as connection: 
        rows = connection.execute(query).mappings().all() 
        
    return [ 
        { 
            "id": row["id"], 
            "city_name": row["city_name"], 
            "latitude": float(row["latitude"]), 
            "longitude": float(row["longitude"]), 
            } 
            for row in rows 
            ] 
    

def get_value(data, key, index): 
    values = data.get(key) or [] 
    if index >= len(values): 
        return None 
    return values[index]