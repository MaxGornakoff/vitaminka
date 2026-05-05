from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import uuid

from app.db.session import get_db
from app.models.product import Product
from app.models.shop import Shop

router = APIRouter()

class ShopRegisterRequest(BaseModel):
    shop_id: str
    name: str
    domain: str
    catalog_url: str

class ShopResponse(BaseModel):
    shop_id: str
    name: str
    domain: str
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

@router.post("/register", response_model=ShopResponse)
async def register_shop(request: ShopRegisterRequest, db: Session = Depends(get_db)):
    """
    Зарегистрировать новый магазин
    """
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
            api_key=api_key,
            is_active=True,
        )
        db.add(shop)
        db.commit()

        return ShopResponse(
            shop_id=shop.shop_id,
            name=shop.name,
            domain=shop.domain,
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
    shop = db.query(Shop).filter(Shop.shop_id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    return {
        "shop_id": shop.shop_id,
        "name": shop.name,
        "domain": shop.domain,
        "catalog_url": shop.catalog_url,
        "is_active": shop.is_active,
    }


@router.post("/{shop_id}/catalog", response_model=CatalogUploadResponse)
async def upload_catalog(shop_id: str, request: CatalogUploadRequest, db: Session = Depends(get_db)):
    """
    Загрузить каталог товаров магазина
    """
    shop = db.query(Shop).filter(Shop.shop_id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

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

    shop.last_indexed = datetime.utcnow()
    db.commit()

    total_products = db.query(Product).filter(Product.shop_id == shop_id).count()
    return CatalogUploadResponse(
        shop_id=shop_id,
        uploaded=len(product_rows),
        total_products=total_products,
    )
