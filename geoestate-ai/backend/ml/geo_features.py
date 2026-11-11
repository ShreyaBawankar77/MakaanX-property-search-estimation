import math
from typing import Dict, Tuple


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * radius_km * math.asin(math.sqrt(a))


def synthetic_amenity_features(latitude: float, longitude: float, locality: str) -> Dict[str, float]:
    base = (abs(latitude - 21.1458) + abs(longitude - 79.0882)) * 10
    return {
        "distance_to_school": max(0.2, 0.7 + base * 0.2 + (len(locality) % 3) * 0.1),
        "distance_to_hospital": max(0.3, 1.0 + base * 0.25),
        "distance_to_mall": max(0.4, 1.2 + base * 0.15),
        "distance_to_railway": max(0.5, 1.6 + base * 0.3),
        "distance_to_airport": max(2.0, 8.0 + base * 0.8),
        "amenity_count_1km": int(8 + (100 - abs(latitude - 21.1458) * 100) * 0.4),
        "amenity_count_3km": int(25 + (100 - abs(longitude - 79.0882) * 80) * 0.8),
    }


def calculate_geo_context(latitude: float, longitude: float, locality: str) -> Dict[str, float]:
    features = synthetic_amenity_features(latitude, longitude, locality)
    accessibility = 65 + (20 - min(features["distance_to_school"], 20)) * 1.5 + (20 - min(features["distance_to_mall"], 20)) * 1.1
    corridor_factor = min(1.0, max(0.0, 1.0 - (features["distance_to_railway"] / 10)))
    density = min(100.0, 30 + features["amenity_count_3km"] * 1.2)
    return {
        "distance_to_school": round(features["distance_to_school"], 2),
        "distance_to_hospital": round(features["distance_to_hospital"], 2),
        "distance_to_mall": round(features["distance_to_mall"], 2),
        "distance_to_railway": round(features["distance_to_railway"], 2),
        "distance_to_airport": round(features["distance_to_airport"], 2),
        "amenity_count_1km": int(features["amenity_count_1km"]),
        "amenity_count_3km": int(features["amenity_count_3km"]),
        "accessibility_score": round(min(100.0, max(30.0, accessibility)), 2),
        "neighborhood_density": round(min(100.0, density), 2),
        "connectivity_score": round((1.0 - corridor_factor) * 100, 2),
    }
