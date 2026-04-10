from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        # TODO: store references to store and llm_fn
        self.store = store 
        self.llm_fn = llm_fn 
        

    def answer(self, question: str, top_k: int = 3) -> str:
        # TODO: retrieve chunks, build prompt, call llm_fn
        retrieved_records = self.store.search(question,top_k)

        content_texts = []
        for i in retrieved_records:
            text_content = i.get("content","")
            content_texts.append(text_content) 
        
        context_string = "\n--\n".join(content_texts)

        promt = (
            "Dựa vào các thông tin dưới đây trả lời cho người dùng\n"
            "Nếu thông tin không có trong tài liệu hãy thành thật trả lời không biết\n\n"
            f"[THÔNG TIN TÀI LIỆU]:\n{context_string}"
            f"[CÂU HỎI]:\n{question}"
            "[TRẢ LỜI]:"
        )
        
        final_answer = self.llm_fn(promt)

        
        return final_answer
