from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class PredictionRequest(BaseModel):
    city: str = "Mumbai"
    locality: str = ""
    property_id: Optional[str] = None
    bhk: int = 2
    area_sqft: float = 1100.0
    resale: int = 0
    listing_price: Optional[float] = None
    amenities: str = ""

    @field_validator("bhk", mode="before")
    @classmethod
    def parse_bhk(cls, v: Any) -> int:
        if v in ("", None):
            return 2
        try:
            return max(1, int(v))
        except (ValueError, TypeError):
            return 2

    @field_validator("area_sqft", mode="before")
    @classmethod
    def parse_area(cls, v: Any) -> float:
        if v in ("", None):
            return 1100.0
        try:
            val = float(v)
            return val if val > 0 else 1100.0
        except (ValueError, TypeError):
            return 1100.0

    @field_validator("resale", mode="before")
    @classmethod
    def parse_resale(cls, v: Any) -> int:
        if v in ("", None):
            return 0
        try:
            return 1 if int(v) else 0
        except (ValueError, TypeError):
            return 0

    @field_validator("listing_price", mode="before")
    @classmethod
    def parse_listing_price(cls, v: Any) -> Optional[float]:
        if v in ("", None):
            return None
        try:
            val = float(v)
            return val if val > 0 else None
        except (ValueError, TypeError):
            return None


class WhatIfRequest(PredictionRequest):
    target_area: Optional[float] = None
    target_bhk: Optional[int] = None
    target_resale: Optional[int] = None


class ImageAnalysisRequest(BaseModel):
    image_name: str = "demo_property.jpg"
    quality_hint: float = 0.75


class SearchLocationRequest(BaseModel):
    city: str = "Nagpur"
    locality: str = "Dharampeth"


class PriceComparisonRequest(BaseModel):
    listing_price: float = 8900000
    predicted_price: float = 8500000


class ModelPerformanceResponse(BaseModel):
    dataset_size: int
    feature_count: int
    training_samples: int
    testing_samples: int
    metrics: dict
    ablation: Optional[list] = None
