
from typing import Dict, Any
import base64
from io import BytesIO
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .db import DailyPrice, get_session

def load_series(origin: str, destination: str, depart_date: str, db_url: str = None) -> pd.DataFrame:
    sess = get_session(db_url)
    try:
        d = datetime.strptime(depart_date, "%Y-%m-%d").date()
        q = (sess.query(DailyPrice)
             .filter(DailyPrice.origin==origin.upper(),
                     DailyPrice.destination==destination.upper(),
                     DailyPrice.depart_date==d)
             .order_by(DailyPrice.captured_at.asc()))
        rows = q.all()
        df = pd.DataFrame([{
            "captured_at": r.captured_at,
            "price": float(r.price),
            "currency": r.currency,
            "source": r.source or ""
        } for r in rows])
        return df
    finally:
        sess.close()

def analyze_variations(df: pd.DataFrame, window: int = 7, drop_z: float = -2.0, epsilon: float = 0.01) -> Dict[str, Any]:
    if df.empty:
        return {"message": "Nessun dato"}
    df = df.sort_values("captured_at").reset_index(drop=True)
    pct = df["price"].pct_change().fillna(0)
    with np.errstate(divide='ignore', invalid='ignore'):
        df["logret"] = np.log1p(pct.replace([-1.0], -0.999999))
    df["roll_min"] = df["price"].rolling(window).min()
    df["roll_mean"] = df["price"].rolling(window).mean()
    df["roll_std"] = df["price"].rolling(window).std()
    df["zscore"] = (df["price"] - df["roll_mean"]) / df["roll_std"]
    latest = df.iloc[-1]
    near_min = bool(latest["price"] <= (latest["roll_min"] * (1 + epsilon)) if pd.notna(latest["roll_min"]) else False)
    drop_signal = bool(latest.get("zscore", 0) <= drop_z) if pd.notna(latest.get("zscore")) else False
    return {
        "latest_price": float(latest["price"]),
        "near_rolling_min": near_min,
        "drop_signal": drop_signal,
        "rolling_window": window,
        "last_zscore": None if pd.isna(latest.get("zscore")) else float(latest["zscore"]),
        "stats": {
            "min": float(df["price"].min()),
            "max": float(df["price"].max()),
            "mean": float(df["price"].mean()),
            "n": int(len(df))
        }
    }

def plot_history(df: pd.DataFrame, title: str = "Prezzo nel tempo") -> str:
    if df.empty:
        return ""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df["captured_at"], df["price"], marker="o", linewidth=1.5)
    ax.set_title(title)
    ax.set_xlabel("Captured at")
    ax.set_ylabel("Price")
    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")
    return data_url
