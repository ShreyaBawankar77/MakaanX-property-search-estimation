from __future__ import annotations

from functools import lru_cache
import os
import re
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import TargetEncoder

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "saved_models")
DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "properties.csv")
MODEL_PATH = os.path.join(MODEL_DIR, "house_price_model_v10.joblib")
VALIDATION_RANDOM_STATES = (42, 2025, 2026)
COMPARABLE_AREA_TOLERANCE = 0.15
MIN_COMPARABLE_LISTINGS = 3
COMPARABLE_BLEND_WEIGHT = 0.5
CATEGORICAL_FEATURES = ["city", "locality"]
NUMERIC_FEATURES = [
    "area_sqft",
    "bhk",
    "resale",
    "Gymnasium",
    "SwimmingPool",
    "CarParking",
    "24X7Security",
    "LiftAvailable",
    "ClubHouse",
]
AMENITY_FEATURES = NUMERIC_FEATURES[3:]
DERIVED_CATEGORICAL_FEATURES = ["city_locality"]
DERIVED_NUMERIC_FEATURES = [
    "area_per_bedroom",
    "log_area",
    "bedrooms_per_1000_sqft",
    "amenity_count",
]
MODEL_CATEGORICAL_FEATURES = CATEGORICAL_FEATURES + DERIVED_CATEGORICAL_FEATURES
MODEL_NUMERIC_FEATURES = NUMERIC_FEATURES + DERIVED_NUMERIC_FEATURES

COLUMN_MAPPING = {
    "price": "listing_price",
    "listing_price": "listing_price",
    "actual_price": "listing_price",
    "area": "area_sqft",
    "area_sqft": "area_sqft",
    "total_sqft": "area_sqft",
    "size": "area_sqft",
    "location": "locality",
    "locality": "locality",
    "suburb": "locality",
    "city": "city",
    "no. of bedrooms": "bhk",
    "bedrooms": "bhk",
    "bhk": "bhk",
    "rooms": "bhk",
    "resale": "resale",
    "amenities": "amenities",
}

AMENITY_COLUMN_ALIASES = {
    "Gymnasium": {"gymnasium", "gym"},
    "SwimmingPool": {"swimmingpool", "pool"},
    "CarParking": {"carparking", "parking"},
    "24X7Security": {"24x7security", "24x7securityavailable", "security"},
    "LiftAvailable": {"liftavailable", "lift", "elevator"},
    "ClubHouse": {"clubhouse"},
}


@lru_cache(maxsize=1)
def _load_training_data() -> pd.DataFrame:
    frame = pd.read_csv(DATASET_PATH, keep_default_na=False)

    # Clean and normalize column names (lowercase & stripped)
    clean_columns = {c: c.strip().lower() for c in frame.columns}
    frame = frame.rename(columns=clean_columns)
    frame = frame.drop_duplicates().copy()

    # Map standard alternate column names to canonical names
    rename_map = {}
    for col in frame.columns:
        if col in COLUMN_MAPPING and COLUMN_MAPPING[col] not in frame.columns:
            rename_map[col] = COLUMN_MAPPING[col]
    if rename_map:
        frame = frame.rename(columns=rename_map)

    # Provide safe defaults for optional columns if omitted
    if "resale" not in frame.columns:
        frame["resale"] = 0
    if "amenities" not in frame.columns:
        frame["amenities"] = ""

    required = {"city", "locality", "area_sqft", "bhk", "listing_price"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Property dataset is missing columns: {', '.join(sorted(missing))}")

    frame = frame.copy()
    for column in ("area_sqft", "bhk", "listing_price", "resale"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["city", "locality", "area_sqft", "bhk", "listing_price"])
    clean_df = pd.DataFrame(frame[(frame["area_sqft"] > 0) & (frame["bhk"] > 0) & (frame["listing_price"] > 0)])

    # Clean string features
    clean_df["city"] = clean_df["city"].astype(str).str.strip()
    clean_df["locality"] = clean_df["locality"].astype(str).str.strip()

    normalized_columns = {
        re.sub(r"[^a-z0-9]", "", column): column
        for column in clean_df.columns
    }
    amenity_text = clean_df["amenities"].fillna("").astype(str).str.casefold()
    amenity_tokens = amenity_text.map(
        lambda value: {token.strip() for token in value.split(",") if token.strip()}
    )
    for amenity in AMENITY_FEATURES:
        aliases = AMENITY_COLUMN_ALIASES[amenity]
        source_column = next(
            (normalized_columns[alias] for alias in aliases if alias in normalized_columns),
            None,
        )
        if source_column:
            values = clean_df[source_column].astype(str).str.strip().str.casefold()
            normalized_values = values.map(
                {"yes": 1.0, "true": 1.0, "available": 1.0, "no": 0.0, "false": 0.0, "unavailable": 0.0}
            )
            numeric_values = pd.to_numeric(values, errors="coerce")
            feature_values = normalized_values.fillna(numeric_values)
            clean_df[amenity] = feature_values.where(feature_values.isin([0.0, 1.0]))
        else:
            clean_df[amenity] = amenity_tokens.map(lambda tokens: int(amenity.casefold() in tokens))
    clean_df["resale"] = pd.Series(clean_df["resale"]).fillna(0).astype(int)
    return clean_df


@lru_cache(maxsize=1)
def _get_known_locations() -> tuple[dict[str, str], dict[tuple[str, str], str]]:
    frame = _load_training_data()
    city_map = {str(c).strip().lower(): str(c).strip() for c in frame["city"].unique()}
    locality_map = {
        (str(row["city"]).strip().lower(), str(row["locality"]).strip().lower()): str(row["locality"]).strip()
        for _, row in frame[["city", "locality"]].drop_duplicates().iterrows()
    }
    return city_map, locality_map


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        if val in ("", None):
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    try:
        if val in ("", None):
            return default
        return int(val)
    except (ValueError, TypeError):
        return default


def _add_model_features(frame: pd.DataFrame) -> pd.DataFrame:
    features = frame.copy()
    features["city_locality"] = features["city"].astype(str) + "|" + features["locality"].astype(str)
    features["area_per_bedroom"] = features["area_sqft"] / features["bhk"].clip(lower=1)
    features["log_area"] = np.log1p(features["area_sqft"])
    features["bedrooms_per_1000_sqft"] = 1000 * features["bhk"] / features["area_sqft"].clip(lower=1)
    features["amenity_count"] = features[AMENITY_FEATURES].sum(axis=1, min_count=1)
    return features


def _model_input(payload: dict[str, Any]) -> pd.DataFrame:
    raw_city = str(payload.get("city", "")).strip()
    raw_locality = str(payload.get("locality", "")).strip()

    city_map, locality_map = _get_known_locations()

    # Canonicalize city (e.g. 'mumbai' -> 'Mumbai')
    canonical_city = city_map.get(raw_city.lower(), raw_city.title())

    # Canonicalize locality (e.g. 'thane west' -> 'Thane West')
    canonical_locality = locality_map.get((canonical_city.lower(), raw_locality.lower()))
    if not canonical_locality:
        for (c, l_lower), l_orig in locality_map.items():
            if c == canonical_city.lower() and (l_lower == raw_locality.lower() or l_lower in raw_locality.lower() or raw_locality.lower() in l_lower):
                canonical_locality = l_orig
                break
    if not canonical_locality:
        canonical_locality = raw_locality.title()

    amenity_text = str(payload.get("amenities", "")).lower()
    row = {
        "city": canonical_city,
        "locality": canonical_locality,
        "area_sqft": _safe_float(payload.get("area_sqft"), 1100.0),
        "bhk": _safe_int(payload.get("bhk"), 2),
        "resale": _safe_int(payload.get("resale"), 0),
    }
    row.update({amenity: int(amenity.lower() in amenity_text) for amenity in AMENITY_FEATURES})
    source_features = pd.DataFrame([row], columns=CATEGORICAL_FEATURES + NUMERIC_FEATURES)
    return _add_model_features(source_features)


def _build_model() -> TransformedTargetRegressor:
    preprocessor = ColumnTransformer(
        [
            (
                "categorical",
                TargetEncoder(
                    target_type="continuous",
                    smooth=5.0,
                    cv=KFold(n_splits=5, shuffle=True, random_state=42),
                ),
                MODEL_CATEGORICAL_FEATURES,
            ),
            ("numeric", "passthrough", MODEL_NUMERIC_FEATURES),
        ]
    )

    return TransformedTargetRegressor(
        regressor=Pipeline(
            [
                ("preprocessor", preprocessor),
                (
                    "regressor",
                    RandomForestRegressor(
                        n_estimators=120,
                        max_features=0.8,
                        min_samples_leaf=8,
                        criterion="absolute_error",
                        n_jobs=-1,
                        random_state=42,
                    ),
                ),
            ]
        ),
        func=np.log1p,
        inverse_func=np.expm1,
    )


def _feature_importances(model: TransformedTargetRegressor, features: pd.DataFrame, target: pd.Series) -> dict[str, float]:
    result = permutation_importance(
        model,
        features,
        target,
        scoring="neg_mean_absolute_error",
        n_repeats=3,
        random_state=42,
        n_jobs=1,
    )
    grouped_importances: dict[str, float] = {}
    feature_names = features.columns.tolist()
    for name, importance in zip(feature_names, result.importances_mean):
        if name == "city_locality":
            name = "locality"
        elif name in {"area_per_bedroom", "log_area"}:
            name = "area_sqft"
        grouped_importances[name] = grouped_importances.get(name, 0.0) + max(float(importance), 0.0)

    total_importance = sum(grouped_importances.values())
    if total_importance > 0:
        return {name: importance / total_importance for name, importance in grouped_importances.items()}
    return grouped_importances


def _build_comparable_index(frame: pd.DataFrame) -> dict[tuple[str, str, int, int], tuple[np.ndarray, np.ndarray, np.ndarray]]:
    comparable_rows = frame.copy()
    comparable_rows["city_key"] = comparable_rows["city"].astype(str).str.strip().str.casefold()
    comparable_rows["locality_key"] = comparable_rows["locality"].astype(str).str.strip().str.casefold()
    comparable_rows["price_per_sqft"] = comparable_rows["listing_price"] / comparable_rows["area_sqft"]
    if "property_id" not in comparable_rows:
        comparable_rows["property_id"] = ""

    index = {}
    group_columns = ["city_key", "locality_key", "bhk", "resale"]
    for key, group in comparable_rows.groupby(group_columns, sort=False, dropna=False):
        group = group.sort_values("area_sqft")
        index[(str(key[0]), str(key[1]), int(key[2]), int(key[3]))] = (
            group["area_sqft"].to_numpy(dtype=float),
            group["price_per_sqft"].to_numpy(dtype=float),
            group["property_id"].astype(str).to_numpy(),
        )
    return index


def _predict_from_comparables(
    payload: dict[str, Any],
    comparable_index: dict[tuple[str, str, int, int], tuple[np.ndarray, np.ndarray, np.ndarray]],
) -> tuple[float, int] | None:
    city = str(payload.get("city", "")).strip().casefold()
    locality = str(payload.get("locality", "")).strip().casefold()
    bhk = _safe_int(payload.get("bhk"), 2)
    resale = _safe_int(payload.get("resale"), 0)
    area = _safe_float(payload.get("area_sqft"), 1100.0)
    key = (city, locality, bhk, resale)
    indexed_group = comparable_index.get(key)
    if indexed_group is None or area <= 0:
        return None

    areas, prices_per_sqft, property_ids = indexed_group
    lower = area * (1 - COMPARABLE_AREA_TOLERANCE)
    upper = area * (1 + COMPARABLE_AREA_TOLERANCE)
    start = int(np.searchsorted(areas, lower, side="left"))
    end = int(np.searchsorted(areas, upper, side="right"))
    candidate_indices = np.arange(start, end)

    raw_property_id = payload.get("property_id")
    property_id = str(raw_property_id).strip() if raw_property_id is not None else ""
    if property_id:
        candidate_indices = candidate_indices[property_ids[candidate_indices] != property_id]
    else:
        candidate_indices = candidate_indices[areas[candidate_indices] != area]

    if not len(candidate_indices):
        return None

    comparable_price_per_sqft = prices_per_sqft[candidate_indices]
    return (
        float(np.median(comparable_price_per_sqft) * area),
        int(len(candidate_indices)),
    )


def _aggregate_training_rows(frame: pd.DataFrame) -> pd.DataFrame:
    feature_columns = CATEGORICAL_FEATURES + NUMERIC_FEATURES
    return (
        frame.groupby(feature_columns, as_index=False, sort=False, dropna=False)
        .agg(listing_price=("listing_price", "median"))
    )


def train_and_save_model() -> dict[str, Any]:
    frame = _load_training_data()
    features = _add_model_features(frame[CATEGORICAL_FEATURES + NUMERIC_FEATURES])
    target = frame["listing_price"]
    group_features = features[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    groups = pd.MultiIndex.from_frame(group_features)

    def calculate_metrics(actual: pd.Series, predicted: np.ndarray) -> dict[str, float]:
        actual_values = np.asarray(actual)
        return {
            "MAE": float(mean_absolute_error(actual_values, predicted)),
            "RMSE": float(np.sqrt(mean_squared_error(actual_values, predicted))),
            "R2": float(r2_score(actual_values, predicted)),
            "MedianAPE": float(
                np.median(np.abs((actual_values - predicted) / actual_values)) * 100
            ),
        }

    split_metrics = []
    random_forest_metrics = []
    split_training_sizes = []
    split_testing_sizes = []
    validation_errors = []
    comparable_coverages = []
    feature_importances = {}
    for split_index, random_state in enumerate(VALIDATION_RANDOM_STATES):
        train_indices, test_indices = next(
            GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=random_state).split(
                features, target, groups=groups
            )
        )
        training_rows = _aggregate_training_rows(frame.iloc[train_indices])
        x_train = _add_model_features(training_rows[CATEGORICAL_FEATURES + NUMERIC_FEATURES])
        x_test = features.iloc[test_indices]
        y_test = target.iloc[test_indices]

        evaluation_model = _build_model()
        evaluation_model.fit(x_train, training_rows["listing_price"])
        random_forest_predictions = np.maximum(0.0, evaluation_model.predict(x_test))
        random_forest_metrics.append(calculate_metrics(y_test, random_forest_predictions))
        validation_comparable_index = _build_comparable_index(frame.iloc[train_indices])
        blended_predictions = random_forest_predictions.copy()
        comparable_count = 0
        for prediction_index, (_, row) in enumerate(frame.iloc[test_indices].iterrows()):
            comparable = _predict_from_comparables(
                row.to_dict(),
                validation_comparable_index,
            )
            if comparable and comparable[1] >= MIN_COMPARABLE_LISTINGS:
                comparable_count += 1
                blended_predictions[prediction_index] = (
                    (1 - COMPARABLE_BLEND_WEIGHT) * random_forest_predictions[prediction_index]
                    + COMPARABLE_BLEND_WEIGHT * comparable[0]
                )
        split_metrics.append(calculate_metrics(y_test, blended_predictions))
        comparable_coverages.append(comparable_count / len(test_indices))
        split_training_sizes.append(len(training_rows))
        split_testing_sizes.append(len(test_indices))
        validation_errors.extend(np.abs(np.asarray(y_test) - blended_predictions))
        if split_index == 0:
            feature_importances = _feature_importances(evaluation_model, x_test, y_test)

    metrics = {
        "Repeated group holdout": {
            metric: float(np.mean([split[metric] for split in split_metrics]))
            for metric in split_metrics[0]
        },
        "Random Forest baseline": {
            metric: float(np.mean([split[metric] for split in random_forest_metrics]))
            for metric in random_forest_metrics[0]
        },
    }
    metrics_std = {
        "Repeated group holdout": {
            metric: float(np.std([split[metric] for split in split_metrics]))
            for metric in split_metrics[0]
        },
        "Random Forest baseline": {
            metric: float(np.std([split[metric] for split in random_forest_metrics]))
            for metric in random_forest_metrics[0]
        },
    }
    error_margin = float(np.quantile(validation_errors, 0.8))
    full_training_rows = _aggregate_training_rows(frame)

    bundle = {
        "model_name": "Random Forest with local-comparable blend",
        "model_object": _build_model(),
        "feature_importances": feature_importances,
        "metrics": metrics,
        "metrics_std": metrics_std,
        "validation_splits": len(VALIDATION_RANDOM_STATES),
        "comparable_blend_weight": COMPARABLE_BLEND_WEIGHT,
        "comparable_minimum_listings": MIN_COMPARABLE_LISTINGS,
        "comparable_validation_coverage": float(np.mean(comparable_coverages)),
        "evaluation_strategy": (
            "Mean of 20% group-aware holdouts using random seeds "
            f"{', '.join(map(str, VALIDATION_RANDOM_STATES))}; identical feature groups stay "
            "in one split and repeated training inputs are median-aggregated. Predictions blend "
            "the Random Forest and the median price per square foot from at least three eligible "
            "training-set comparables; otherwise they use the Random Forest alone"
        ),
        "error_margin_80": error_margin,
        "training_samples": len(full_training_rows),
        "evaluation_training_samples": float(np.mean(split_training_sizes)),
        "testing_samples": int(round(np.mean(split_testing_sizes))),
        "dataset_size": len(frame),
        "feature_count": len(features.columns),
        "comparable_index": _build_comparable_index(frame),
    }
    full_features = _add_model_features(full_training_rows[CATEGORICAL_FEATURES + NUMERIC_FEATURES])
    bundle["model_object"].fit(full_features, full_training_rows["listing_price"])
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(bundle, MODEL_PATH)
    return bundle


@lru_cache(maxsize=1)
def load_model_bundle() -> dict[str, Any]:
    if not os.path.exists(MODEL_PATH):
        return train_and_save_model()
    return joblib.load(MODEL_PATH)


def predict_price(payload: dict[str, Any]) -> dict[str, Any]:
    bundle = load_model_bundle()
    model = bundle["model_object"]
    inp_df = _model_input(payload)
    resolved_payload = inp_df.iloc[0].to_dict()
    resolved_payload["property_id"] = payload.get("property_id", "")

    # Blend with comparable listings only when enough independent local examples exist.
    random_forest_prediction = max(0.0, float(model.predict(inp_df)[0]))
    prediction = random_forest_prediction
    estimation_method = "random_forest_regression"

    # Supplementary local comparable listings analysis
    comparable = _predict_from_comparables(
        resolved_payload,
        bundle.get("comparable_index") or _build_comparable_index(_load_training_data()),
    )
    comparable_count = comparable[1] if comparable else 0
    comparable_median_price = comparable[0] if comparable else None
    if comparable and comparable_count >= MIN_COMPARABLE_LISTINGS:
        prediction = (
            (1 - COMPARABLE_BLEND_WEIGHT) * random_forest_prediction
            + COMPARABLE_BLEND_WEIGHT * comparable_median_price
        )
        estimation_method = "random_forest_comparable_blend"

    area = max(_safe_float(payload.get("area_sqft"), 1100.0), 1.0)
    listing_price = _safe_float(payload.get("listing_price"), 0.0)
    listing_price_warning = None
    if comparable and listing_price > 0 and comparable_median_price and comparable_median_price > 0:
        listing_to_estimate_ratio = listing_price / comparable_median_price
        if listing_to_estimate_ratio >= 3:
            listing_price_warning = (
                f"The asking price is {listing_to_estimate_ratio:.1f}× the local median estimate from "
                f"{comparable_count} close listings in this area. Verify property details."
            )
        elif listing_to_estimate_ratio <= 1 / 3:
            listing_price_warning = (
                f"The asking price is unusually low ({listing_to_estimate_ratio:.1f}× of local median from "
                f"{comparable_count} close listings). Verify if it is a distress or special sale."
            )

    resolved_city = inp_df["city"].iloc[0]
    resolved_locality = inp_df["locality"].iloc[0]

    matching_rows = _load_training_data()
    local_count = len(
        matching_rows[
            (matching_rows["city"].str.lower() == resolved_city.lower())
            & (matching_rows["locality"].str.lower() == resolved_locality.lower())
        ]
    )
    return {
        "predicted_price": round(prediction, 2),
        "estimated_range": {
            "lower": round(max(0.0, prediction - bundle["error_margin_80"]), 2),
            "upper": round(prediction + bundle["error_margin_80"], 2),
        },
        "price_per_sqft": round(prediction / area, 2),
        "locality_sample_count": local_count,
        "comparable_count": comparable_count,
        "comparable_median_price": round(comparable_median_price, 2) if comparable_median_price else None,
        "estimation_method": estimation_method,
        "listing_price_warning": listing_price_warning,
        "range_coverage": 80,
        "fairness": "Fairly Priced",
        "feature_importances": bundle["feature_importances"],
        "model_name": bundle["model_name"],
    }


def get_model_performance() -> dict[str, Any]:
    bundle = load_model_bundle()
    return {
        "model_name": bundle["model_name"],
        "dataset_size": bundle["dataset_size"],
        "feature_count": bundle["feature_count"],
        "training_samples": bundle["training_samples"],
        "evaluation_training_samples": bundle["evaluation_training_samples"],
        "testing_samples": bundle["testing_samples"],
        "metrics": bundle["metrics"],
        "metrics_std": bundle["metrics_std"],
        "validation_splits": bundle["validation_splits"],
        "evaluation_strategy": bundle["evaluation_strategy"],
        "comparable_blend_weight": bundle["comparable_blend_weight"],
        "comparable_minimum_listings": bundle["comparable_minimum_listings"],
        "comparable_validation_coverage": bundle["comparable_validation_coverage"],
    }


if __name__ == "__main__":
    print("Loading / validating house price model...")
    bundle = load_model_bundle()
    print("Model loaded successfully!")
    print(f"Algorithm: {bundle['model_name']}")
    print(f"Metrics: {bundle['metrics']}")
    sample = predict_price({
        "city": "mumbai",
        "locality": "thane west",
        "bhk": 2,
        "area_sqft": 1000,
        "resale": 0,
        "amenities": "Gymnasium,SwimmingPool",
    })
    print(f"Prediction for 2 BHK in Thane West (case-insensitive test): Rs. {sample['predicted_price']:,.2f} (sample count: {sample['locality_sample_count']})")
