from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer
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
    catalog_sync_interval_hours = Column(Integer, nullable=True)  # null = использовать CATALOG_SYNC_INTERVAL_HOURS из .env
    last_indexed = Column(DateTime, nullable=True)

    # Widget theme
    widget_color_primary = Column(String(30), nullable=True)    # Основной цвет (градиент от), напр. "#3498db"
    widget_color_secondary = Column(String(30), nullable=True)  # Вторичный цвет (градиент до), напр. "#2c3e50"
    widget_color_bg = Column(String(30), nullable=True)         # Фон области чата, напр. "#f0f4f8"
    widget_border_radius = Column(Integer, nullable=True)       # Скругление окна чата (px), напр. 20
    widget_custom_css = Column(Text, nullable=True)             # Произвольный CSS для Shadow DOM
    widget_currency_symbol = Column(String(20), nullable=True)  # Символ валюты для цен, напр. "₽" или "руб."
    last_catalog_synced_at = Column(DateTime, nullable=True)
    last_catalog_indexed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Shop {self.shop_id}>"
