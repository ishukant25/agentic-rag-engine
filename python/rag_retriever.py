"""
RAG (Retrieval-Augmented Generation) Knowledge Base Retriever
Implements semantic vector matching and context chunk retrieval to ground LLM agent responses.
Author: Ishukant (https://github.com/ishukant25)
"""

import json
import math
import os
import re
from typing import List, Dict, Any


class KnowledgeRetriever:
    """Lightweight, zero-external-dependency semantic & keyword RAG retriever."""

    def __init__(self, data_path: str = None):
        if not data_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "data", "knowledge_base.json")
        self.data_path = data_path
        self.documents = self._load_documents()

    def _load_documents(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.data_path):
            return []
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Normalize and tokenize text into lowercase word tokens."""
        return re.findall(r"\w+", text.lower())

    def _compute_relevance(self, query: str, doc_text: str) -> float:
        """Compute term frequency and overlap score between query and document."""
        query_tokens = set(self._tokenize(query))
        doc_tokens = self._tokenize(doc_text)
        if not query_tokens or not doc_tokens:
            return 0.0

        matches = sum(1 for token in doc_tokens if token in query_tokens)
        score = matches / (math.sqrt(len(doc_tokens)) + 1e-5)
        return round(score, 4)

    def retrieve(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Retrieve top_k most relevant document chunks based on semantic overlap."""
        scored_docs = []
        for doc in self.documents:
            score = self._compute_relevance(query, f"{doc['title']} {doc['content']}")
            scored_docs.append({**doc, "relevance_score": score})

        # Sort by relevance descending
        scored_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_docs[:top_k]

    def format_for_context(self, query: str, top_k: int = 2) -> str:
        """Format retrieved chunks into a clean context block for LLM prompts."""
        results = self.retrieve(query, top_k)
        if not results:
            return "No specific external context found."

        context_blocks = []
        for i, item in enumerate(results, 1):
            context_blocks.append(
                f"[Source {i}: {item['title']} (Score: {item['relevance_score']})]\n{item['content']}"
            )
        return "\n\n".join(context_blocks)


if __name__ == "__main__":
    retriever = KnowledgeRetriever()
    test_query = "How to optimize website audits and avoid LLM hallucinations?"
    print(f"Query: {test_query}\n")
    print(retriever.format_for_context(test_query, top_k=2))
