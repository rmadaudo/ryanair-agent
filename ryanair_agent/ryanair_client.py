
import time
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def _build_session(total_retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    """Create a requests Session with retry/backoff for transient errors."""
    s = requests.Session()
    retry = Retry(
        total=total_retries,
        read=total_retries,
        connect=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"])
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

def _month_start(d: date) -> date:
    return d.replace(day=1)

def _add_month(d: date) -> date:
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)

def _parse_fares(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Leniently parse Ryanair 'cheapestPerDay' payload into a list of {day, price, currency}."""
    if not isinstance(payload, dict):
        return []
    fares = []
    container = (payload.get("outbound") or {})
    fares_list = container.get("fares") or payload.get("fares") or []
    for item in fares_list:
        day = item.get("day") or item.get("date") or item.get("dateOut") or item.get("departureDate")
        price_info = item.get("price")
        price_val = None
        currency = None
        if isinstance(price_info, dict):
            price_val = (
                price_info.get("value")
                or price_info.get("amount")
                or price_info.get("regular")
                or price_info.get("min")
            )
            currency = price_info.get("currencyCode") or price_info.get("currency")
        elif isinstance(price_info, (int, float)):
            price_val = float(price_info)
        if day and price_val is not None:
            fares.append({"day": day, "price": float(price_val), "currency": currency})
    return fares

def collect_ryanair_cheapest_per_day(
    orig: str,
    dest: str,
    start_date: str,
    end_date: str,
    currency: str = "EUR",
    sleep_sec: float = 0.5,
    session: Optional[requests.Session] = None
) -> List[Dict[str, Any]]:
    """
    Collect 'cheapest per day' fares from Ryanair for [start_date, end_date] inclusive.
    Returns list of dicts: {date, price, currency, origin, destination, source}.
    """
    sdate = datetime.strptime(start_date, "%Y-%m-%d").date()
    edate = datetime.strptime(end_date, "%Y-%m-%d").date()
    if edate < sdate:
        raise ValueError("end_date must be >= start_date")

    """ MODIFICA X USO PROXY
    url = f"https://www.ryanair.com/api/farfnd/v4/oneWayFares/{orig}/{dest}/cheapestPerDay"
    """
    headers = {
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/117.0 Safari/537.36"
        ),
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    }

    _url = f"https://europe-west1-ryanair-proxy.cloudfunctions.net/ryanair_api_proxy/?host=www.ryanair.com&path=/api/farfnd/v4/oneWayFares/{orig}/{dest}/cheapestPerDay&outboundMonthOfDate="
    sess = session or _build_session()
    cur = _month_start(sdate)
    per_day_min: Dict[date, float] = {}
    detected_currency: Optional[str] = None

    while cur <= edate:
        params = {"outboundMonthOfDate": cur.isoformat(), "currency": currency}
        # MODIFICA X USO PROXY
        params = {}
        url = _url + "{}".format(cur.isoformat())
        # FINE MODIFICA
        try:
            resp = sess.get(url, params=params, headers=headers, timeout=20, verify=False)
            resp.raise_for_status()
            payload = resp.json()
            print(payload)
            for rec in _parse_fares(payload):
                try:
                    d = datetime.fromisoformat(rec["day"][:10]).date()
                except Exception:
                    continue
                if sdate <= d <= edate:
                    p = float(rec["price"])
                    if (d not in per_day_min) or (p < per_day_min[d]):
                        per_day_min[d] = p
                if not detected_currency and rec.get("currency"):
                    detected_currency = rec["currency"]
        except Exception as e:
            print(e)
        time.sleep(sleep_sec)
        cur = _add_month(cur)

    out: List[Dict[str, Any]] = []
    for d in sorted(per_day_min.keys()):
        out.append({
            "date": d.isoformat(),
            "price": round(per_day_min[d], 2),
            "currency": detected_currency or currency,
            "origin": orig.upper(),
            "destination": dest.upper(),
            "source": "ryanair_farfnd_v4"
        })
    return out
