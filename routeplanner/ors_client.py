import requests
from typing import Any, Dict, List, Tuple
from django.conf import settings


class RoutingError(Exception):
    pass


def get_route_geojson(start: Tuple[float, float], end: Tuple[float, float]) -> Dict[str, Any]:
    """
    Call ORS Directions API once and return GeoJSON FeatureCollection.
    Start/end are (lng, lat).
    """
    api_key = settings.ORS_API_KEY
    if not api_key:
        raise RoutingError("ORS_API_KEY is not configured")

    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"

    payload = {
        "coordinates": [
            [start[0], start[1]],
            [end[0], end[1]],
        ]
    }

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json, application/geo+json",
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=8)
    if resp.status_code != 200:
        raise RoutingError(f"ORS error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    return data


def extract_route_info(geojson: Dict[str, Any]):
    """
    From ORS GeoJSON response, extract:
      - distance in miles
      - duration in hours
      - coordinates (lon, lat) list
    """
    try:
        feature = geojson["features"][0]
        props = feature["properties"]["summary"]
        distance_m = props["distance"]          # meters
        duration_s = props["duration"]          # seconds
        coords: List[Tuple[float, float]] = feature["geometry"]["coordinates"]
    except (KeyError, IndexError, TypeError) as e:
        raise RoutingError(f"Malformed ORS response: {e}")

    distance_miles = distance_m * 0.000621371
    duration_hours = duration_s / 3600.0
    return distance_miles, duration_hours, coords
