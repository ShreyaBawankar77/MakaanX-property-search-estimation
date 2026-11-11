from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from backend.database import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(String, unique=True, index=True, nullable=False)
    city = Column(String, nullable=False)
    locality = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    property_type = Column(String, nullable=False)
    bhk = Column(Integer, nullable=False)
    bathrooms = Column(Integer, nullable=False)
    area_sqft = Column(Float, nullable=False)
    carpet_area_sqft = Column(Float, nullable=False)
    floor = Column(Integer, nullable=False)
    total_floors = Column(Integer, nullable=False)
    property_age = Column(Float, nullable=False)
    furnishing = Column(String, nullable=False)
    parking = Column(Integer, nullable=False)
    balcony = Column(Integer, nullable=False)
    amenities = Column(String, default="")
    distance_to_metro = Column(Float, default=0.0)
    distance_to_school = Column(Float, default=0.0)
    distance_to_hospital = Column(Float, default=0.0)
    distance_to_mall = Column(Float, default=0.0)
    distance_to_railway = Column(Float, default=0.0)
    distance_to_airport = Column(Float, default=0.0)
    locality_price_per_sqft = Column(Float, default=0.0)
    locality_growth_rate = Column(Float, default=0.0)
    listing_price = Column(Float, default=0.0)
    actual_price = Column(Float, default=0.0)
    image_url = Column(String, default="")
    created_at = Column(DateTime, default=_utcnow)


class Amenity(Base):
    __tablename__ = "amenities"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=False)
    locality = Column(String, nullable=False)
    name = Column(String, nullable=False)
    amenity_type = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    distance_km = Column(Float, default=0.0)


class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(String, nullable=False)
    city = Column(String, nullable=False)
    locality = Column(String, nullable=False)
    predicted_price = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=False)
    upper_bound = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    fairness = Column(String, nullable=False)
    created_at = Column(DateTime, default=_utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow)


class UserCredential(Base):
    __tablename__ = "user_credentials"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    password_hash = Column(String, nullable=False)


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    request_data = Column(Text, nullable=False)
    result_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class SavedProperty(Base):
    __tablename__ = "saved_properties"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    property_id = Column(String, nullable=False)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=_utcnow)


class LocationRecord(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=False)
    locality = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accessibility_score = Column(Float, default=0.0)
    neighborhood_density = Column(Float, default=0.0)
    connectivity_score = Column(Float, default=0.0)
    amenity_count_1km = Column(Integer, default=0)
    amenity_count_3km = Column(Integer, default=0)
    updated_at = Column(DateTime, default=_utcnow)


class LocalityMetric(Base):
    __tablename__ = "locality_metrics"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=False)
    locality = Column(String, nullable=False)
    locality_dna = Column(Float, default=0.0)
    connectivity = Column(Float, default=0.0)
    education = Column(Float, default=0.0)
    healthcare = Column(Float, default=0.0)
    shopping = Column(Float, default=0.0)
    transport = Column(Float, default=0.0)
    employment = Column(Float, default=0.0)
    recreation = Column(Float, default=0.0)
    safety = Column(Float, default=0.0)
    development = Column(Float, default=0.0)
    price_stability = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=_utcnow)
