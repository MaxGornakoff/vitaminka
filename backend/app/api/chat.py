from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import uuid

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

chat_service = ChatService()

@router.post("/message", response_model=ChatMessageResponse)
async def send_message(request: ChatMessageRequest):
    """
    Отправить сообщение в чат и получить ответ от ассистента
    """
    try:
        response = await chat_service.process_message(
            shop_id=request.shop_id,
            session_id=request.session_id,
            user_message=request.message
        )
        return ChatMessageResponse(role="assistant", content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """
    Получить историю диалога
    """
    try:
        messages = await chat_service.get_chat_history(session_id)
        return ChatHistoryResponse(messages=messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
