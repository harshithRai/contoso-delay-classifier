from pathlib import Path
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ['carrier', 'distance_km', 'weight_kg', 'items', 'order_hour', 'is_sale_day', 'warehouse_backlog', 'weather_index']
def load_data(path):
    frame = pd.read_csv(path)
    if list(frame.columns) != FEATURES + ['delayed'] or len(frame) != 10000:
        raise ValueError('Expected the supplied 10,000-row CSV and exact training schema.')
    if frame.isna().any().any() or not set(frame.delayed.unique()) <= {0, 1}:
        raise ValueError('Missing values or invalid labels.')
    return frame

def split(frame):
    return train_test_split(frame, test_size=0.2, stratify=frame.delayed, random_state=42)

def evaluate(model, test):
    x, y = test[FEATURES], test.delayed
    prediction = model.predict(x)
    probabilities = model.predict_proba(x)[:, list(model.classes_).index(1)]
    return {
        'auc': float(roc_auc_score(y, probabilities)), 'accuracy': float(accuracy_score(y, prediction)),
        'precision': float(precision_score(y, prediction, pos_label=1, zero_division=0)),
        'recall': float(recall_score(y, prediction, pos_label=1, zero_division=0)),
        'f1': float(f1_score(y, prediction, pos_label=1, zero_division=0)),
        'confusionMatrix': confusion_matrix(y, prediction, labels=[0,1]).tolist()
    }

def save_json(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')
