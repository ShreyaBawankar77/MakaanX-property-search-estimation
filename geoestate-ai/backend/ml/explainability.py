from __future__ import annotations

from typing import Dict, List, Any


def compute_feature_importance(model_meta: Dict[str, Any]) -> Dict[str, float]:
    model_name = str(model_meta.get('model_name', ''))
    if (
        'forest' in model_name.lower()
        or 'gradient' in model_name.lower()
        or 'ensemble' in model_name.lower()
        or 'regressor' in model_name.lower()
        or model_meta.get('feature_importances')
    ):
        importances = model_meta.get('feature_importances', {})
        if importances:
            return dict(importances)

    coefficients = model_meta.get('coefficients', {})
    if coefficients:
        return {k: abs(v) for k, v in coefficients.items()}
    return {}


def explain_prediction(features: Dict[str, Any], model_meta: Dict[str, Any], top_n: int = 5) -> Dict[str, Any]:
    importances = compute_feature_importance(model_meta)
    ranked = sorted(importances.items(), key=lambda item: abs(item[1]), reverse=True)[:top_n]
    positive = []
    negative = []
    amenities_text = str(features.get("amenities", "")).lower()
    for key, weight in ranked:
        if key in {"Gymnasium", "SwimmingPool", "CarParking", "24X7Security", "LiftAvailable", "ClubHouse"}:
            value = 1 if key.lower() in amenities_text else 0
        else:
            value = features.get(key, 0.0)
        if isinstance(value, (int, float)) and value > 0:
            positive.append({"feature": key, "impact": round(float(weight) * 100, 2), "value": value})
        elif isinstance(value, (int, float)):
            negative.append({"feature": key, "impact": round(float(weight) * 100, 2), "value": value})
        elif value:
            positive.append({"feature": key, "impact": round(float(weight) * 100, 2), "value": str(value)})

    return {
        "top_factors": [{"feature": k, "weight": round(float(v), 4)} for k, v in ranked],
        "positive": positive,
        "negative": negative,
    }
