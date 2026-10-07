"""
convert_model_to_native.py
Converts the pickled XGBoost model to XGBoost's own JSON format.

Why: a pickle only loads reliably on the same xgboost/scikit-learn/Python versions that wrote it
(that is what caused "XGBoostError: input stream corrupted" on another machine). XGBoost's native
JSON file is version-tolerant, human-readable, and is the format XGBoost itself recommends for saving.

Run from the repo root:   python src/convert_model_to_native.py
Reads  models/xgboost_model_v2.pkl   (only works on a machine where that pickle still loads)
Writes models/xgboost_model_v2.json  and checks both give identical predictions.
If the pickle will not load on your machine, simply retrain: python src/train_final_model.py
"""
import pickle
import sys
from pathlib import Path

import numpy as np
from xgboost import XGBClassifier

SRC = Path("models/xgboost_model_v2.pkl")
DST = Path("models/xgboost_model_v2.json")

if not SRC.exists():
    sys.exit(f"{SRC} not found - run this from the repo root, or retrain with src/train_final_model.py")

with open(SRC, "rb") as f:
    old = pickle.load(f)
old.save_model(DST)

new = XGBClassifier()
new.load_model(DST)

# Compare predictions on random inputs drawn from each feature's observed range (1000 rows)
rng = np.random.default_rng(0)
cols = list(old.feature_names_in_)
X = rng.integers(0, 6, size=(1000, len(cols))).astype(float)
import pandas as pd
X = pd.DataFrame(X, columns=cols)
diff = np.abs(old.predict_proba(X) - new.predict_proba(X)).max()
same_cols = list(new.feature_names_in_) == cols
print(f"Saved {DST} ({DST.stat().st_size / 1024:.0f} KB)")
print(f"Feature names preserved: {same_cols}   max probability difference vs pickle: {diff:.2e}")
sys.exit(0 if (same_cols and diff < 1e-6) else "MISMATCH - do not use the JSON file")
