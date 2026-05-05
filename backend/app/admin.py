from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.core.config import settings
from app.db.session import engine
from app.models.shop import Shop
from app.models.product import Product
from app.models.chat import ChatSession, ChatMessage


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username", "")
        password = form.get("password", "")
        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            request.session["admin_authenticated"] = True
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("admin_authenticated", False)


class ShopAdmin(ModelView, model=Shop):
    name = "Магазин"
    name_plural = "Магазины"
    icon = "fa-solid fa-store"

    column_list = [
        Shop.shop_id,
        Shop.name,
        Shop.assistant_name,
        Shop.domain,
        Shop.manager_phone,
        Shop.is_active,
        Shop.created_at,
    ]
    column_searchable_list = [Shop.shop_id, Shop.name, Shop.domain]
    column_sortable_list = [Shop.created_at, Shop.name, Shop.is_active]

    form_columns = [
        Shop.shop_id,
        Shop.name,
        Shop.assistant_name,
        Shop.domain,
        Shop.catalog_url,
        Shop.manager_phone,
        Shop.is_active,
    ]

    # api_key доступен только для чтения — не включаем в форму редактирования
    column_details_list = [
        Shop.shop_id,
        Shop.name,
        Shop.assistant_name,
        Shop.domain,
        Shop.catalog_url,
        Shop.manager_phone,
        Shop.api_key,
        Shop.is_active,
        Shop.last_indexed,
        Shop.created_at,
        Shop.updated_at,
    ]


class ProductAdmin(ModelView, model=Product):
    name = "Товар"
    name_plural = "Товары"
    icon = "fa-solid fa-box"

    column_list = [
        Product.shop_id,
        Product.name,
        Product.price,
        Product.currency,
        Product.category,
        Product.created_at,
    ]
    column_searchable_list = [Product.shop_id, Product.name, Product.category]
    column_sortable_list = [Product.created_at, Product.price, Product.name]

    form_columns = [
        Product.shop_id,
        Product.external_id,
        Product.name,
        Product.description,
        Product.price,
        Product.currency,
        Product.category,
        Product.url,
        Product.image_url,
    ]


class ChatSessionAdmin(ModelView, model=ChatSession):
    name = "Сессия"
    name_plural = "Сессии чатов"
    icon = "fa-solid fa-comments"
    can_create = False
    can_edit = False
    can_delete = True

    column_list = [
        ChatSession.shop_id,
        ChatSession.session_id,
        ChatSession.user_identifier,
        ChatSession.created_at,
    ]
    column_searchable_list = [ChatSession.shop_id, ChatSession.session_id]
    column_sortable_list = [ChatSession.created_at]


class ChatMessageAdmin(ModelView, model=ChatMessage):
    name = "Сообщение"
    name_plural = "Сообщения чатов"
    icon = "fa-solid fa-message"
    can_create = False
    can_edit = False

    column_list = [
        ChatMessage.session_id,
        ChatMessage.role,
        ChatMessage.content,
        ChatMessage.created_at,
    ]
    column_searchable_list = [ChatMessage.session_id, ChatMessage.role]
    column_sortable_list = [ChatMessage.created_at]


def create_admin(app) -> Admin:
    authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)
    admin = Admin(
        app,
        engine,
        authentication_backend=authentication_backend,
        title="Vitaminka Admin",
    )
    admin.add_view(ShopAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(ChatSessionAdmin)
    admin.add_view(ChatMessageAdmin)
    return admin
