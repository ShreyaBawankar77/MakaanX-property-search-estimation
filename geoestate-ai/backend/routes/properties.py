from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Response

router = APIRouter()
DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "properties.csv"


@lru_cache(maxsize=1)
def _load_properties() -> pd.DataFrame:
    rows = pd.read_csv(DATASET_PATH, keep_default_na=False)
    # Keep price comparisons numeric and predictable even if a CSV refresh
    # contains blank or malformed price/size values.
    for column in ("listing_price", "actual_price", "area_sqft", "bhk", "resale"):
        if column in rows.columns:
            rows[column] = pd.to_numeric(rows[column], errors="coerce")
    # Guarantee only unique properties are loaded (drop duplicate listings)
    rows = rows.drop_duplicates(subset=["city", "locality", "bhk", "area_sqft", "listing_price"], keep="first")
    return rows


@lru_cache(maxsize=1)
def _price_per_sqft_benchmarks() -> dict[tuple[str, int], float]:
    rows = _load_properties().copy()
    rows["price_per_sqft"] = rows["listing_price"] / rows["area_sqft"]
    medians = rows.groupby(["city", "bhk"])["price_per_sqft"].median()
    benchmarks = {}
    for (city, bhk), value in medians.items():
        benchmarks[(str(city), int(bhk))] = float(value)
        benchmarks[(str(city).strip().casefold(), int(bhk))] = float(value)
    return benchmarks


def _filter_properties(
    city: str | None = None,
    locality: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    bhk: int | None = None,
    resale: int | None = None,
    area_sqft: float | None = None,
    area_tolerance: float = 0.2,
    amenities: str | None = None,
) -> pd.DataFrame:
    rows = _load_properties()
    if city and city.strip():
        city_norm = city.strip().casefold()
        rows = rows[rows["city"].astype(str).str.strip().str.casefold() == city_norm]
    if locality and locality.strip():
        loc_clean = locality.strip().casefold()
        loc_alnum = "".join(ch for ch in loc_clean if ch.isalnum())
        direct_mask = rows["locality"].astype(str).str.strip().str.casefold() == loc_clean
        alnum_mask = rows["locality"].astype(str).apply(lambda s: "".join(ch for ch in str(s).lower() if ch.isalnum())) == loc_alnum
        rows = rows[direct_mask | alnum_mask]
    if max_price is not None:
        try:
            p_val = float(max_price)
            rows = rows[rows["listing_price"] <= p_val]
        except (ValueError, TypeError):
            pass
    if min_price is not None:
        try:
            p_val = float(min_price)
            rows = rows[rows["listing_price"] >= p_val]
        except (ValueError, TypeError):
            pass
    if bhk is not None:
        try:
            bhk_val = int(bhk)
            if bhk_val > 0:
                rows = rows[rows["bhk"] == bhk_val]
        except (ValueError, TypeError):
            pass
    if resale is not None:
        try:
            resale_val = int(resale)
            rows = rows[rows["resale"] == resale_val]
        except (ValueError, TypeError):
            pass
    if area_sqft is not None:
        try:
            area_val = float(area_sqft)
            if area_val > 0:
                rows = rows[
                    rows["area_sqft"].between(
                        area_val * (1 - area_tolerance),
                        area_val * (1 + area_tolerance),
                    )
                ]
        except (ValueError, TypeError):
            pass
    if amenities:
        for amenity in (value.strip() for value in amenities.split(",") if value.strip()):
            rows = rows[rows["amenities"].str.contains(amenity, case=False, regex=False)]
    return rows


@router.get("/api/properties/options")
def property_options(
    city: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    bhk: int | None = None,
    resale: int | None = None,
    area_sqft: float | None = None,
    area_tolerance: float = Query(default=0.2, ge=0, le=1),
    amenities: str | None = None,
) -> dict[str, list[str]]:
    rows = _load_properties()
    localities = _filter_properties(
        city=city,
        max_price=max_price,
        min_price=min_price,
        bhk=bhk,
        resale=resale,
        area_sqft=area_sqft,
        area_tolerance=area_tolerance,
        amenities=amenities,
    )
    return {
        "cities": sorted(rows["city"].dropna().unique().tolist()),
        "localities": sorted(localities["locality"].dropna().unique().tolist()),
    }


@router.get("/api/budget/coach")
def budget_coach(
    city: str | None = None,
    locality: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    bhk: int | None = None,
    resale: int | None = None,
    area_sqft: float | None = None,
    area_tolerance: float = Query(default=0.2, ge=0, le=1),
    amenities: str | None = None,
) -> dict[str, Any]:
    base_filters = {
        "city": city,
        "locality": locality,
        "bhk": bhk,
        "resale": resale,
        "area_sqft": area_sqft,
        "area_tolerance": area_tolerance,
        "amenities": amenities,
    }
    comparable_homes = _filter_properties(**base_filters)
    price_filters = {**base_filters, "min_price": min_price}
    within_budget = comparable_homes
    if min_price is not None:
        within_budget = within_budget[within_budget["listing_price"] >= min_price]
    if max_price is not None:
        within_budget = within_budget[within_budget["listing_price"] <= max_price]

    tradeoff_options = [
        (
            "any_area",
            f"Search all areas in {city}" if city else "Search all areas",
            {**price_filters, "locality": None},
            max_price,
        ),
        (
            "any_bhk",
            "Include all BHK types",
            {**price_filters, "bhk": None},
            max_price,
        ),
        (
            "all_home_types",
            "Include new and pre-owned homes",
            {**price_filters, "resale": None},
            max_price,
        ),
        (
            "wider_size_range",
            "Include homes a little smaller or larger",
            {**price_filters, "area_tolerance": min(area_tolerance + 0.15, 1.0)},
            max_price,
        ),
        (
            "fewer_features",
            "Make selected home features optional",
            {**price_filters, "amenities": None},
            max_price,
        ),
        (
            "slightly_higher_budget",
            "Increase your budget by 10%",
            price_filters,
            max_price * 1.1 if max_price is not None else None,
        ),
    ]

    unbudgeted_matches = _filter_properties(**price_filters)
    if max_price is not None and not unbudgeted_matches.empty:
        next_price = float(unbudgeted_matches["listing_price"].min())
        if next_price > max_price:
            tradeoff_options.append(
                (
                    "budget_for_next_match",
                    "Raise budget to the lowest matching listing",
                    price_filters,
                    next_price,
                )
            )

    tradeoffs = []
    for key, label, filters, budget_limit in tradeoff_options:
        matches = _filter_properties(**filters)
        if budget_limit is not None:
            matches = matches[matches["listing_price"] <= budget_limit]
        additional = len(matches) - len(within_budget)
        if additional > 0:
            tradeoffs.append(
                {
                    "key": key,
                    "label": label,
                    "additional_homes": additional,
                    "filters": {
                        "city": filters["city"],
                        "locality": filters["locality"],
                        "bhk": filters["bhk"],
                        "resale": filters["resale"],
                        "area_sqft": filters["area_sqft"],
                        "area_tolerance": filters["area_tolerance"],
                        "amenities": filters["amenities"] or "",
                        "min_price": min_price,
                        "max_price": budget_limit,
                    },
                }
            )

    comparable_count = len(comparable_homes)
    budget_fit = round(len(within_budget) / comparable_count * 100) if comparable_count else 0
    median_price = round(float(comparable_homes["listing_price"].median())) if comparable_count else None
    return {
        "comparable_homes": comparable_count,
        "within_budget": len(within_budget),
        "budget_fit_percent": budget_fit,
        "median_comparable_price": median_price,
        "tradeoffs": tradeoffs,
    }


@router.get("/api/properties")
def list_properties(
    response: Response,
    city: str | None = None,
    locality: str | None = None,
    max_price: float | None = Query(default=None, ge=0),
    min_price: float | None = Query(default=None, ge=0),
    bhk: int | None = None,
    resale: int | None = None,
    area_sqft: float | None = None,
    area_tolerance: float = Query(default=0.2, ge=0, le=1),
    amenities: str | None = None,
    limit: int = Query(default=24, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=422, detail="Minimum price cannot exceed maximum price.")

    rows = _filter_properties(
        city=city,
        locality=locality,
        min_price=min_price,
        max_price=max_price,
        bhk=bhk,
        resale=resale,
        area_sqft=area_sqft,
        area_tolerance=area_tolerance,
        amenities=amenities,
    )
    if max_price is not None:
        rows = rows[pd.to_numeric(rows["listing_price"], errors="coerce") <= max_price]
    if min_price is not None:
        rows = rows[pd.to_numeric(rows["listing_price"], errors="coerce") >= min_price]
    response.headers["X-Total-Count"] = str(len(rows))
    if len(rows) == 0:
        # Provide context headers so the frontend can display helpful fallback alternatives
        if locality:
            loc_matches = _filter_properties(city=city, locality=locality)
            if not loc_matches.empty:
                response.headers["X-Min-Price-In-Locality"] = str(round(float(loc_matches["listing_price"].min())))
                response.headers["X-Total-In-Locality"] = str(len(loc_matches))
        if city and max_price:
            city_matches = _filter_properties(city=city, max_price=max_price)
            response.headers["X-Total-In-City-Under-Budget"] = str(len(city_matches))
    rows = rows.sort_values("listing_price", ascending=True).iloc[offset:offset + limit]
    benchmarks = _price_per_sqft_benchmarks()
    properties = rows.to_dict(orient="records")
    for item in properties:
        listing_p = float(item["listing_price"]) if pd.notna(item.get("listing_price")) else 0.0
        area = max(float(item["area_sqft"]), 1.0) if pd.notna(item.get("area_sqft")) and float(item["area_sqft"]) > 0 else 1.0
        price_per_sqft = listing_p / area
        bhk_val = int(item["bhk"]) if pd.notna(item.get("bhk")) else 2
        city_str = str(item.get("city", "")).strip()
        benchmark = benchmarks.get((city_str, bhk_val)) or benchmarks.get((city_str.casefold(), bhk_val))
        item["price_per_sqft"] = round(price_per_sqft, 2)
        item["city_bhk_median_price_per_sqft"] = round(benchmark, 2) if benchmark else None
        item["price_vs_city_bhk_median_percent"] = (
            round((price_per_sqft / benchmark - 1) * 100, 1) if benchmark else None
        )
    return properties


@router.get("/api/properties/{property_id}")
async def property_detail(property_id: str) -> dict[str, Any]:
    rows = _load_properties()
    match = rows[rows["property_id"] == property_id]
    if match.empty:
        raise HTTPException(status_code=404, detail="Property not found")
    data = match.iloc[0].to_dict()
    return {k: (None if pd.isna(v) else v) for k, v in data.items()}


@router.get("/api/comparables/{property_id}")
async def comparables(property_id: str) -> list[dict[str, Any]]:
    rows = _load_properties()
    current = rows[rows["property_id"] == property_id]
    if current.empty:
        raise HTTPException(status_code=404, detail="Property not found")
    property_row = current.iloc[0]
    matches = rows[
        (rows["city"].astype(str).str.strip().str.casefold() == str(property_row["city"]).strip().casefold())
        & (rows["locality"].astype(str).str.strip().str.casefold() == str(property_row["locality"]).strip().casefold())
        & (rows["property_id"] != property_id)
    ]
    return matches.head(5).to_dict(orient="records")
