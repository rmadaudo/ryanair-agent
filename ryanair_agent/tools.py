
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Optional
import csv
import os

from .ryanair_client import collect_ryanair_cheapest_per_day
from .db import init_db, get_session, insert_prices
from .analysis import load_series, analyze_variations, plot_history

DATA_DIR = os.environ.get("DATA_DIR", "data")

class CheapestInput(BaseModel):
    origin: str = Field(..., description="IATA origin, e.g., BGY")
    destination: str = Field(..., description="IATA destination, e.g., CTA")
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")
    currency: str = Field("EUR", description="Currency code")
    db_url: Optional[str] = Field(None, description="SQLAlchemy DB url, defaults to sqlite:///data/fares.db")

def cheapest_tool(origin: str, destination: str, start_date: str, end_date: str, currency: str = "EUR", db_url: Optional[str] = None) -> str:
    rows = collect_ryanair_cheapest_per_day(origin, destination, start_date, end_date, currency)
    if not rows:
        return f"Nessun dato per {origin}-{destination} nel periodo {start_date}→{end_date}."
    os.makedirs(os.path.join(DATA_DIR, "exports"), exist_ok=True)
    csv_path = os.path.join(DATA_DIR, "exports", f"cheapest_{origin}_{destination}_{start_date}_{end_date}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "price", "currency", "origin", "destination", "source"]) 
        w.writeheader(); w.writerows(rows)
    init_db(db_url)
    sess = get_session(db_url)
    try:
        inserted = insert_prices(sess, rows)
    finally:
        sess.close()
    prices = [r['price'] for r in rows]
    return (f"Raccolti {len(rows)} giorni; salvato CSV in {csv_path}. "
            f"DB insert: {inserted}. Min/Max: {min(prices):.2f}/{max(prices):.2f} {rows[0]['currency']}")

CheapestPerDayTool = StructuredTool.from_function(
    func=cheapest_tool,
    name="ryanair_cheapest_per_day",
    description="Raccoglie i prezzi minimi giornalieri per un intervallo di date e salva CSV + DB.",
    args_schema=CheapestInput
)

class AnalyzeInput(BaseModel):
    origin: str = Field(...)
    destination: str = Field(...)
    depart_date: str = Field(..., description="YYYY-MM-DD")
    db_url: Optional[str] = Field(None)

def analyze_tool(origin: str, destination: str, depart_date: str, db_url: Optional[str] = None) -> str:
    df = load_series(origin, destination, depart_date, db_url)
    res = analyze_variations(df)
    if "message" in res:
        return f"Nessun dato per {origin}-{destination} {depart_date}."
    return (f"Analisi {origin}-{destination} {depart_date}
"
            f"Prezzo attuale: {res['latest_price']:.2f}
"
            f"Vicino al minimo rolling: {res['near_rolling_min']}
"
            f"Drop (z-score): {res['drop_signal']} (z={res['last_zscore']})
"
            f"Campioni: {res['stats']['n']} | Min/Max/Mean: {res['stats']['min']:.2f}/{res['stats']['max']:.2f}/{res['stats']['mean']:.2f}")

AnalyzeTool = StructuredTool.from_function(
    func=analyze_tool,
    name="compute_alerts",
    description="Analizza variazioni, rolling min e segnali di drop per una rotta e una data.",
    args_schema=AnalyzeInput
)

class PlotInput(BaseModel):
    origin: str
    destination: str
    depart_date: str = Field(..., description="YYYY-MM-DD")
    db_url: Optional[str] = Field(None)

def plot_tool(origin: str, destination: str, depart_date: str, db_url: Optional[str] = None) -> str:
    df = load_series(origin, destination, depart_date, db_url)
    if df.empty:
        return "Nessun dato da plottare."
    title = f"{origin}-{destination} {depart_date} - Prezzo nel tempo"
    data_url = plot_history(df, title)
    os.makedirs(os.path.join(DATA_DIR, "plots"), exist_ok=True)
    import base64
    b64 = data_url.split(",", 1)[1]
    png_bytes = base64.b64decode(b64)
    file_path = os.path.join(DATA_DIR, "plots", f"plot_{origin}_{destination}_{depart_date}.png")
    with open(file_path, "wb") as f:
        f.write(png_bytes)
    return f"Grafico generato: {file_path}"

PlotTool = StructuredTool.from_function(
    func=plot_tool,
    name="plot_history",
    description="Crea un grafico PNG dell'andamento del prezzo per una rotta+data.",
    args_schema=PlotInput
)
