# --- add at very top ---
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# ------------------------
import os
from dotenv import load_dotenv
from ryanair_agent.ryanair_client import collect_ryanair_cheapest_per_day
from ryanair_agent.db import init_db, get_session, insert_prices, get_latest_price
from ryanair_agent.alerts import send_email, send_telegram

load_dotenv()

def main():
    origin = os.environ.get("ORIGIN", "BGY")
    destination = os.environ.get("DESTINATION", "CTA")
    start_date = os.environ.get("START_DATE", "2026-12-19")
    end_date = os.environ.get("END_DATE", "2026-12-22")
    currency = os.environ.get("CURRENCY", "EUR")
    db_url = os.environ.get("DB_URL", None)

    print(f"Collecting {origin}-{destination} {start_date}→{end_date} ...")
    rows = collect_ryanair_cheapest_per_day(origin, destination, start_date, end_date, currency)
    print(f"Collected {len(rows)} daily prices. Preparing change detection ...")

    # Snapshot previous prices before inserting
    prev_map = {}
    init_db(db_url)
    sess = get_session(db_url)
    try:
        for r in rows:
            d = r['date']
            prev = get_latest_price(sess, origin, destination, d)
            if prev:
                prev_map[d] = float(prev.price), prev.captured_at
    finally:
        sess.close()

    # Insert new snapshot batch
    init_db(db_url)
    sess = get_session(db_url)
    try:
        inserted = insert_prices(sess, rows)
        print(f"Inserted {inserted} rows.")
    finally:
        sess.close()

    # Build alert on changes vs previous snapshot
    changes = []
    from datetime import datetime as _dt
    now_iso = _dt.utcnow().isoformat(timespec='seconds') + 'Z'
    for r in rows:
        d = r['date']
        new_p = float(r['price'])
        if d in prev_map:
            old_p, old_ts = prev_map[d]
            if abs(new_p - old_p) > 1e-6:
                delta = new_p - old_p
                pct = (delta / old_p) * 100 if old_p else 0.0
                changes.append({
                    'date': d,
                    'origin': origin,
                    'destination': destination,
                    'old_price': old_p,
                    'new_price': new_p,
                    'delta': delta,
                    'pct': pct,
                    'old_ts': str(old_ts),
                    'new_ts': now_iso,
                    'currency': r.get('currency','EUR')
                })

    if changes and os.environ.get('ALERT_EMAIL_ENABLED','1').lower() in ('1','true','yes','on'):
        rows_html = ''.join([
            (
                f"<tr>"
                f"<td>{c['origin']}</td>"
                f"<td>{c['destination']}</td>"
                f"<td>{c['date']}</td>"
                f"<td style='text-align:right'>{c['old_price']:.2f} {c['currency']}</td>"
                f"<td style='text-align:right'>{c['new_price']:.2f} {c['currency']}</td>"
                f"<td style='text-align:right'>{c['delta']:+.2f}</td>"
                f"<td style='text-align:right'>{c['pct']:+.2f}%</td>"
                f"<td>{c['old_ts']} → {c['new_ts']}</td>"
                f"</tr>"
            ) for c in changes
        ])
        html = (
            "<h3>Variazioni prezzo rilevate</h3>"
            f"<p>Route {origin}→{destination} | Finestra {start_date}→{end_date}</p>"
            "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse'>"
            "<thead><tr><th>Orig</th><th>Dest</th><th>Data volo</th><th>Prezzo prec.</th><th>Prezzo nuovo</th><th>Δ</th><th>Δ%</th><th>Timestamp</th></tr></thead>"
            f"<tbody>{rows_html}</tbody></table>"
        )
        subject = f"[FARES] {origin}→{destination}: {len(changes)} variazioni di prezzo"
        try:
            send_email(subject=subject, html_body=html)
            print(f"Alert email inviata: {len(changes)} variazioni")
            send_telegram(html)
        except Exception as e:
            print(f"Errore invio email: {e}")
        rows = []
        for c in changes:
            trend_emoji = "📉" if c["delta"] < 0 else "📈"
            rows.append(
                f"{trend_emoji} <b>{c['origin']} → {c['destination']}</b> ({c['date']})\n"
                f"• Prezzo: <code>{c['old_price']:.2f}</code> → <b>{c['new_price']:.2f} {c['currency']}</b>\n"
                f"• Variazione: <b>{c['delta']:+.2f} {c['currency']}</b> ({c['pct']:+.2f}%)\n"
                f"• Rilevato: <i>{c['old_ts']} → {c['new_ts']}</i>"
            )

        rows_text = "\n\n".join(rows)

        telegram_message = (
            "🔔 <b>Variazioni prezzo rilevate</b>\n"
            f"📍 Rotta: <b>{origin} → {destination}</b>\n"
            f"📅 Finestra: <code>{start_date} → {end_date}</code>\n\n"
            f"{rows_text}"
        )
        try:
            send_email(subject=subject, html_body=html)
            print(f"Alert tgr inviato: {len(changes)} variazioni")
            send_telegram(html)
        except Exception as e:
            print(f"Errore invio email: {e}")
    else:
        print("Nessuna variazione di prezzo rispetto allo snapshot precedente.")


if __name__ == "__main__":
    main()
