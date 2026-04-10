from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        
        import re
        raw_sentences = re.split(r'(?<=[.!?])\s+', text)
        clean_sentences = [s.strip() for s in raw_sentences if s.strip()]
        
        chunks = []
        for i in range(0, len(clean_sentences), self.max_sentences_per_chunk):
            batch = clean_sentences[i : i + self.max_sentences_per_chunk]
            chunks.append(" ".join(batch)) # Đảm bảo trả về chuỗi (string)
            
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    # TODO: implement cosine similarity formula
    dot_product = _dot(vec_a,vec_b) 
    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0 
    return dot_product / (mag_a * mag_b)




class RecursiveChunker:
    """
    Recursively split text using separators in priority order.
    """
    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]

        sep = ""
        next_seps = []
        for i, s in enumerate(remaining_separators):
            if s == "":
                sep = s
                break
            if s in current_text:
                sep = s
                next_seps = remaining_separators[i + 1:]
                break

        if sep == "":
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        splits = current_text.split(sep)
        chunks = []
        current_chunk = ""

        for part in splits:
            if len(part) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                chunks.extend(self._split(part, next_seps))
            else:
                new_chunk = current_chunk + sep + part if current_chunk else part
                if len(new_chunk) <= self.chunk_size:
                    current_chunk = new_chunk
                else:
                    chunks.append(current_chunk)
                    current_chunk = part

        if current_chunk:
            chunks.append(current_chunk)

        return chunks


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""
    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed_chunker = FixedSizeChunker(chunk_size=chunk_size)
        sentence_chunker = SentenceChunker()
        recursive_chunker = RecursiveChunker(chunk_size=chunk_size)

        def get_stats(chunks: list[str]) -> dict:
            if not chunks:
                return {"count": 0, "avg_length": 0.0, "chunks": []}
            
            total_length = sum(len(c) for c in chunks)
            return {
                "count": len(chunks),
                "avg_length": round(total_length / len(chunks), 2),
                "chunks": chunks  # Đã thêm danh sách dữ liệu gốc vào đây để pass bài test
            }

        return {
            "fixed_size": get_stats(fixed_chunker.chunk(text)),
            "by_sentences": get_stats(sentence_chunker.chunk(text)),
            "recursive": get_stats(recursive_chunker.chunk(text))
        }