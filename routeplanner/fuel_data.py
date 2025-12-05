import csv
from dataclasses import dataclass
from functools import lru_cache
from typing import List
from django.conf import settings


@dataclass
class GasStation:
    station_id: str
    name: str
    lat: float
    lng: float
    price: float
    city: str | None = None
    state: str | None = None
    route_mile: float | None = None


@lru_cache(maxsize=1)
def load_gas_stations() -> List[GasStation]:
    """Load gas stations from CSV once per process (fast after first)."""
    stations: List[GasStation] = []
    path = settings.FUEL_PRICE_FILE
    if not path:
        return stations

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                stations.append(
                    GasStation(
                        station_id=row.get("station_id") or row.get("id") or "",
                        name=row.get("name", "Unknown"),
                        lat=float(row["lat"]),
                        lng=float(row["lng"]),
                        price=float(row["price"]),
                        city=row.get("city"),
                        state=row.get("state"),
                    )
                )
            except (KeyError, ValueError):
                continue

    return stations
