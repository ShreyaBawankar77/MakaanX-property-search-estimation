from __future__ import annotations

import os
from typing import Dict, Any

import pandas as pd

from backend.ml import house_price_model as uploaded_data_model

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'saved_models')
DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'properties.csv')


def _get_model_path() -> str:
    os.makedirs(MODEL_DIR, exist_ok=True)
    return os.path.join(MODEL_DIR, 'geoestate_model.joblib')


def generate_demo_dataset() -> pd.DataFrame:
    if os.path.exists(DATASET_PATH):
        df = pd.read_csv(DATASET_PATH)
        if not df.empty:
            return df
    return uploaded_data_model._load_training_data()


def train_and_save_model() -> Dict[str, Any]:
    return uploaded_data_model.train_and_save_model()


def load_model_bundle() -> Dict[str, Any]:
    return uploaded_data_model.load_model_bundle()


def predict_price(payload: Dict[str, Any]) -> Dict[str, Any]:
    return uploaded_data_model.predict_price(payload)


def get_model_performance() -> Dict[str, Any]:
    return uploaded_data_model.get_model_performance()
