import logging
import asyncio
from typing import Dict, List

import chromadb
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_EMBED_BATCH_SIZE = 96
MAX_DOCUMENT_LENGTH = 4000
MAX_EMBED_RETRIES = 3


class ProductIndexer:
    """
    Индексирует товары в ChromaDB для поиска по RAG
    """

    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    @staticmethod
    def _to_document(product: Dict) -> str:
        name = product.get("name") or ""
        description = product.get("description") or ""
        vendor = product.get("vendor") or ""
        category = product.get("category") or ""
        price = product.get("price")
        currency = product.get("currency") or "RUB"
        price_text = f"{price} {currency}" if price is not None else ""
        document = " | ".join([part for part in [name, vendor, description, category, price_text] if part])
        return document[:MAX_DOCUMENT_LENGTH]

    async def _embed_texts(self, texts: List[str], input_type: str) -> List[List[float]]:
        if not settings.COHERE_API_KEY:
            raise RuntimeError("COHERE_API_KEY is not configured")

        payload = {
            "model": settings.COHERE_EMBED_MODEL,
            "texts": texts,
            "input_type": input_type,
        }
        headers = {
            "Authorization": f"Bearer {settings.COHERE_API_KEY}",
            "Content-Type": "application/json",
        }

        timeout = httpx.Timeout(30.0)
        last_error: Exception | None = None
        for attempt in range(MAX_EMBED_RETRIES):
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post("https://api.cohere.ai/v1/embed", headers=headers, json=payload)
            if response.status_code != 429:
                response.raise_for_status()
                data = response.json()
                break

            last_error = RuntimeError(f"Cohere rate limited embeddings request: {response.text}")
            if attempt == MAX_EMBED_RETRIES - 1:
                raise last_error
            await asyncio.sleep(2 ** attempt)
        else:
            raise last_error or RuntimeError("Unknown embedding error")

        embeddings = data.get("embeddings", [])
        if not embeddings:
            raise RuntimeError("Cohere returned no embeddings")
        return embeddings

    async def clear_shop(self, shop_id: str) -> None:
        self.collection.delete(where={"shop_id": shop_id})

    async def index_products(self, shop_id: str, products: List[Dict], replace_existing: bool = False):
        """
        Индексировать товары магазина
        """
        logger.info(f"Indexing {len(products)} products for shop {shop_id}")

        if replace_existing:
            await self.clear_shop(shop_id)

        if not products:
            return

        ids = []
        documents = []
        metadatas = []

        for idx, product in enumerate(products):
            external_id = product.get("external_id") or f"item_{idx + 1}"
            vector_id = f"{shop_id}:{external_id}"
            doc = self._to_document(product)

            metadata = {
                "shop_id": shop_id,
                "external_id": external_id,
                "name": product.get("name") or "",
                "description": product.get("description") or "",
                "vendor": product.get("vendor") or "",
                "category": product.get("category") or "",
                "currency": product.get("currency") or "RUB",
                "url": product.get("url") or "",
            }
            price = product.get("price")
            if price is not None:
                metadata["price"] = float(price)

            ids.append(vector_id)
            documents.append(doc)
            metadatas.append(metadata)

        embeddings: List[List[float]] = []
        batch_ranges = list(range(0, len(documents), MAX_EMBED_BATCH_SIZE))
        for batch_idx, start in enumerate(batch_ranges):
            batch = documents[start:start + MAX_EMBED_BATCH_SIZE]
            if batch_idx > 0:
                logger.info(f"Waiting 65s before next embedding batch ({batch_idx + 1}/{len(batch_ranges)}) to avoid rate limit...")
                await asyncio.sleep(65)
            embeddings.extend(await self._embed_texts(batch, input_type="search_document"))

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    async def search(self, query: str, shop_id: str, limit: int = 5) -> List[Dict]:
        """
        Найти релевантные товары по запросу
        """
        logger.info("Semantic search for shop %s: %s", shop_id, query)

        query_embeddings = await self._embed_texts([query], input_type="search_query")
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=limit,
            where={"shop_id": shop_id},
            include=["metadatas", "distances"],
        )

        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]

        output: List[Dict] = []
        for meta, dist in zip(metadatas, distances):
            output.append(
                {
                    "name": meta.get("name") or "",
                    "description": meta.get("description") or "",
                    "vendor": meta.get("vendor") or "",
                    "price": meta.get("price"),
                    "currency": meta.get("currency") or "RUB",
                    "category": meta.get("category") or "",
                    "url": meta.get("url") or "",
                    "external_id": meta.get("external_id") or "",
                    "score": 1.0 - float(dist),
                }
            )

        return output
