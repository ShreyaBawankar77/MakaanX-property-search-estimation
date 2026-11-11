from __future__ import annotations

from typing import List

import pandas as pd


def clean_and_prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    for column in [
        'bhk', 'bathrooms', 'floor', 'total_floors', 'parking', 'balcony',
        'property_age', 'area_sqft', 'carpet_area_sqft', 'listing_price',
        'locality_price_per_sqft', 'distance_to_metro', 'distance_to_school',
        'distance_to_hospital', 'distance_to_mall', 'distance_to_railway',
        'distance_to_airport', 'locality_growth_rate'
    ]:
        if column in cleaned.columns:
            num_s = pd.Series(pd.to_numeric(cleaned[column], errors='coerce'))
            median_val = float(num_s.median()) if not num_s.dropna().empty else 0.0
            cleaned[column] = num_s.fillna(median_val)

    for column in ['city', 'locality', 'property_type', 'furnishing', 'amenities']:
        if column in cleaned.columns:
            col_s = pd.Series(cleaned[column])
            cleaned[column] = col_s.fillna('Unknown').astype(str)

    base_price = cleaned['actual_price'] if 'actual_price' in cleaned.columns else cleaned['listing_price']
    cleaned['actual_price'] = pd.Series(pd.to_numeric(base_price, errors='coerce'))
    return cleaned


def get_feature_columns() -> List[str]:
    return [
        'bhk', 'bathrooms', 'area_sqft', 'carpet_area_sqft', 'floor', 'total_floors',
        'property_age', 'parking', 'balcony', 'distance_to_metro', 'distance_to_school',
        'distance_to_hospital', 'distance_to_mall', 'distance_to_railway', 'distance_to_airport',
        'locality_price_per_sqft', 'locality_growth_rate', 'accessibility_score',
        'neighborhood_density', 'connectivity_score', 'amenity_count_1km', 'amenity_count_3km',
        'amenity_score', 'locality_score'
    ]
