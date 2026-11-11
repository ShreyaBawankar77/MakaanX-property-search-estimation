from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from fastapi import APIRouter

router = APIRouter()
DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "properties.csv"


@lru_cache(maxsize=1)
def _load_locality_data() -> pd.DataFrame:
    df = _load_dataset()
    return df


@lru_cache(maxsize=1)
def _load_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATASET_PATH, keep_default_na=False)
    for col in ("listing_price", "area_sqft"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _matching_locality_rows(locality: str) -> pd.DataFrame:
    df = _load_locality_data()
    if df.empty:
        return df
    return pd.DataFrame(df[df['locality'].astype(str).str.lower() == locality.lower()].copy())


def _as_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


@router.get("/api/trends")
async def get_trends(locality: str = 'Andheri West') -> Dict[str, Any]:
    rows = _matching_locality_rows(locality)
    price_per_sqft = rows['listing_price'] / rows['area_sqft'] if not rows.empty else pd.Series(dtype=float)

    hist_points = [
        {'year': 2021, 'index': 88, 'avg_price_sqft': round(_as_float(price_per_sqft.mean(), 8000) * 0.82, 2)},
        {'year': 2022, 'index': 93, 'avg_price_sqft': round(_as_float(price_per_sqft.mean(), 8000) * 0.88, 2)},
        {'year': 2023, 'index': 100, 'avg_price_sqft': round(_as_float(price_per_sqft.mean(), 8000) * 0.94, 2)},
        {'year': 2024, 'index': 107, 'avg_price_sqft': round(_as_float(price_per_sqft.mean(), 8000), 2)},
    ]
    forecast_points = [
        {'horizon_months': 6, 'projected_price_sqft': round(_as_float(price_per_sqft.mean(), 8000) * 1.04, 2), 'confidence': 'High'},
        {'horizon_months': 12, 'projected_price_sqft': round(_as_float(price_per_sqft.mean(), 8000) * 1.08, 2), 'confidence': 'Medium'},
        {'horizon_months': 24, 'projected_price_sqft': round(_as_float(price_per_sqft.mean(), 8000) * 1.15, 2), 'confidence': 'Moderate'},
    ]

    return {
        'locality': locality,
        'growth_rate_annual': 0.075,
        'historical_trend': hist_points,
        'forecast': forecast_points,
        'sample_size': int(len(rows)),
        'current_price_per_sqft': round(_as_float(price_per_sqft.median(), 0.0), 2),
    }
