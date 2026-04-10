from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # Khởi tạo ChromaDB Client (chạy trên RAM, tự động xóa khi tắt chương trình)
            client = chromadb.EphemeralClient()
            self._collection = client.get_or_create_collection(name=self._collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None
    
    def _make_record(self, doc: Document) -> dict[str, Any]:
        embedding = self._embedding_fn(doc.content)
        
        # Bắt buộc chèn doc_id vào metadata để hàm Delete có thể nhận diện và xóa
        meta = doc.metadata or {}
        meta["doc_id"] = doc.id  
        
        return {
            "id": doc.id,
            "content": doc.content, # Đổi từ 'text' thành 'content' theo đúng yêu cầu test
            "embedding": embedding,
            "metadata": meta
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records:
            return []

        query_embedding = self._embedding_fn(query)
        scored_records = []

        for record in records:
            score = _dot(query_embedding, record["embedding"])
            # Tạo bản sao và nhét thêm điểm 'score' vào để test không báo lỗi KeyError
            result_record = record.copy()
            result_record["score"] = score
            scored_records.append(result_record)

        scored_records.sort(key=lambda x: x["score"], reverse=True)
        return scored_records[:top_k]
 

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]

        if self._use_chroma:
            ids = [r["id"] for r in records]
            documents = [r["text"] for r in records]
            embeddings = [r["embedding"] for r in records]
            metadatas = [r["metadata"] for r in records]
            
            self._collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
        else:
            self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma:
            query_embedding = self._embedding_fn(query)
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            parsed_results = []
            # Bóc tách dữ liệu Chroma trả về (nằm trong các list lồng nhau)
            if results and results.get("ids") and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    parsed_results.append({
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
                    })
            return parsed_results
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        metadata_filter = metadata_filter or {}

        if self._use_chroma:
            query_embedding = self._embedding_fn(query)
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=metadata_filter
            )
            
            parsed_results = []
            if results and results.get("ids") and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    parsed_results.append({
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
                    })
            return parsed_results
        else:
            # Lọc thủ công trên RAM
            filtered_records = []
            for record in self._store:
                match = True
                for key, value in metadata_filter.items():
                    if record.get("metadata", {}).get(key) != value:
                        match = False
                        break
                if match:
                    filtered_records.append(record)
                    
            return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma:
            initial_count = self._collection.count()
            self._collection.delete(where={"doc_id": doc_id})
            return self._collection.count() < initial_count
        else:
            initial_len = len(self._store)
            # Giữ lại những chunk KHÔNG thuộc về doc_id cần xóa
            self._store = [r for r in self._store if r.get("metadata", {}).get("doc_id") != doc_id]
            return len(self._store) < initial_len