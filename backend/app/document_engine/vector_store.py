"""
Vector Store and Semantic Retrieval Engine for Insurance Policies and Case Documents.
Implements hybrid retrieval (TF-IDF vector space + keyword matching) with strict citation tracing.
Section 5.2 & 7.2: Any generated finding must cite document, page, and article.
"""

from typing import List, Dict, Any, Optional
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.document_engine.corpus.policy_corpus import POLICY_CORPUS


class DocumentChunk:
    def __init__(
        self,
        chunk_id: str,
        doc_id: str,
        doc_title: str,
        page: int,
        article: str,
        category: str,
        content: str,
        tags: List[str]
    ):
        self.chunk_id = chunk_id
        self.doc_id = doc_id
        self.doc_title = doc_title
        self.page = page
        self.article = article
        self.category = category
        self.content = content
        self.tags = tags

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "doc_title": self.doc_title,
            "page": self.page,
            "article": self.article,
            "category": self.category,
            "content": self.content,
            "tags": self.tags
        }


class PolicyVectorStore:
    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self._load_reference_corpus()

    def _load_reference_corpus(self):
        """
        Loads and indexes reference policy corpus.
        """
        self.chunks = []
        for idx, item in enumerate(POLICY_CORPUS):
            chunk = DocumentChunk(
                chunk_id=f"ref_{idx}",
                doc_id=item["doc_id"],
                doc_title=item["doc_title"],
                page=item["page"],
                article=item["article"],
                category=item["category"],
                content=item["content"],
                tags=item.get("tags", [])
            )
            self.chunks.append(chunk)
        self._reindex()

    def add_custom_document(
        self,
        doc_id: str,
        doc_title: str,
        page_texts: List[str],
        category: str = "Pièce Dossier"
    ):
        """
        Indexes pages of an uploaded case document.
        """
        for page_num, text in enumerate(page_texts, start=1):
            if not text.strip():
                continue
            # Simple paragraph chunking
            paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
            if not paragraphs:
                paragraphs = [text.strip()]
            for p_idx, p_content in enumerate(paragraphs):
                chunk = DocumentChunk(
                    chunk_id=f"{doc_id}_p{page_num}_{p_idx}",
                    doc_id=doc_id,
                    doc_title=doc_title,
                    page=page_num,
                    article=f"Page {page_num} - Extrait {p_idx+1}",
                    category=category,
                    content=p_content,
                    tags=[]
                )
                self.chunks.append(chunk)
        self._reindex()

    def _reindex(self):
        """
        Fits TF-IDF vectorizer over all corpus chunks.
        """
        if not self.chunks:
            return
        corpus_texts = [f"{c.doc_title} {c.article} {c.category} {c.content} {' '.join(c.tags)}" for c in self.chunks]
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words=["le", "la", "les", "du", "de", "des", "en", "un", "une", "et", "ou", "a", "dans", "par", "pour"]
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus_texts)

    def search(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.08
    ) -> List[Dict[str, Any]]:
        """
        Hybrid semantic search returning verifiable citations with doc_id, page, article, snippet, and score.
        """
        if not self.chunks or self.vectorizer is None or self.tfidf_matrix is None:
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        ranked_indices = np.argsort(scores)[::-1]
        results: List[Dict[str, Any]] = []

        for idx in ranked_indices[:top_k]:
            score = float(scores[idx])
            if score >= threshold:
                chunk = self.chunks[idx]
                results.append({
                    "citation_id": f"CIT-{chunk.doc_id}-P{chunk.page}",
                    "doc_id": chunk.doc_id,
                    "doc_title": chunk.doc_title,
                    "page": chunk.page,
                    "article": chunk.article,
                    "category": chunk.category,
                    "content_snippet": chunk.content,
                    "relevance_score": round(score, 3)
                })

        return results


# Global singleton instance
policy_vector_store = PolicyVectorStore()
