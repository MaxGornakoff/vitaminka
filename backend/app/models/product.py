from sqlalchemy import Column, String, Text, Float, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.db.base import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = Column(String(100), nullable=False, index=True)
    external_id = Column(String(255), nullable=False)  # ID товара в системе магазина
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String(10), default="RUB")
    
    vendor = Column(String(255), nullable=True)
    category = Column(String(255), nullable=True)
    url = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    
    # Для индексации в ChromaDB
    embedding_id = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Product {self.name}>"
