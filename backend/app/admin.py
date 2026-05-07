from html import escape
import logging
from urllib.parse import quote_plus
import uuid

from markupsafe import Markup
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.models.chat import ChatMessage, ChatSession
from app.models.product import Product
from app.models.shop import Shop
from app.api.shops import _SYNC_RUNTIME_STATUS
from app.services.chat_service import ChatService
from app.services.feed_sync import sync_shop_catalog

logger = logging.getLogger(__name__)


def _render_admin_page(title: str, body: str, status_code: int = 200) -> HTMLResponse:
    html = f"""
    <html>
        <head>
            <meta charset=\"utf-8\" />
            <title>{title}</title>
        </head>
        <body style=\"font-family:Segoe UI,Arial,sans-serif;background:#f5f7fb;padding:32px;\">
            <div style=\"max-width:920px;margin:0 auto;background:#fff;border-radius:14px;padding:24px;box-shadow:0 10px 30px rgba(15,23,42,0.08);\">
                {body}
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=status_code)


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
        Shop.catalog_sync_interval_hours,
        Shop.manager_phone,
        Shop.is_active,
    ]

    column_details_list = [
        Shop.shop_id,
        Shop.name,
        Shop.assistant_name,
        Shop.domain,
        Shop.catalog_url,
        Shop.catalog_sync_interval_hours,
        Shop.manager_phone,
        Shop.api_key,
        Shop.is_active,
        Shop.last_indexed,
        Shop.last_catalog_synced_at,
        Shop.last_catalog_indexed_at,
        Shop.created_at,
        Shop.updated_at,
    ]

    column_formatters_detail = {
        Shop.shop_id: lambda model, attr: Markup(
            f"""
            <div>{model.shop_id}</div>
            <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;">
                <form method="post" action="/admin-action/shop/{model.shop_id}/sync" style="display:inline;">
                    <button type="submit" style="padding:8px 12px;border:none;border-radius:6px;background:#1769e0;color:#fff;cursor:pointer;">Синхронизировать каталог</button>
                </form>
                <a href="/admin-action/shop/{model.shop_id}/sync/status" style="display:inline-block;padding:8px 12px;border-radius:6px;background:#f59e0b;color:#fff;text-decoration:none;">📊 Статус синхронизации</a>
                <a href="/admin-action/shop/{model.shop_id}/assistant-check" style="display:inline-block;padding:8px 12px;border-radius:6px;background:#0f766e;color:#fff;text-decoration:none;">Проверить ассистента</a>
            </div>
            """
        )
    }

    async def on_model_change(self, data: dict, model: Shop, is_created: bool, request: Request) -> None:
        if is_created and not getattr(model, "api_key", None):
            model.api_key = str(uuid.uuid4())


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

    @app.post("/admin-action/shop/{shop_id}/sync")
    async def admin_sync_shop_catalog(request: Request, shop_id: str):
        if not await authentication_backend.authenticate(request):
            return RedirectResponse(url="/admin/login", status_code=302)

        db = SessionLocal()
        try:
            shop = db.query(Shop).filter(Shop.shop_id == shop_id).first()
            if not shop:
                return RedirectResponse(url="/admin/shop/list", status_code=302)

            result = await sync_shop_catalog(shop, db)
            logger.info("Синхронизация %s через admin: %d товаров", shop_id, result.synced_count)

            index_status = "Индексация завершена успешно" if result.indexed_successfully else "Индексация завершилась с предупреждением"
            index_details = ""
            if not result.indexed_successfully:
                index_details = f'<p style="margin:12px 0 0;color:#92400e;"><strong>Детали:</strong> {escape(result.index_error or "Неизвестная ошибка")}</p>'

            body = f"""
            <h1 style=\"margin:0 0 16px;font-size:28px;\">Синхронизация завершена</h1>
            <p style=\"margin:0 0 12px;font-size:16px;\"><strong>Магазин:</strong> {escape(shop.name)} ({escape(shop.shop_id)})</p>
            <p style=\"margin:0 0 12px;font-size:16px;\"><strong>Загружено товаров:</strong> {result.synced_count}</p>
            <p style=\"margin:0 0 12px;font-size:16px;\"><strong>Статус индексации:</strong> {index_status}</p>
            <p style=\"margin:0 0 12px;font-size:16px;\"><strong>Последний импорт товаров:</strong> {shop.last_catalog_synced_at or '—'}</p>
            <p style=\"margin:0 0 12px;font-size:16px;\"><strong>Последняя успешная индексация:</strong> {shop.last_catalog_indexed_at or '—'}</p>
            {index_details}
            <div style=\"margin-top:24px;display:flex;gap:12px;\">
                <a href=\"/admin/shop/details/{shop.id}\" style=\"padding:10px 14px;border-radius:8px;background:#1769e0;color:#fff;text-decoration:none;\">Назад к магазину</a>
                <a href=\"/admin/product/list\" style=\"padding:10px 14px;border-radius:8px;background:#e8eefc;color:#1d4ed8;text-decoration:none;\">Открыть товары</a>
                <a href=\"/admin-action/shop/{shop.shop_id}/assistant-check\" style=\"padding:10px 14px;border-radius:8px;background:#d1fae5;color:#065f46;text-decoration:none;\">Проверить ассистента</a>
            </div>
            """
            return _render_admin_page("Результат синхронизации", body)
        except Exception as exc:
            logger.error("Ошибка синхронизации %s: %s", shop_id, exc, exc_info=True)
            body = f"""
            <h1 style=\"margin:0 0 16px;font-size:28px;color:#b91c1c;\">Синхронизация не выполнена</h1>
            <p style=\"margin:0 0 12px;font-size:16px;\"><strong>Магазин:</strong> {escape(shop_id)}</p>
            <p style=\"margin:0 0 12px;font-size:16px;color:#7f1d1d;\">{escape(str(exc))}</p>
            <div style=\"margin-top:24px;display:flex;gap:12px;\">
                <a href=\"/admin/shop/list\" style=\"padding:10px 14px;border-radius:8px;background:#1769e0;color:#fff;text-decoration:none;\">Назад к магазинам</a>
            </div>
            """
            return _render_admin_page("Ошибка синхронизации", body, status_code=500)
        finally:
            db.close()

    @app.get("/admin-action/shop/{shop_id}/assistant-check")
    async def admin_assistant_check_page(request: Request, shop_id: str, question: str | None = None):
        if not await authentication_backend.authenticate(request):
            return RedirectResponse(url="/admin/login", status_code=302)

        db = SessionLocal()
        try:
            shop = db.query(Shop).filter(Shop.shop_id == shop_id).first()
            if not shop:
                return RedirectResponse(url="/admin/shop/list", status_code=302)

            default_question = "Есть ли у вас протеин Optimum Nutrition 100% Whey Gold Standard?"
            body = f"""
            <h1 style=\"margin:0 0 16px;font-size:28px;\">Проверка ассистента</h1>
            <p style=\"margin:0 0 16px;font-size:16px;\"><strong>Магазин:</strong> {escape(shop.name)} ({escape(shop.shop_id)})</p>
            <form method=\"post\" action=\"/admin-action/shop/{shop.shop_id}/assistant-check\">
                <label for=\"question\" style=\"display:block;margin-bottom:8px;font-weight:600;\">Тестовый вопрос</label>
                <textarea id=\"question\" name=\"question\" rows=\"4\" style=\"width:100%;padding:12px;border:1px solid #cbd5e1;border-radius:10px;resize:vertical;\">{escape(question or default_question)}</textarea>
                <div style=\"margin-top:16px;display:flex;gap:12px;\">
                    <button type=\"submit\" style=\"padding:10px 14px;border:none;border-radius:8px;background:#0f766e;color:#fff;cursor:pointer;\">Отправить вопрос</button>
                    <a href=\"/admin/shop/details/{shop.id}\" style=\"padding:10px 14px;border-radius:8px;background:#e8eefc;color:#1d4ed8;text-decoration:none;\">Назад к магазину</a>
                </div>
            </form>
            """
            return _render_admin_page("Проверка ассистента", body)
        finally:
            db.close()

    @app.post("/admin-action/shop/{shop_id}/assistant-check")
    async def admin_assistant_check_run(request: Request, shop_id: str):
        if not await authentication_backend.authenticate(request):
            return RedirectResponse(url="/admin/login", status_code=302)

        db = SessionLocal()
        try:
            shop = db.query(Shop).filter(Shop.shop_id == shop_id).first()
            if not shop:
                return RedirectResponse(url="/admin/shop/list", status_code=302)

            form = await request.form()
            question = (form.get("question") or "").strip() or "Есть ли у вас товары из каталога?"

            chat_service = ChatService(db=db)
            answer = await chat_service.process_message(
                shop_id=shop.shop_id,
                session_id=f"admin-check-{uuid.uuid4().hex[:12]}",
                user_message=question,
            )

            body = f"""
            <h1 style=\"margin:0 0 16px;font-size:28px;\">Результат проверки ассистента</h1>
            <p style=\"margin:0 0 12px;font-size:16px;\"><strong>Магазин:</strong> {escape(shop.name)} ({escape(shop.shop_id)})</p>
            <div style=\"margin-top:16px;padding:16px;border-radius:12px;background:#f8fafc;border:1px solid #e2e8f0;\">
                <p style=\"margin:0 0 8px;font-weight:600;\">Вопрос</p>
                <div>{escape(question)}</div>
            </div>
            <div style=\"margin-top:16px;padding:16px;border-radius:12px;background:#f0fdf4;border:1px solid #bbf7d0;\">
                <p style=\"margin:0 0 8px;font-weight:600;\">Ответ ассистента</p>
                <div>{escape(answer).replace(chr(10), '<br>')}</div>
            </div>
            <div style=\"margin-top:24px;display:flex;gap:12px;\">
                <a href=\"/admin-action/shop/{shop.shop_id}/assistant-check?question={quote_plus(question)}\" style=\"padding:10px 14px;border-radius:8px;background:#0f766e;color:#fff;text-decoration:none;\">Задать другой вопрос</a>
                <a href=\"/admin/shop/details/{shop.id}\" style=\"padding:10px 14px;border-radius:8px;background:#e8eefc;color:#1d4ed8;text-decoration:none;\">Назад к магазину</a>
            </div>
            """
            return _render_admin_page("Результат проверки ассистента", body)
        finally:
            db.close()

    return admin
