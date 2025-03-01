from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean

Base = declarative_base()

class Client(Base):
    __tablename__ = "clients"
    
    client_id = Column(Integer, primary_key=True)
    api_key = Column(String)
    api_secret = Column(String)
    is_testnet = Column(Boolean, default=False)
    bots = relationship("Bot", back_populates="client")

class Bot(Base):
    __tablename__ = "bots"
    
    bot_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.client_id"))
    pair = Column(String, nullable=False)
    status = Column(String, nullable=False)
    lower_price = Column(Float, nullable=False)
    upper_price = Column(Float, nullable=False)
    grids = Column(Integer, nullable=False)
    capital_btc = Column(Float, nullable=True)
    
    client = relationship("Client", back_populates="bots")
    trades = relationship("Trade", back_populates="bot")

class Trade(Base):
    __tablename__ = "trades"
    
    trade_id = Column(Integer, primary_key=True)
    bot_id = Column(Integer, ForeignKey("bots.bot_id"))
    timestamp = Column(DateTime, nullable=False)
    amount_btc = Column(Float, nullable=False)
    profit_btc = Column(Float, nullable=False)
    
    bot = relationship("Bot", back_populates="trades") 