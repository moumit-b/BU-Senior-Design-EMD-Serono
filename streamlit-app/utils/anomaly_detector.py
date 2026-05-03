"""
Hallucination Rate Anomaly Detector

Uses Isolation Forest to flag reports whose hallucination rate is a
statistical outlier compared to historical reports. Requires at least
5 prior reports to produce a meaningful signal; returns None otherwise.
"""

import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

_MIN_SAMPLES = 5  # minimum historical records needed to fit the model


def _fetch_historical_rates(db_manager) -> list:
    """Return all hallucination rates from report_verifications."""
    try:
        from context.db_models import ReportVerificationRecord
        with db_manager.get_session() as session:
            rows = session.query(ReportVerificationRecord.hallucination_rate).all()
            return [r.hallucination_rate for r in rows]
    except Exception as e:
        logger.warning(f"anomaly_detector: could not fetch historical rates: {e}")
        return []


def score_report(db_manager, current_rate: float) -> Optional[bool]:
    """
    Determine whether current_rate is anomalous vs. historical reports.

    Returns:
        True  — anomaly detected, scientist review recommended
        False — rate is within normal range
        None  — not enough historical data to make a determination
    """
    rates = _fetch_historical_rates(db_manager)

    # Exclude the report we just saved so we compare against prior history
    # (the current report is already in the DB at this point)
    rates = rates[:-1] if rates else []

    if len(rates) < _MIN_SAMPLES:
        return None

    try:
        from sklearn.ensemble import IsolationForest

        X = np.array(rates).reshape(-1, 1)
        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(X)

        prediction = model.predict([[current_rate]])[0]
        return prediction == -1  # -1 = anomaly
    except Exception as e:
        logger.warning(f"anomaly_detector: model failed: {e}")
        return None
