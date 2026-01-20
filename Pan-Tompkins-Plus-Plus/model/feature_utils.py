# -*- coding: utf-8 -*-
import numpy as np

NUM_COL = ["Age", "MaxHR", "Oldpeak"]


def fix_suspicious_numeric(X):
    if hasattr(X, "to_numpy"):
        X = X.to_numpy()
    X = X.astype(float, copy=True)
    oldpeak_idx = NUM_COL.index("Oldpeak")
    X[X[:, oldpeak_idx] < 0, oldpeak_idx] = np.nan
    return X
