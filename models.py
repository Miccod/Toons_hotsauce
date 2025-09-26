from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    product_sku = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="cad")
    stripe_session_id = Column(String, unique=True)
    status = Column(String, default="pending")  # pending, paid, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    fulfilled = Column(Boolean, default=False)
