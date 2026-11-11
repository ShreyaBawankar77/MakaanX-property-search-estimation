from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from backend.ml.explainability import explain_prediction
from backend.ml.house_price_model import get_model_performance, predict_price
from backend.schemas import PredictionRequest, PriceComparisonRequest, WhatIfRequest

router = APIRouter()


@router.post("/api/predict")
async def predict_property(payload: PredictionRequest) -> Dict[str, Any]:
    try:
        result = predict_price(payload.model_dump())
        if result.get('estimation_method') == 'random_forest_comparable_blend':
            explanation = {
                'top_factors': [],
                'summary': (
                    f"This estimate blends the Random Forest prediction with the median listed "
                    f"price per square foot from {result['comparable_count']} similar properties "
                    "in this locality, with the same bedroom count and home type, and within 15% "
                    "of the requested area."
                ),
            }
        else:
            explanation = explain_prediction(
                payload.model_dump(),
                {
                    'model_name': result.get(
                        'model_name',
                        'Local comparable listings with Random Forest regression fallback',
                    ),
                    'feature_importances': result.get('feature_importances', {}),
                },
                top_n=5,
            )
        fairness = (
            _fairness_status(payload.listing_price, result['predicted_price'])
            if payload.listing_price and payload.listing_price > 0
            else 'LISTING PRICE NOT PROVIDED'
        )
        result['fairness'] = fairness
        result['explanation'] = explanation
        result['note'] = 'This is an estimate and not a professional appraisal.'
        return result
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/api/predict/what-if")
async def predict_what_if(payload: WhatIfRequest) -> Dict[str, Any]:
    data = payload.model_dump()
    if data.get('target_area'):
        data['area_sqft'] = float(data['target_area'])
    if data.get('target_bhk'):
        data['bhk'] = int(data['target_bhk'])
    if data.get('target_resale') is not None:
        data['resale'] = int(data['target_resale'])
    if data.get('target_bathrooms'):
        data['bathrooms'] = int(data['target_bathrooms'])
    if data.get('target_property_age'):
        data['property_age'] = float(data['target_property_age'])
    if data.get('target_distance_to_metro'):
        data['distance_to_metro'] = float(data['target_distance_to_metro'])
    if data.get('target_furnishing'):
        data['furnishing'] = data['target_furnishing']
    if data.get('target_parking'):
        data['parking'] = int(data['target_parking'])
    result = predict_price(data)
    delta = result['predicted_price'] - (payload.listing_price or result['predicted_price'])
    result['price_change'] = round(delta, 2)
    result['scenario'] = 'What-if simulation applied.'
    return result


@router.get("/api/model/performance")
async def model_performance() -> Dict[str, Any]:
    return get_model_performance()


@router.post("/api/fairness")
async def fairness(payload: PriceComparisonRequest) -> Dict[str, Any]:
    diff = payload.listing_price - payload.predicted_price
    status = _fairness_status(payload.listing_price, payload.predicted_price)
    return {
        'listing_price': payload.listing_price,
        'predicted_price': payload.predicted_price,
        'price_difference': round(diff, 2),
        'fairness': status,
        'gauge': ['UNDERPRICED', 'FAIR', 'OVERPRICED'],
    }


def _fairness_status(listing_price: float, predicted_price: float) -> str:
    delta = abs(listing_price - predicted_price)
    ratio = delta / max(predicted_price, 1.0)
    if listing_price < predicted_price * 0.9:
        return 'UNDERPRICED'
    if listing_price > predicted_price * 1.1:
        return 'OVERPRICED'
    return 'FAIRLY PRICED'
