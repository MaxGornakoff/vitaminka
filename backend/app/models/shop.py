from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.db.base import Base

class Shop(Base):
    __tablename__ = "shops"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=True)
    manager_phone = Column(String(30), nullable=True)
    description = Column(Text, nullable=True)
    api_key = Column(String(255), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    
    catalog_url = Column(Text, nullable=True)  # URL каталога товаров
    assistant_name = Column(String(255), nullable=True, default="Ассистент")  # Имя в UI виджета
    last_indexed = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Shop {self.shop_id}>"
