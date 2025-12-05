import math
from typing import List, Tuple
from .fuel_data import GasStation, load_gas_stations

EARTH_RADIUS_MILES = 3958.8


def haversine_miles(lat1, lon1, lat2, lon2) -> float:
    """Distance between two lat/lngs in miles."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


def build_route_cumulative_miles(coords: List[Tuple[float, float]]) -> List[float]:
    """Return cumulative miles along route coordinates."""
    cum = [0.0]
    for i in range(1, len(coords)):
        lon1, lat1 = coords[i - 1]
        lon2, lat2 = coords[i]
        cum.append(cum[-1] + haversine_miles(lat1, lon1, lat2, lon2))
    return cum


def project_stations_onto_route(
    route_coords: List[Tuple[float, float]],
    cum_miles: List[float],
    max_detour_miles: float = 100.0,  
) -> List[GasStation]:

    stations = load_gas_stations()
    projected: List[GasStation] = []

    for s in stations:
        best_dist = float("inf")
        best_idx = None
        for i, (lon, lat) in enumerate(route_coords):
            d = haversine_miles(s.lat, s.lng, lat, lon)
            if d < best_dist:
                best_dist = d
                best_idx = i

        if best_idx is not None and best_dist <= max_detour_miles:
            s_copy = GasStation(
                station_id=s.station_id,
                name=s.name,
                lat=s.lat,
                lng=s.lng,
                price=s.price,
                city=s.city,
                state=s.state,
                route_mile=cum_miles[best_idx],
            )
            projected.append(s_copy)

    projected.sort(key=lambda x: x.route_mile or 0)
    return projected


def plan_fuel_stops(
    total_distance_miles: float,
    route_coords: List[Tuple[float, float]],
    cum_miles: List[float],
    vehicle_range_miles: float = 500.0,
    mpg: float = 10.0,
):
    stations = project_stations_onto_route(route_coords, cum_miles)

    if not stations:
        gallons = total_distance_miles / mpg
        return {
            "total_gallons": round(gallons, 2),
            "total_cost": None,
            "stops": [],
        }

    windows = []
    start = 0.0

    while start < total_distance_miles:
        end = min(start + vehicle_range_miles, total_distance_miles)
        windows.append((start, end))
        start = end

    stops = []
    total_cost = 0.0
    total_gallons = total_distance_miles / mpg

    for idx, (w_start, w_end) in enumerate(windows):

        cand = [
            s for s in stations
            if s.route_mile is not None and (w_start - 200) <= s.route_mile <= (w_end + 200)
        ]

        if not cand:
            cand = stations

        best = min(cand, key=lambda s: s.price)

        window_distance = w_end - w_start
        gallons = window_distance / mpg
        cost = gallons * best.price
        total_cost += cost

        stops.append({
            "segment_index": idx,
            "route_mile": round(best.route_mile, 2),
            "gallons": round(gallons, 2),
            "cost": round(cost, 2),
            "price_per_gallon": best.price,
            "station": {
                "id": best.station_id,
                "name": best.name,
                "city": best.city,
                "state": best.state,
                "lat": best.lat,
                "lng": best.lng,
            },
            "segment_range_miles": {
                "start": round(w_start, 2),
                "end": round(w_end, 2),
            }
        })

    return {
        "total_gallons": round(total_gallons, 2),
        "total_cost": round(total_cost, 2),
        "stops": stops,
    }
