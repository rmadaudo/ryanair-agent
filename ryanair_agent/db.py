
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import (
    create_engine, Column, Integer, String, Date, DateTime, Numeric, UniqueConstraint
)

from sqlalchemy.orm import declarative_base, sessionmaker

DEFAULT_DB_URL = "sqlite:///data/fares.db"

Base = declarative_base()

class DailyPrice(Base):
    __tablename__ = "daily_prices"
    id = Column(Integer, primary_key=True)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    depart_date = Column(Date, nullable=False)
    captured_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    price = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    source = Column(String, nullable=True)
    __table_args__ = (
        UniqueConstraint("origin", "destination", "depart_date", "captured_at", name="uq_price_snapshot"),
    )

def get_engine(db_url: str = None):
    return create_engine(db_url or DEFAULT_DB_URL, future=True)

def init_db(db_url: str = None):
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    return engine

def get_session(db_url: str = None):
    engine = get_engine(db_url)
    return sessionmaker(bind=engine, future=True)()

def insert_prices(session, rows: List[Dict[str, Any]]):
    """Insert a batch of price snapshots; ignores duplicates violating the unique constraint."""
    now = datetime.utcnow()
    inserted = 0
    for r in rows:
        try:
            rec = DailyPrice(
                origin=r["origin"],
                destination=r["destination"],
                depart_date=datetime.strptime(r["date"], "%Y-%m-%d").date(),
                captured_at=now,
                price=str(r["price"]),
                currency=r.get("currency", "EUR"),
                source=r.get("source")
            )
            session.add(rec)
            session.commit()
            inserted += 1
        except Exception as e:
            print(e)
            session.rollback()
    return inserted

def get_latest_price(session, origin: str, destination: str, depart_date: str):
    d = datetime.strptime(depart_date, "%Y-%m-%d").date()
    rec = (session.query(DailyPrice)
           .filter(DailyPrice.origin==origin.upper(),
                   DailyPrice.destination==destination.upper(),
                   DailyPrice.depart_date==d)
           .order_by(DailyPrice.captured_at.desc())
           .first())
    return rec
