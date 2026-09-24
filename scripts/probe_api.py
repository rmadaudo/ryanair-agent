
import os, json
from ryanair_agent.ryanair_client import collect_ryanair_cheapest_per_day

origin = os.environ.get("ORIGIN", "BGY")
destination = os.environ.get("DESTINATION", "CTA")
start_date = os.environ.get("START_DATE", "2026-12-19")
end_date = os.environ.get("END_DATE", "2026-12-22")
currency = os.environ.get("CURRENCY", "EUR")

rows = collect_ryanair_cheapest_per_day(origin, destination, start_date, end_date, currency)
print(f"Collected {len(rows)} rows.")
print("Sample:", json.dumps(rows[:5], indent=2, ensure_ascii=False))
