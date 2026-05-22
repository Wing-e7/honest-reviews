# chat/store.py
import chromadb


class ChromaStore:
    def __init__(self, persist_dir: str = "./chroma_db", collection_prefix: str = "hr"):
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._prefix = collection_prefix

    def _collection_name(self, product: str) -> str:
        return f"{self._prefix}_{product}_evidence"

    def upsert_chunks(
        self,
        product: str,
        chunks: list[str],
        metadatas: list[dict],
    ) -> None:
        col = self._client.get_or_create_collection(self._collection_name(product))
        ids = [f"{product}_{i}_{hash(c) & 0xFFFFFF}" for i, c in enumerate(chunks)]
        col.upsert(documents=chunks, metadatas=metadatas, ids=ids)

    def query_chunks(
        self,
        product: str,
        query: str,
        top_k: int = 3,
    ) -> list[dict]:
        try:
            col = self._client.get_collection(self._collection_name(product))
        except Exception:
            return []
        results = col.query(query_texts=[query], n_results=min(top_k, col.count()))
        if not results["documents"] or not results["documents"][0]:
            return []
        return [
            {"text": doc, **meta}
            for doc, meta in zip(results["documents"][0], results["metadatas"][0])
        ]
