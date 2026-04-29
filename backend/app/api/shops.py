from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid

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
async def register_shop(request: ShopRegisterRequest):
    """
    Зарегистрировать новый магазин
    """
    try:
        api_key = str(uuid.uuid4())
        # TODO: Сохранить в БД
        return ShopResponse(
            shop_id=request.shop_id,
            name=request.name,
            domain=request.domain,
            api_key=api_key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{shop_id}")
async def get_shop(shop_id: str):
    """
    Получить информацию о магазине
    """
    # TODO: Получить из БД
    return {"shop_id": shop_id, "status": "ok"}
