from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
from fastapi import APIRouter

router = APIRouter()
DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "properties.csv"


def _matching_locality_rows(locality: str) -> pd.DataFrame:
    df = _load_data()
    if not locality:
        return pd.DataFrame(df.iloc[0:0])
    return pd.DataFrame(df[df['locality'].astype(str).str.lower() == locality.lower()].copy())


@lru_cache(maxsize=1)
def _load_data() -> pd.DataFrame:
    df = pd.read_csv(DATASET_PATH, keep_default_na=False)
    for col in ("listing_price", "area_sqft"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _as_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


@router.post("/api/location/analyze")
async def analyze_location(payload: Dict[str, Any]) -> Dict[str, Any]:
    locality = str(payload.get('locality', 'Andheri West'))
    city = str(payload.get('city', ''))
    rows = _matching_locality_rows(locality)
    if city:
        rows = pd.DataFrame(rows[rows['city'].astype(str).str.lower() == city.lower()])
    price_per_sqft = rows['listing_price'] / rows['area_sqft'] if not rows.empty else pd.Series(dtype=float)

    first_city = None
    if not rows.empty:
        first_city = str(pd.Series(rows['city']).iloc[0])

    return {
        'locality': locality,
        'city': city or first_city,
        'location': {
            'listing_count': int(len(rows)),
            'average_price_per_sqft': round(_as_float(price_per_sqft.mean()), 2),
            'median_price_per_sqft': round(_as_float(price_per_sqft.median()), 2),
        },
        'locality_dna': {},
        'summary': (
            f'{len(rows)} source listings match {locality}; coordinates and neighborhood scores are not included in this dataset.'
            if not rows.empty
            else f'No source listings match {locality} in {city or "the selected city"}.'
        ),
    }
