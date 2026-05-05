"""
Сервис синхронизации каталога из внешнего фида (Яндекс.Маркет XML/YML и JSON).

Поддерживаемые форматы:
  1. YML/XML (yml_catalog → shop → offers/offer)
  2. JSON: {"shop": {"offers": [...], "categories": [...]}}
  3. JSON: {"offers": [...]}
  4. JSON: плоский список []
"""

import logging
import xml.etree.ElementTree as ET
import requests
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.models.shop import Shop
from app.models.product import Product
from app.rag.indexer import ProductIndexer

logger = logging.getLogger(__name__)


@dataclass
class CatalogSyncResult:
    synced_count: int
    indexed_successfully: bool
    index_error: str | None = None


def _extract_offers(data: Any) -> List[Dict]:
    """Извлекаем список офферов из любой поддерживаемой структуры фида."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # {"shop": {"offers": [...]}}
        shop_node = data.get("shop", {})
        if shop_node and "offers" in shop_node:
            return shop_node.get("offers", [])
        # {"offers": [...]}
        if "offers" in data:
            return data.get("offers", [])
        # {"items": [...]}
        if "items" in data:
            return data.get("items", [])
        # {"products": [...]}
        if "products" in data:
            return data.get("products", [])
    return []


def _extract_categories(data: Any) -> Dict[str, str]:
    """Строим словарь {id: name} для категорий."""
    cats: Dict[str, str] = {}
    if not isinstance(data, dict):
        return cats
    shop_node = data.get("shop", data)
    for cat in shop_node.get("categories", []):
        if isinstance(cat, dict):
            cat_id = str(cat.get("id", ""))
            cat_name = cat.get("name", "")
            if cat_id:
                cats[cat_id] = cat_name
    return cats


def _parse_offer(offer: Dict, categories: Dict[str, str]) -> Optional[Dict]:
    """Нормализуем один оффер в наш формат."""
    if not isinstance(offer, dict):
        return None

    # external_id
    external_id = str(
        offer.get("id")
        or offer.get("external_id")
        or offer.get("vendorCode")
        or offer.get("article")
        or offer.get("sku")
        or ""
    )

    # name
    name = (
        offer.get("name")
        or offer.get("title")
        or offer.get("model")
        or ""
    ).strip()
    if not name:
        return None  # товар без названия бесполезен

    # price
    price_raw = offer.get("price") or offer.get("oldprice") or offer.get("cost")
    try:
        price = float(price_raw) if price_raw is not None else None
    except (ValueError, TypeError):
        price = None

    # currency
    currency = offer.get("currencyId") or offer.get("currency") or "RUB"

    # url
    url = offer.get("url") or offer.get("link") or None

    # image
    pictures = offer.get("picture") or offer.get("pictures") or offer.get("image") or offer.get("image_url")
    if isinstance(pictures, list):
        image_url = pictures[0] if pictures else None
    else:
        image_url = pictures or None

    # description
    description = offer.get("description") or offer.get("body") or None
    # Добавляем vendor/brand к описанию если есть
    vendor = offer.get("vendor") or offer.get("brand") or None
    if vendor and description:
        description = f"{vendor}. {description}"
    elif vendor:
        description = str(vendor)

    # category
    category_id = str(offer.get("categoryId") or offer.get("category_id") or "")
    category = categories.get(category_id) or offer.get("category") or offer.get("categoryName") or None

    return {
        "external_id": external_id or name[:50],
        "name": name,
        "description": description,
        "vendor": vendor,
        "price": price,
        "currency": currency,
        "url": url,
        "image_url": image_url,
        "category": category,
    }


def _parse_yml_xml(content: bytes) -> List[Dict]:
    """Парсим Яндекс.Маркет YML/XML фид."""
    root = ET.fromstring(content)
    shop_el = root.find("shop")
    if shop_el is None:
        shop_el = root  # на случай если root уже shop

    # Категории
    categories: Dict[str, str] = {}
    for cat in shop_el.findall(".//categories/category"):
        cat_id = cat.get("id", "")
        cat_name = (cat.text or "").strip()
        if cat_id:
            categories[cat_id] = cat_name

    # Офферы
    products = []
    for offer in shop_el.findall(".//offers/offer"):
        offer_id = offer.get("id", "")

        def _text(tag: str) -> Optional[str]:
            el = offer.find(tag)
            return (el.text or "").strip() if el is not None and el.text else None

        name = _text("name")
        if not name:
            continue

        price_raw = _text("price")
        try:
            price = float(price_raw) if price_raw else None
        except ValueError:
            price = None

        currency = _text("currencyId") or "RUB"
        url = _text("url")
        image_url = _text("picture")
        description = _text("description")
        vendor = _text("vendor")
        if vendor and description:
            description = f"{vendor}. {description}"
        elif vendor:
            description = vendor

        category_id = _text("categoryId") or ""
        category = categories.get(category_id) or _text("category")

        # Параметры (вкус, вес и т.п.) добавляем к описанию
        params = []
        for param_el in offer.findall("param"):
            pname = param_el.get("name", "")
            pval = (param_el.text or "").strip()
            if pname and pval:
                params.append(f"{pname}: {pval}")
        if params:
            params_str = "; ".join(params)
            description = f"{description}. {params_str}" if description else params_str

        products.append({
            "external_id": offer_id or name[:50],
            "name": name,
            "description": description,
            "vendor": vendor,
            "price": price,
            "currency": currency,
            "url": url,
            "image_url": image_url,
            "category": category,
        })

    return products


def fetch_and_parse_feed(feed_url: str) -> List[Dict]:
    """Скачиваем фид и возвращаем список нормализованных товаров."""
    try:
        resp = requests.get(feed_url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Ошибка при загрузке фида: {e}")

    # Определяем формат: XML или JSON
    content_type = resp.headers.get("Content-Type", "")
    body = resp.content
    is_xml = (
        "xml" in content_type
        or body.lstrip()[:5] in (b"<?xml", b"<yml_", b"<shop")
        or body.lstrip()[:1] == b"<"
    )

    if is_xml:
        try:
            return _parse_yml_xml(body)
        except ET.ParseError as e:
            raise RuntimeError(f"Ошибка парсинга XML фида: {e}")
    else:
        try:
            data = resp.json()
        except ValueError as e:
            raise RuntimeError(f"Фид не является валидным JSON или XML: {e}")

        categories = _extract_categories(data)
        raw_offers = _extract_offers(data)
        products = []
        for offer in raw_offers:
            parsed = _parse_offer(offer, categories)
            if parsed:
                products.append(parsed)
        return products


async def sync_shop_catalog(shop: Shop, db: Session) -> CatalogSyncResult:
    """
    Скачивает фид из shop.catalog_url, обновляет товары в БД и переиндексирует Chroma.
    Возвращает количество загруженных товаров.
    """
    if not shop.catalog_url:
        raise ValueError("У магазина не задан catalog_url")

    products = fetch_and_parse_feed(shop.catalog_url)
    if not products:
        raise ValueError("Фид не содержит товаров или не удалось распознать формат")

    # Удаляем старые товары
    db.query(Product).filter(Product.shop_id == shop.shop_id).delete()

    # Сохраняем новые
    for p in products:
        db.add(Product(
            shop_id=shop.shop_id,
            external_id=p["external_id"],
            name=p["name"],
            description=p.get("description"),
            vendor=p.get("vendor"),
            price=p.get("price"),
            currency=p.get("currency", "RUB"),
            category=p.get("category"),
            url=p.get("url"),
            image_url=p.get("image_url"),
        ))

    sync_finished_at = datetime.utcnow()
    shop.last_indexed = sync_finished_at
    shop.last_catalog_synced_at = sync_finished_at
    db.commit()

    # Переиндексируем в Chroma
    indexer = ProductIndexer()
    indexed_successfully = True
    index_error = None
    try:
        await indexer.index_products(shop.shop_id, products, replace_existing=True)
        shop.last_catalog_indexed_at = datetime.utcnow()
        db.commit()
    except Exception as exc:
        indexed_successfully = False
        index_error = str(exc)
        logger.exception("Не удалось переиндексировать каталог магазина %s", shop.shop_id)

    logger.info("Синхронизация магазина %s: %d товаров", shop.shop_id, len(products))
    return CatalogSyncResult(
        synced_count=len(products),
        indexed_successfully=indexed_successfully,
        index_error=index_error,
    )
