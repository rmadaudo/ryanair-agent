# --- add at very top ---
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# ------------------------
import os
from ryanair_agent.analysis import load_series, analyze_variations, plot_history

def main():
    origin = os.environ.get("ORIGIN", "BGY")
    destination = os.environ.get("DESTINATION", "CTA")
    depart_date = os.environ.get("DEPART_DATE", "2026-12-20")
    db_url = os.environ.get("DB_URL", None)
    df = load_series(origin, destination, depart_date, db_url)
    res = analyze_variations(df)
    print(res)
    data_url = plot_history(df, title=f"{origin}-{destination} {depart_date} - Prezzi")
    if data_url:
        import base64
        png = base64.b64decode(data_url.split(",",1)[1])
        os.makedirs("data/plots", exist_ok=True)
        out = os.path.join("data", "plots", f"plot_{origin}_{destination}_{depart_date}.png")
        with open(out, "wb") as f:
            f.write(png)
        print(f"Plot salvato: {out}")

if __name__ == "__main__":
    main()
