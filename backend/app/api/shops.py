from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import uuid

from app.db.session import get_db
from app.models.product import Product
from app.models.shop import Shop
from app.rag.indexer import ProductIndexer
from app.core.config import settings
from app.services.feed_sync import sync_shop_catalog

router = APIRouter()
_SYNC_RUNTIME_STATUS: dict[str, dict] = {}

class ShopRegisterRequest(BaseModel):
    shop_id: str
    name: str
    domain: str
    catalog_url: str
    manager_phone: Optional[str] = None
    assistant_name: Optional[str] = "Ассистент"
    catalog_sync_interval_hours: Optional[int] = None

class ShopResponse(BaseModel):
    shop_id: str
    name: str
    domain: str
    manager_phone: Optional[str] = None
    assistant_name: Optional[str] = None
    api_key: str


class CatalogProductRequest(BaseModel):
    external_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    currency: str = "RUB"
    category: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None


class CatalogUploadRequest(BaseModel):
    products: List[CatalogProductRequest]
    replace_existing: bool = True


class CatalogUploadResponse(BaseModel):
    shop_id: str
    uploaded: int
    total_products: int


class ShopUpdateRequest(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    catalog_url: Optional[str] = None
    manager_phone: Optional[str] = None
    assistant_name: Optional[str] = None
    catalog_sync_interval_hours: Optional[int] = None
    is_active: Optional[bool] = None


def _get_shop_or_404(db: Session, shop_id: str) -> Shop:
    shop = db.query(Shop).filter(Shop.shop_id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


def _validate_api_key(shop: Shop, x_api_key: str | None) -> None:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header is required")
    if x_api_key != shop.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")


def _validate_admin_secret(x_admin_secret: str | None) -> None:
    if not x_admin_secret:
        raise HTTPException(status_code=401, detail="X-Admin-Secret header is required")
    if x_admin_secret != settings.ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")


@router.post("/register", response_model=ShopResponse)
async def register_shop(
    request: ShopRegisterRequest,
    db: Session = Depends(get_db),
    x_admin_secret: Optional[str] = Header(default=None),
):
    """
    Зарегистрировать новый магазин
    """
    _validate_admin_secret(x_admin_secret)
    try:
        existing_shop = db.query(Shop).filter(Shop.shop_id == request.shop_id).first()
        if existing_shop:
            raise HTTPException(status_code=409, detail="Shop with this shop_id already exists")

        api_key = str(uuid.uuid4())
        shop = Shop(
            shop_id=request.shop_id,
            name=request.name,
            domain=request.domain,
            catalog_url=request.catalog_url,
            manager_phone=request.manager_phone,
            assistant_name=request.assistant_name,
            catalog_sync_interval_hours=request.catalog_sync_interval_hours,
            api_key=api_key,
            is_active=True,
        )
        db.add(shop)
        db.commit()

        return ShopResponse(
            shop_id=shop.shop_id,
            name=shop.name,
            domain=shop.domain,
            manager_phone=shop.manager_phone,
            assistant_name=shop.assistant_name,
            api_key=api_key
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{shop_id}")
async def get_shop(shop_id: str, db: Session = Depends(get_db)):
    """
    Получить информацию о магазине
    """
    shop = _get_shop_or_404(db, shop_id)

    return {
        "shop_id": shop.shop_id,
        "name": shop.name,
        "domain": shop.domain,
        "manager_phone": shop.manager_phone,
        "assistant_name": shop.assistant_name,
        "catalog_url": shop.catalog_url,
        "is_active": shop.is_active,
        "widget_theme": {
            "color_primary": shop.widget_color_primary,
            "color_secondary": shop.widget_color_secondary,
            "color_bg": shop.widget_color_bg,
            "border_radius": shop.widget_border_radius,
            "custom_css": shop.widget_custom_css,
        },
    }


@router.patch("/{shop_id}")
async def update_shop(
    shop_id: str,
    request: ShopUpdateRequest,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    """
    Обновить настройки магазина (требует X-API-Key)
    """
    shop = _get_shop_or_404(db, shop_id)
    _validate_api_key(shop, x_api_key)

    updates = request.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(shop, field, value)

    db.commit()
    db.refresh(shop)

    return {
        "shop_id": shop.shop_id,
        "name": shop.name,
        "domain": shop.domain,
        "manager_phone": shop.manager_phone,
        "catalog_url": shop.catalog_url,
        "is_active": shop.is_active,
    }


@router.post("/{shop_id}/catalog", response_model=CatalogUploadResponse)
async def upload_catalog(
    shop_id: str,
    request: CatalogUploadRequest,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    """
    Загрузить каталог товаров магазина
    """
    shop = _get_shop_or_404(db, shop_id)
    _validate_api_key(shop, x_api_key)

    if request.replace_existing:
        db.query(Product).filter(Product.shop_id == shop_id).delete(synchronize_session=False)

    product_rows = []
    for idx, item in enumerate(request.products):
        external_id = item.external_id or f"item_{idx + 1}_{uuid.uuid4().hex[:8]}"
        product_rows.append(
            Product(
                shop_id=shop_id,
                external_id=external_id,
                name=item.name,
                description=item.description,
                price=item.price,
                currency=item.currency,
                category=item.category,
                url=item.url,
                image_url=item.image_url,
            )
        )

    if product_rows:
        db.add_all(product_rows)

    indexer_payload = [
        {
            "external_id": p.external_id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "currency": p.currency,
            "category": p.category,
            "url": p.url,
        }
        for p in product_rows
    ]

    indexer = ProductIndexer()
    await indexer.index_products(
        shop_id=shop_id,
        products=indexer_payload,
        replace_existing=request.replace_existing,
    )

    shop.last_indexed = datetime.utcnow()
    db.commit()

    total_products = db.query(Product).filter(Product.shop_id == shop_id).count()
    return CatalogUploadResponse(
        shop_id=shop_id,
        uploaded=len(product_rows),
        total_products=total_products,
    )


class SyncResponse(BaseModel):
    shop_id: str
    synced: int
    catalog_url: str


class SyncStatusResponse(BaseModel):
    shop_id: str
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    synced_count: Optional[int] = None
    indexed_successfully: Optional[bool] = None
    index_error: Optional[str] = None
    total_products_in_db: int
    last_catalog_synced_at: Optional[datetime] = None
    last_catalog_indexed_at: Optional[datetime] = None


@router.post("/{shop_id}/catalog/sync", response_model=SyncResponse)
async def sync_catalog_from_feed(
    shop_id: str,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    """
    Синхронизировать каталог из внешнего JSON-фида (Яндекс.Маркет и совместимые).
    Использует catalog_url из настроек магазина.
    """
    shop = _get_shop_or_404(db, shop_id)
    _validate_api_key(shop, x_api_key)

    if not shop.catalog_url:
        raise HTTPException(
            status_code=400,
            detail="У магазина не задан catalog_url. Укажите его в настройках магазина."
        )

    started_at = datetime.utcnow()
    _SYNC_RUNTIME_STATUS[shop_id] = {
        "status": "running",
        "started_at": started_at,
        "finished_at": None,
        "synced_count": None,
        "indexed_successfully": None,
        "index_error": None,
    }

    try:
        result = await sync_shop_catalog(shop, db)
    except ValueError as e:
        _SYNC_RUNTIME_STATUS[shop_id] = {
            "status": "failed",
            "started_at": started_at,
            "finished_at": datetime.utcnow(),
            "synced_count": None,
            "indexed_successfully": False,
            "index_error": str(e),
        }
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        _SYNC_RUNTIME_STATUS[shop_id] = {
            "status": "failed",
            "started_at": started_at,
            "finished_at": datetime.utcnow(),
            "synced_count": None,
            "indexed_successfully": False,
            "index_error": str(e),
        }
        raise HTTPException(status_code=502, detail=str(e))

    _SYNC_RUNTIME_STATUS[shop_id] = {
        "status": "completed" if result.indexed_successfully else "completed_with_index_error",
        "started_at": started_at,
        "finished_at": datetime.utcnow(),
        "synced_count": result.synced_count,
        "indexed_successfully": result.indexed_successfully,
        "index_error": result.index_error,
    }

    return SyncResponse(shop_id=shop_id, synced=result.synced_count, catalog_url=shop.catalog_url)


@router.get("/{shop_id}/catalog/sync/status", response_model=SyncStatusResponse)
async def get_catalog_sync_status(
    shop_id: str,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    """
    Статус синхронизации каталога для polling из UI/скриптов.
    """
    shop = _get_shop_or_404(db, shop_id)
    _validate_api_key(shop, x_api_key)

    runtime = _SYNC_RUNTIME_STATUS.get(shop_id) or {}
    total_products = db.query(Product).filter(Product.shop_id == shop_id).count()

    if runtime:
        status = runtime.get("status") or "idle"
    elif shop.last_catalog_synced_at:
        status = "idle"
    else:
        status = "never_started"

    return SyncStatusResponse(
        shop_id=shop_id,
        status=status,
        started_at=runtime.get("started_at"),
        finished_at=runtime.get("finished_at"),
        synced_count=runtime.get("synced_count"),
        indexed_successfully=runtime.get("indexed_successfully"),
        index_error=runtime.get("index_error"),
        total_products_in_db=total_products,
        last_catalog_synced_at=shop.last_catalog_synced_at,
        last_catalog_indexed_at=shop.last_catalog_indexed_at,
    )
