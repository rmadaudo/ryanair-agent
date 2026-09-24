
# Ryanair Price Agent (LangChain-ready)

> **Nota**: usa l'endpoint Ryanair in modo conforme ai Termini d'Uso. Evita scraping aggressivo; imposta rate limit conservativi.

## Struttura

```
ryanair_price_agent/
├─ ryanair_agent/
│  ├─ ryanair_client.py    # client HTTP + parsing + retry
│  ├─ db.py                # SQLAlchemy models + insert
│  ├─ analysis.py          # rolling min, z-score, plot
│  ├─ tools.py             # LangChain StructuredTools
│  ├─ alerts.py            # email SMTP
│  └─ agent.py             # agent LLM + tool-calling
├─ scripts/
│  ├─ run_collect.py       # raccolta + persist + alert email su variazioni
│  ├─ run_analyze.py       # analisi e plot
├─ data/
│  ├─ exports/
│  └─ plots/
├─ requirements.txt
├─ .env.example
└─ README.md
```

## Setup (Windows)

```powershell
cd C:\percorso\ryanair_price_agent
py -3 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# apri .env e compila SMTP_* e ALERT_TO
```

## Esecuzione manuale

```powershell
$env:ORIGIN="BGY"; $env:DESTINATION="CTA"; $env:START_DATE="2026-12-19"; $env:END_DATE="2026-12-22"
python .\scripts\run_collect.py
```

## Schedulazione (Task Scheduler)
Programma:
```
C:\Windows\System32\cmd.exe
```
Argomenti:
```
/c "cd /d C:\percorso\ryanair_price_agent && .venv\Scripts\python.exe scripts\run_collect.py >> logs\collect.log 2>&1"
```

## Note
- Snapshot salvati in `data/fares.db` (SQLite)
- Email inviata **solo** se un prezzo è cambiato rispetto allo snapshot precedente
- Grafici in `data/plots/`
