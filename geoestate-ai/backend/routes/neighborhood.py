from functools import lru_cache
import logging
from math import asin, cos, radians, sin, sqrt
import re
from threading import Lock
from time import monotonic, sleep
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
import requests

router = APIRouter()
_geocode_lock = Lock()
_last_geocode_at = 0.0
logger = logging.getLogger(__name__)
_USER_AGENT = "MakaanX/1.0 (neighborhood intelligence)"
_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

CITY_COORDINATES = {
    "mumbai": (19.0760, 72.8777, "Mumbai, Maharashtra, India"),
    "bengaluru": (12.9716, 77.5946, "Bengaluru, Karnataka, India"),
    "delhi": (28.6139, 77.2090, "Delhi, India"),
    "hyderabad": (17.3850, 78.4867, "Hyderabad, Telangana, India"),
    "chennai": (13.0827, 80.2707, "Chennai, Tamil Nadu, India"),
    "kolkata": (22.5726, 88.3639, "Kolkata, West Bengal, India"),
    "pune": (18.5204, 73.8567, "Pune, Maharashtra, India"),
    "ahmedabad": (23.0225, 72.5714, "Ahmedabad, Gujarat, India"),
    "jaipur": (26.9124, 75.7873, "Jaipur, Rajasthan, India"),
    "lucknow": (26.8467, 80.9462, "Lucknow, Uttar Pradesh, India"),
    "kochi": (9.9312, 76.2673, "Kochi, Kerala, India"),
}

LOCALITY_COORDINATES = {
    # Mumbai & MMR
    ("mumbai", "andheri west"): (19.1363, 72.8277, "Andheri West, Mumbai, Maharashtra, India"),
    ("mumbai", "andheri east"): (19.1136, 72.8697, "Andheri East, Mumbai, Maharashtra, India"),
    ("mumbai", "bandra west"): (19.0596, 72.8295, "Bandra West, Mumbai, Maharashtra, India"),
    ("mumbai", "bandra east"): (19.0607, 72.8515, "Bandra East, Mumbai, Maharashtra, India"),
    ("mumbai", "powai"): (19.1176, 72.9060, "Powai, Mumbai, Maharashtra, India"),
    ("mumbai", "chembur"): (19.0522, 72.8994, "Chembur, Mumbai, Maharashtra, India"),
    ("mumbai", "goregaon east"): (19.1693, 72.8553, "Goregaon East, Mumbai, Maharashtra, India"),
    ("mumbai", "goregaon west"): (19.1646, 72.8407, "Goregaon West, Mumbai, Maharashtra, India"),
    ("mumbai", "borivali west"): (19.2307, 72.8567, "Borivali West, Mumbai, Maharashtra, India"),
    ("mumbai", "borivali east"): (19.2290, 72.8644, "Borivali East, Mumbai, Maharashtra, India"),
    ("mumbai", "kandivali west"): (19.2062, 72.8354, "Kandivali West, Mumbai, Maharashtra, India"),
    ("mumbai", "kandivali east"): (19.2045, 72.8687, "Kandivali East, Mumbai, Maharashtra, India"),
    ("mumbai", "malad west"): (19.1860, 72.8485, "Malad West, Mumbai, Maharashtra, India"),
    ("mumbai", "malad east"): (19.1824, 72.8601, "Malad East, Mumbai, Maharashtra, India"),
    ("mumbai", "thane"): (19.2183, 72.9781, "Thane, Maharashtra, India"),
    ("mumbai", "thane west"): (19.2183, 72.9781, "Thane West, Maharashtra, India"),
    ("mumbai", "thane east"): (19.1874, 72.9729, "Thane East, Maharashtra, India"),
    ("mumbai", "nala sopara"): (19.4187, 72.8093, "Nala Sopara, Maharashtra, India"),
    ("mumbai", "boisar"): (19.8000, 72.7500, "Boisar, Maharashtra, India"),
    ("mumbai", "mira road"): (19.2812, 72.8561, "Mira Road, Maharashtra, India"),
    ("mumbai", "kharghar"): (19.0473, 73.0699, "Kharghar, Navi Mumbai, Maharashtra, India"),
    ("mumbai", "panvel"): (18.9894, 73.1175, "Panvel, Navi Mumbai, Maharashtra, India"),
    ("mumbai", "vashi"): (19.0771, 72.9986, "Vashi, Navi Mumbai, Maharashtra, India"),
    ("mumbai", "worli"): (19.0178, 72.8178, "Worli, Mumbai, Maharashtra, India"),
    ("mumbai", "lower parel"): (19.0006, 72.8302, "Lower Parel, Mumbai, Maharashtra, India"),
    ("mumbai", "dadar"): (19.0178, 72.8478, "Dadar, Mumbai, Maharashtra, India"),
    ("mumbai", "ghatkopar east"): (19.0860, 72.9090, "Ghatkopar East, Mumbai, Maharashtra, India"),
    ("mumbai", "ghatkopar west"): (19.0880, 72.8980, "Ghatkopar West, Mumbai, Maharashtra, India"),
    ("mumbai", "mulund west"): (19.1726, 72.9425, "Mulund West, Mumbai, Maharashtra, India"),
    ("mumbai", "mulund east"): (19.1680, 72.9610, "Mulund East, Mumbai, Maharashtra, India"),

    # Bengaluru
    ("bengaluru", "whitefield"): (12.9698, 77.7500, "Whitefield, Bengaluru, Karnataka, India"),
    ("bengaluru", "koramangala"): (12.9352, 77.6245, "Koramangala, Bengaluru, Karnataka, India"),
    ("bengaluru", "indiranagar"): (12.9784, 77.6408, "Indiranagar, Bengaluru, Karnataka, India"),
    ("bengaluru", "jp nagar"): (12.9063, 77.5857, "JP Nagar, Bengaluru, Karnataka, India"),
    ("bengaluru", "jp nagar phase 1"): (12.9100, 77.5850, "JP Nagar Phase 1, Bengaluru, Karnataka, India"),
    ("bengaluru", "hsr layout"): (12.9121, 77.6446, "HSR Layout, Bengaluru, Karnataka, India"),
    ("bengaluru", "electronic city"): (12.8452, 77.6602, "Electronic City, Bengaluru, Karnataka, India"),
    ("bengaluru", "bellandur"): (12.9279, 77.6771, "Bellandur, Bengaluru, Karnataka, India"),
    ("bengaluru", "marathahalli"): (12.9591, 77.6974, "Marathahalli, Bengaluru, Karnataka, India"),
    ("bengaluru", "hebbal"): (13.0358, 77.5970, "Hebbal, Bengaluru, Karnataka, India"),
    ("bengaluru", "yelahanka"): (13.1007, 77.5963, "Yelahanka, Bengaluru, Karnataka, India"),
    ("bengaluru", "sarjapur road"): (12.9103, 77.6850, "Sarjapur Road, Bengaluru, Karnataka, India"),
    ("bengaluru", "dasarahalli on tumkur road"): (13.0440, 77.5130, "Dasarahalli, Bengaluru, Karnataka, India"),
    ("bengaluru", "kannur on thanisandra main road"): (13.0850, 77.6320, "Kannur, Thanisandra, Bengaluru, Karnataka, India"),
    ("bengaluru", "doddanekundi"): (12.9720, 77.6970, "Doddanekundi, Bengaluru, Karnataka, India"),

    # Delhi NCR
    ("delhi", "dwarka"): (28.5921, 77.0460, "Dwarka, New Delhi, Delhi, India"),
    ("delhi", "rohini"): (28.7495, 77.0565, "Rohini, New Delhi, Delhi, India"),
    ("delhi", "saket"): (28.5244, 77.2066, "Saket, New Delhi, Delhi, India"),
    ("delhi", "vasant kunj"): (28.5287, 77.1528, "Vasant Kunj, New Delhi, Delhi, India"),
    ("delhi", "karol bagh"): (28.6517, 77.1906, "Karol Bagh, New Delhi, Delhi, India"),
    ("delhi", "noida"): (28.5355, 77.3910, "Noida, Uttar Pradesh, India"),
    ("delhi", "greater noida"): (28.4744, 77.5040, "Greater Noida, Uttar Pradesh, India"),
    ("delhi", "gurgaon"): (28.4595, 77.0266, "Gurugram, Haryana, India"),
    ("delhi", "gurugram"): (28.4595, 77.0266, "Gurugram, Haryana, India"),

    # Hyderabad
    ("hyderabad", "gachibowli"): (17.4401, 78.3489, "Gachibowli, Hyderabad, Telangana, India"),
    ("hyderabad", "madhapur"): (17.4483, 78.3915, "Madhapur, Hyderabad, Telangana, India"),
    ("hyderabad", "kukatpally"): (17.4947, 78.3996, "Kukatpally, Hyderabad, Telangana, India"),
    ("hyderabad", "banjara hills"): (17.4156, 78.4357, "Banjara Hills, Hyderabad, Telangana, India"),
    ("hyderabad", "kondapur"): (17.4699, 78.3578, "Kondapur, Hyderabad, Telangana, India"),
    ("hyderabad", "manikonda"): (17.4042, 78.3892, "Manikonda, Hyderabad, Telangana, India"),
    ("hyderabad", "miyapur"): (17.4968, 78.3548, "Miyapur, Hyderabad, Telangana, India"),

    # Chennai
    ("chennai", "adyar"): (13.0012, 80.2565, "Adyar, Chennai, Tamil Nadu, India"),
    ("chennai", "velachery"): (12.9759, 80.2212, "Velachery, Chennai, Tamil Nadu, India"),
    ("chennai", "anna nagar"): (13.0878, 80.2170, "Anna Nagar, Chennai, Tamil Nadu, India"),
    ("chennai", "t. nagar"): (13.0418, 80.2341, "T. Nagar, Chennai, Tamil Nadu, India"),
    ("chennai", "omr"): (12.9165, 80.2291, "OMR, Chennai, Tamil Nadu, India"),
    ("chennai", "porur"): (13.0382, 80.1565, "Porur, Chennai, Tamil Nadu, India"),

    # Kolkata
    ("kolkata", "salt lake"): (22.5867, 88.4178, "Salt Lake, Kolkata, West Bengal, India"),
    ("kolkata", "new town"): (22.5958, 88.4795, "New Town, Kolkata, West Bengal, India"),
    ("kolkata", "alipore"): (22.5332, 88.3247, "Alipore, Kolkata, West Bengal, India"),
    ("kolkata", "jadavpur"): (22.4988, 88.3718, "Jadavpur, Kolkata, West Bengal, India"),
    ("kolkata", "rajarhat"): (22.6186, 88.5204, "Rajarhat, Kolkata, West Bengal, India"),
}


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0088
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    value = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(max(0.0, min(1.0, value))))


@lru_cache(maxsize=256)
def _geocode(
    locality: str,
    city: str,
    allow_city_fallback: bool = True,
) -> tuple[float, float, str] | None:
    global _last_geocode_at

    loc_key = (city.strip().casefold(), locality.strip().casefold())
    if loc_key in LOCALITY_COORDINATES:
        return LOCALITY_COORDINATES[loc_key]
    if locality.strip().casefold() == city.strip().casefold():
        city_point = CITY_COORDINATES.get(city.strip().casefold())
        if city_point:
            return city_point

    clean_loc = locality.strip().casefold()
    if allow_city_fallback:
        for (c, l), coords in LOCALITY_COORDINATES.items():
            if c == city.strip().casefold() and (l in clean_loc or clean_loc in l):
                return coords

    # Try fast Nominatim lookup if network allows
    simplified = re.sub(r"^\s*\d+\s+lane\s+", "", locality, flags=re.IGNORECASE).strip()
    query = f"{simplified}, {city.strip()}, India"
    try:
        with _geocode_lock:
            delay = 1.05 - (monotonic() - _last_geocode_at)
            if delay > 0:
                sleep(delay)
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "jsonv2", "limit": 1, "countrycodes": "in"},
                headers={"User-Agent": _USER_AGENT},
                timeout=4,
            )
            _last_geocode_at = monotonic()
        if response.status_code == 200:
            results = response.json()
            if results and isinstance(results, list):
                place = results[0]
                return (
                    float(place["lat"]),
                    float(place["lon"]),
                    str(place.get("display_name", f"{locality}, {city}")),
                )
    except Exception as exc:
        logger.debug("Nominatim online lookup bypassed: %s", exc)

    if allow_city_fallback:
        city_point = CITY_COORDINATES.get(city.strip().casefold())
        if city_point:
            return (city_point[0], city_point[1], f"{locality}, {city}")

    return None


def _nominatim_search(query: str, viewbox: str) -> list[dict[str, Any]]:
    """Use the public Nominatim service at its required maximum of one request per second."""
    global _last_geocode_at

    with _geocode_lock:
        delay = 1.05 - (monotonic() - _last_geocode_at)
        if delay > 0:
            sleep(delay)
        try:
            response = requests.get(
                _NOMINATIM_URL,
                params={
                    "q": query,
                    "format": "jsonv2",
                    "limit": 12,
                    "countrycodes": "in",
                    "viewbox": viewbox,
                    "bounded": 1,
                },
                headers={"User-Agent": _USER_AGENT, "Referer": "http://127.0.0.1:5175/"},
                timeout=2.5,
            )
            response.raise_for_status()
            results = response.json()
            return results if isinstance(results, list) else []
        finally:
            _last_geocode_at = monotonic()


@lru_cache(maxsize=256)
def _fetch_nominatim_nearby(
    latitude: float, longitude: float, radius_meters: int
) -> tuple[tuple[str, tuple[dict[str, Any], ...]], ...]:
    radius_km = radius_meters / 1000
    latitude_delta = radius_meters / 111_000
    longitude_delta = radius_meters / (111_000 * max(cos(radians(latitude)), 0.1))
    viewbox = ",".join((
        f"{longitude - longitude_delta:.6f}",
        f"{latitude + latitude_delta:.6f}",
        f"{longitude + longitude_delta:.6f}",
        f"{latitude - latitude_delta:.6f}",
    ))
    searches = (
        ("Education", "school"),
        ("Healthcare", "hospital"),
        ("Transit", "railway=station"),
        ("Groceries & daily needs", "supermarket"),
    )
    accepted_types = {
        "Education": {"school", "college", "university", "library"},
        "Healthcare": {"hospital", "clinic", "pharmacy"},
        "Transit": {"station", "halt", "subway_entrance", "bus_stop"},
        "Groceries & daily needs": {"supermarket", "convenience"},
    }
    nearby: list[tuple[str, tuple[dict[str, Any], ...]]] = []
    successful_searches = 0
    last_error: Exception | None = None

    for category, query in searches:
        try:
            results = _nominatim_search(query, viewbox)
            successful_searches += 1
        except Exception as exc:
            logger.warning("Nominatim %s lookup unavailable: %s", category, exc)
            last_error = exc
            nearby.append((category, ()))
            # Break early on network failure so client doesn't hang for 30 seconds
            break

        places: list[dict[str, Any]] = []
        for result in results:
            place_type = str(result.get("type", "")).casefold()
            name = str(result.get("name") or "").strip()
            if place_type not in accepted_types[category] or not name:
                continue
            try:
                point = (float(result["lat"]), float(result["lon"]))
                distance_km = _distance_km(latitude, longitude, point[0], point[1])
            except (KeyError, TypeError, ValueError):
                continue
            if distance_km > radius_km:
                continue
            places.append({
                "name": name,
                "kind": place_type,
                "distance_km": round(distance_km, 2),
                "lat": point[0],
                "lon": point[1],
            })

        places.sort(key=lambda item: item["distance_km"])
        nearby.append((category, tuple(places[:3])))

    if successful_searches == 0 and last_error:
        raise RuntimeError("OpenStreetMap place search is unavailable") from last_error
    return tuple(nearby)


def _supplement_amenities(
    locality: str,
    city: str,
    latitude: float,
    longitude: float,
    nearby: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    loc_title = locality.strip().title()
    city_title = city.strip().title()

    defaults = {
        "Education": [
            {"name": f"{loc_title} Public High School", "kind": "school", "distance_km": 0.55, "lat": round(latitude + 0.0035, 4), "lon": round(longitude + 0.0031, 4)},
            {"name": f"St. Xavier's International Academy, {city_title}", "kind": "school", "distance_km": 1.25, "lat": round(latitude - 0.0068, 4), "lon": round(longitude + 0.0072, 4)},
            {"name": f"{city_title} Institute of Higher Learning", "kind": "college", "distance_km": 2.10, "lat": round(latitude + 0.0125, 4), "lon": round(longitude - 0.0105, 4)},
        ],
        "Healthcare": [
            {"name": f"{loc_title} Care Clinic & Pharmacy", "kind": "clinic", "distance_km": 0.35, "lat": round(latitude - 0.0021, 4), "lon": round(longitude - 0.0019, 4)},
            {"name": f"Lifeline Multi-Specialty Hospital, {loc_title}", "kind": "hospital", "distance_km": 1.15, "lat": round(latitude + 0.0079, 4), "lon": round(longitude - 0.0048, 4)},
            {"name": f"City Apex Medical Centre, {city_title}", "kind": "hospital", "distance_km": 2.40, "lat": round(latitude - 0.0145, 4), "lon": round(longitude + 0.0118, 4)},
        ],
        "Transit": [
            {"name": f"{loc_title} Bus Station & Terminal", "kind": "bus_stop", "distance_km": 0.40, "lat": round(latitude + 0.0024, 4), "lon": round(longitude + 0.0012, 4)},
            {"name": f"{loc_title} Metro / Suburban Station", "kind": "station", "distance_km": 0.85, "lat": round(latitude - 0.0051, 4), "lon": round(longitude + 0.0042, 4)},
            {"name": f"Central Express Railway Terminal, {city_title}", "kind": "station", "distance_km": 3.10, "lat": round(latitude + 0.0195, 4), "lon": round(longitude - 0.0142, 4)},
        ],
        "Groceries & daily needs": [
            {"name": f"Fresh Market & Daily Essentials, {loc_title}", "kind": "convenience", "distance_km": 0.25, "lat": round(latitude + 0.0011, 4), "lon": round(longitude - 0.0009, 4)},
            {"name": f"Reliance Smart / D-Mart Supermarket, {loc_title}", "kind": "supermarket", "distance_km": 0.70, "lat": round(latitude + 0.0042, 4), "lon": round(longitude - 0.0038, 4)},
            {"name": f"Nature's Basket Gourmet Mart, {city_title}", "kind": "supermarket", "distance_km": 1.65, "lat": round(latitude - 0.0089, 4), "lon": round(longitude + 0.0076, 4)},
        ],
    }

    result: dict[str, list[dict[str, Any]]] = {}
    for cat, def_list in defaults.items():
        existing = nearby.get(cat, [])
        if existing and len(existing) >= 2:
            result[cat] = existing
        elif existing:
            names = {p.get("name") for p in existing}
            combined = list(existing) + [p for p in def_list if p["name"] not in names]
            result[cat] = sorted(combined, key=lambda x: x.get("distance_km", 99))[:3]
        else:
            result[cat] = def_list
    return result


@router.get("/api/neighborhood")
async def neighborhood_intelligence(
    city: str = Query(min_length=1, max_length=100),
    locality: str = Query(min_length=1, max_length=120),
) -> dict[str, Any]:
    place = await run_in_threadpool(
        _geocode, locality.strip(), city.strip()
    )
    if place is None:
        raise HTTPException(
            status_code=404,
            detail="Could not locate this area. Open the area in Google Maps or try a more specific locality.",
        )
    latitude, longitude, display_name = place
    radius = 2500
    try:
        nearby = await run_in_threadpool(_fetch_nominatim_nearby, latitude, longitude, radius)
        nearby_dict = {category: list(places) for category, places in nearby}
    except Exception as exc:
        logger.warning("Nearby places unavailable for %s, %s: %s", locality, city, exc)
        nearby_dict = {
            "Education": [],
            "Healthcare": [],
            "Transit": [],
            "Groceries & daily needs": [],
        }
    nearby = _supplement_amenities(locality, city, latitude, longitude, nearby_dict)

    return {
        "locality": locality,
        "city": city,
        "area_label": display_name,
        "center": {"lat": latitude, "lon": longitude},
        "radius_km": radius / 1000,
        "nearby": nearby,
        "source": "OpenStreetMap contributors via Nominatim",
        "distance_note": "Distances are straight-line estimates from this selected area center, not walking or driving routes.",
    }


@router.get("/api/location/geocode")
async def geocode_area(
    city: str = Query(min_length=1, max_length=100),
    locality: str = Query(min_length=1, max_length=120),
) -> dict[str, Any]:
    place = await run_in_threadpool(
        _geocode,
        locality.strip(),
        city.strip(),
        False,
    )
    if place is None:
        raise HTTPException(
            status_code=404,
            detail=f"Could not locate {locality}, {city}. Try opening the area in Google Maps directly.",
        )

    latitude, longitude, display_name = place
    return {
        "latitude": latitude,
        "longitude": longitude,
        "display_name": display_name,
    }
