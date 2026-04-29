from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid

from app.db.session import get_db
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
