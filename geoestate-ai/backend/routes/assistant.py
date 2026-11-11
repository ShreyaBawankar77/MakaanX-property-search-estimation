from __future__ import annotations

import re
import pandas as pd
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.routes.properties import _filter_properties, _load_properties

router = APIRouter()

CITY_ALIASES = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "chennai": "Chennai",
    "delhi": "Delhi",
    "hyderabad": "Hyderabad",
    "kolkata": "Kolkata",
    "mumbai": "Mumbai",
}
AMENITY_ALIASES = {
    "gym": "Gymnasium",
    "gymnasium": "Gymnasium",
    "pool": "SwimmingPool",
    "swimming pool": "SwimmingPool",
    "parking": "CarParking",
    "car parking": "CarParking",
    "security": "24X7Security",
    "24x7 security": "24X7Security",
    "lift": "LiftAvailable",
    "elevator": "LiftAvailable",
    "clubhouse": "ClubHouse",
    "club house": "ClubHouse",
}


class AssistantRequest(BaseModel):
    message: str
    city: str | None = None
    locality: str | None = None
    max_price: float | None = None
    min_price: float | None = None
    bhk: int | None = None
    resale: int | None = None
    area_sqft: float | None = None
    area_tolerance: float = 0.2
    amenities: str = ""


def _budget_from_message(message: str) -> float | None:
    amount_pattern = r"([\d,]+(?:\.\d+)?)\s*(crores?|cr|lakhs?|lacs?|lac|l)?"
    prefixed = re.search(
        rf"(?:under|below|within|up\s*to|upto|less\s+than|budget(?:\s+of)?|max(?:imum)?)\s*(?:₹|rs\.?|inr)?\s*{amount_pattern}",
        message,
        re.IGNORECASE,
    )
    currency = re.search(rf"(?:₹|rs\.?|inr)\s*{amount_pattern}", message, re.IGNORECASE)
    match = prefixed or currency
    if not match:
        return None

    amount = float(match.group(1).replace(",", ""))
    unit = (match.group(2) or "").lower()
    if unit in {"crore", "crores", "cr"}:
        return amount * 10_000_000
    if unit in {"lakh", "lakhs", "lac", "lacs", "l"}:
        return amount * 100_000
    return amount


def _parsed_filters(request: AssistantRequest) -> dict[str, Any]:
    message = request.message.lower()
    city = request.city
    for alias, canonical in CITY_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", message):
            city = canonical
            break

    locality = request.locality
    city_rows = _load_properties()
    if city:
        city_rows = city_rows[city_rows["city"] == city]
    locality_series = pd.Series(city_rows["locality"])
    for candidate in sorted(locality_series.dropna().unique(), key=len, reverse=True):
        candidate_clean = candidate.strip().lower()
        # Avoid treating the city name itself as a locality (e.g. 'mumbai' in Mumbai)
        if city and candidate_clean == city.strip().lower():
            continue
        # Use word boundary search so short locality words don't match substrings
        if re.search(rf"\b{re.escape(candidate_clean)}\b", message):
            locality = candidate
            break
    if city and locality and not (city_rows["locality"] == locality).any():
        locality = None

    bhk = request.bhk
    bhk_match = re.search(r"\b([1-9])\s*(?:bhk|bed(?:room)?s?)\b", message)
    if bhk_match:
        bhk = int(bhk_match.group(1))

    area_sqft = request.area_sqft
    area_match = re.search(r"\b(\d{3,5})\s*(?:sq\.?\s*ft|sqft|square\s+feet)\b", message)
    if area_match:
        area_sqft = float(area_match.group(1))

    resale = request.resale
    if re.search(r"\b(resale|resale home|second.hand)\b", message):
        resale = 1
    elif re.search(r"\b(primary sale|new project|new property)\b", message):
        resale = 0

    amenities = {value.strip() for value in request.amenities.split(",") if value.strip()}
    for phrase, amenity in AMENITY_ALIASES.items():
        if re.search(rf"\b{re.escape(phrase)}\b", message):
            amenities.add(amenity)

    return {
        "city": city,
        "locality": locality,
        "max_price": (
            None
            if re.search(r"\b(no\s+budget|any\s+budget|any\s+price|no\s+limit|clear\s+budget)\b", message)
            else (_budget_from_message(request.message) or request.max_price)
        ),
        "min_price": (
            None
            if re.search(r"\b(no\s+budget|any\s+budget|any\s+price|no\s+limit|clear\s+budget)\b", message)
            else request.min_price
        ),
        "bhk": bhk,
        "resale": resale,
        "area_sqft": area_sqft,
        "area_tolerance": request.area_tolerance,
        "amenities": ",".join(sorted(amenities)),
    }


@router.post("/api/assistant/chat")
async def chat_with_property_assistant(request: AssistantRequest) -> dict[str, Any]:
    filters = _parsed_filters(request)
    rows = _filter_properties(
        city=filters["city"],
        locality=filters["locality"],
        min_price=filters["min_price"],
        max_price=filters["max_price"],
        bhk=filters["bhk"],
        resale=filters["resale"],
        area_sqft=filters["area_sqft"],
        area_tolerance=filters["area_tolerance"],
        amenities=filters["amenities"],
    )
    count = len(rows)
    properties = rows.sort_values("listing_price", ascending=True).head(3).to_dict(orient="records")

    criteria = []
    if filters["city"]:
        criteria.append(filters["city"])
    if filters["locality"] and (not filters["city"] or filters["locality"].strip().lower() != filters["city"].strip().lower()):
        criteria.append(filters["locality"])
    if filters["bhk"]:
        criteria.append(f"{filters['bhk']} bedrooms")
    if filters["max_price"]:
        criteria.append(f"up to ₹{filters['max_price']:,.0f}")
    if filters["min_price"]:
        criteria.append(f"from ₹{filters['min_price']:,.0f}")
    if filters["area_sqft"]:
        criteria.append(f"around {filters['area_sqft']:,.0f} square feet")
    if filters["resale"] is not None:
        criteria.append("pre-owned home" if filters["resale"] else "new home")
    if filters["amenities"]:
        feature_names = {
            "Gymnasium": "gym",
            "SwimmingPool": "swimming pool",
            "CarParking": "parking",
            "24X7Security": "24/7 security",
            "LiftAvailable": "lift",
            "ClubHouse": "clubhouse",
        }
        features: list[str] = [str(feature_names.get(name, name)) for name in filters["amenities"].split(",") if name]
        criteria.append("home features: " + ", ".join(features))

    if count:
        answer = f"I found {count:,} homes for {' · '.join(criteria) or 'your current search'}. Your results are updated; choose a home to see its estimated price."
    else:
        answer = f"I couldn't find a home for {' · '.join(criteria) or 'those choices'}. Try a higher budget or a larger home-size range."

    return {"answer": answer, "filters": filters, "match_count": count, "properties": properties}