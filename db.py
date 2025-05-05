from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
import os

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class PokerHand(Base):
    __tablename__ = "poker_hands"
    id = Column(Integer, primary_key=True, index=True)
    hand = Column(String)
    action_preflop = Column(String)
    position = Column(String)
    action_flop = Column(String)
    action_turn = Column(String)
    action_river = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def insert_hand(data: dict):
    async with SessionLocal() as session:
        record = PokerHand(**data)
        session.add(record)
        await session.commit()

async def fetch_all_hands():
    async with SessionLocal() as session:
        result = await session.execute(
            PokerHand.__table__.select().order_by(PokerHand.timestamp.desc())
        )
        return result.fetchall()
