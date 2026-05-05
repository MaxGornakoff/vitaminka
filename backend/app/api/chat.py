from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.chat_service import ChatService

router = APIRouter()

class ChatMessageRequest(BaseModel):
    shop_id: str
    session_id: str
    message: str

class ChatMessageResponse(BaseModel):
    role: str
    content: str

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse]

@router.get("/message")
async def message_usage():
    """
    Подсказка по использованию endpoint /message
    """
    return {
        "detail": "Use POST /api/chat/message with JSON body",
        "example": {
            "shop_id": "demo_shop_db",
            "session_id": "sess_123",
            "message": "Помоги подобрать витамины"
        }
    }

@router.post("/message", response_model=ChatMessageResponse)
async def send_message(request: ChatMessageRequest, db: Session = Depends(get_db)):
    """
    Отправить сообщение в чат и получить ответ от ассистента
    """
    try:
        chat_service = ChatService(db=db)
        response = await chat_service.process_message(
            shop_id=request.shop_id,
            session_id=request.session_id,
            user_message=request.message
        )
        return ChatMessageResponse(role="assistant", content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """
    Получить историю диалога
    """
    try:
        chat_service = ChatService(db=db)
        messages = await chat_service.get_chat_history(session_id)
        return ChatHistoryResponse(messages=messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
