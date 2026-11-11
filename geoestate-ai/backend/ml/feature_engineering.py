from __future__ import annotations

from typing import Dict, Any

from backend.ml.geo_features import calculate_geo_context


def build_feature_vector(record: Dict[str, Any]) -> Dict[str, float]:
    geo = calculate_geo_context(float(record.get('latitude', 21.1458)), float(record.get('longitude', 79.0882)), str(record.get('locality', 'Dharampeth')))
    feature_vector = {
        "city_code": 1 if str(record.get('city', '')).lower() == 'nagpur' else 0,
        "locality_score": min(100.0, 50 + float(record.get('locality_price_per_sqft', 7000)) / 80),
        "bhk": float(record.get('bhk', 2)),
        "bathrooms": float(record.get('bathrooms', 2)),
        "area_sqft": float(record.get('area_sqft', 1100)),
        "carpet_area_sqft": float(record.get('carpet_area_sqft', 1000)),
        "floor": float(record.get('floor', 4)),
        "total_floors": float(record.get('total_floors', 8)),
        "property_age": float(record.get('property_age', 5)),
        "parking": float(record.get('parking', 1)),
        "balcony": float(record.get('balcony', 1)),
        "distance_to_metro": float(record.get('distance_to_metro', 1.2)),
        "distance_to_school": float(record.get('distance_to_school', geo['distance_to_school'])),
        "distance_to_hospital": float(record.get('distance_to_hospital', geo['distance_to_hospital'])),
        "distance_to_mall": float(record.get('distance_to_mall', geo['distance_to_mall'])),
        "distance_to_railway": float(record.get('distance_to_railway', geo['distance_to_railway'])),
        "distance_to_airport": float(record.get('distance_to_airport', geo['distance_to_airport'])),
        "locality_price_per_sqft": float(record.get('locality_price_per_sqft', 7000)),
        "locality_growth_rate": float(record.get('locality_growth_rate', 0.08)),
        "accessibility_score": float(record.get('accessibility_score', geo['accessibility_score'])),
        "neighborhood_density": float(record.get('neighborhood_density', geo['neighborhood_density'])),
        "connectivity_score": float(record.get('connectivity_score', geo['connectivity_score'])),
        "amenity_count_1km": float(record.get('amenity_count_1km', geo['amenity_count_1km'])),
        "amenity_count_3km": float(record.get('amenity_count_3km', geo['amenity_count_3km'])),
        "amenity_score": 60 + min(40, float(record.get('amenity_count_3km', geo['amenity_count_3km'])) * 0.7),
        "listing_price": float(record.get('listing_price', 0)) or 0.0,
    }
    return feature_vector


def compute_locality_dna(locality_metrics: Dict[str, float]) -> Dict[str, float]:
    connectivity = float(locality_metrics.get('connectivity', 87))
    education = float(locality_metrics.get('education', 84))
    healthcare = float(locality_metrics.get('healthcare', 82))
    shopping = float(locality_metrics.get('shopping', 86))
    transport = float(locality_metrics.get('transport', 88))
    employment = float(locality_metrics.get('employment', 80))
    recreation = float(locality_metrics.get('recreation', 75))
    safety = float(locality_metrics.get('safety', 81))
    development = float(locality_metrics.get('development', 84))
    price_stability = float(locality_metrics.get('price_stability', 79))
    total = (
        connectivity + education + healthcare + shopping + transport + employment + recreation + safety + development + price_stability
    ) / 10
    return {
        "locality_dna": round(total, 2),
        "connectivity": round(connectivity, 2),
        "education": round(education, 2),
        "healthcare": round(healthcare, 2),
        "shopping": round(shopping, 2),
        "transport": round(transport, 2),
        "employment": round(employment, 2),
        "recreation": round(recreation, 2),
        "safety": round(safety, 2),
        "development": round(development, 2),
        "price_stability": round(price_stability, 2),
    }
