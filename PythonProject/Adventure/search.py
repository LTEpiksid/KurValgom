import requests
import random

OVERPASS_API_URL = 'http://overpass-api.de/api/interpreter'


def search_random_restaurant():
    query = """
    [out:json];
    area["name"="Vilnius"]->.searchArea;
    node["amenity"="restaurant"]["name"](area.searchArea);
    out body;
    """
    response = requests.post(OVERPASS_API_URL, data={'data': query})
    if response.status_code == 200:
        restaurants = response.json()['elements']
        if restaurants:
            valid_restaurants = [r for r in restaurants]
            if valid_restaurants:
                return random.choice(valid_restaurants)
    return None


def search_nearby_restaurants(lat, lon, radius):
    query = f"""
    [out:json];
    node(around:{radius},{lat},{lon})["amenity"="restaurant"]["name"];
    out body;
    """
    response = requests.post(OVERPASS_API_URL, data={'data': query})
    if response.status_code == 200:
        restaurants = response.json()['elements']
        if restaurants:
            valid_restaurants = [r for r in restaurants]
            if valid_restaurants:
                return random.choice(valid_restaurants)
    return None
