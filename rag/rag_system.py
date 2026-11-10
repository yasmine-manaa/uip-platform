"""
Système RAG (Retrieval-Augmented Generation) pour l'UIP
Gère l'extraction de documents, la vectorisation et la recherche sémantique.
"""

import os
import re
import pickle
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

# Imports pour le traitement de documents
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False


class DocumentProcessor:
    """
    Traite les documents PDF et images pour extraire le texte.
    """

    def __init__(self):
        self.supported_formats = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
        self.temp_dir = Path("temp_documents")
        self.temp_dir.mkdir(exist_ok=True)

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Traite un document et extrait le texte.

        Args:
            file_path: Chemin vers le document

        Returns:
            Dictionnaire avec le texte extrait et les métadonnées
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return {
                "success": False,
                "error": f"Fichier non trouvé: {file_path}",
                "text": "",
                "metadata": {}
            }

        # Déterminer le type de fichier
        file_ext = file_path.suffix.lower()

        if file_ext == ".pdf":
            return self._process_pdf(file_path)
        elif file_ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            return self._process_image(file_path)
        else:
            return self._process_text_file(file_path)

    def _process_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Traite un fichier PDF"""
        result = {
            "success": False,
            "error": None,
            "text": "",
            "metadata": {},
            "pages": []
        }

        try:
            if PYMUPDF_AVAILABLE:
                # Utiliser PyMuPDF pour extraire le texte
                doc = fitz.open(file_path)
                text_parts = []

                for page_num in range(len(doc)):
                    page = doc[page_num]
                    page_text = page.get_text()
                    text_parts.append(page_text)

                    # Extraire les métadonnées de la page
                    page_metadata = {
                        "page_number": page_num + 1,
                        "text_length": len(page_text),
                        "has_images": len(page.get_images()) > 0
                    }
                    result["pages"].append(page_metadata)

                result["text"] = "\n\n".join(text_parts)
                result["metadata"] = {
                    "page_count": len(doc),
                    "file_size": file_path.stat().st_size,
                    "title": doc.metadata.get("title", ""),
                    "author": doc.metadata.get("author", ""),
                    "subject": doc.metadata.get("subject", "")
                }
                doc.close()

            elif OCR_AVAILABLE:
                # Utiliser OCR pour les PDF scannés
                images = convert_from_path(file_path)
                text_parts = []

                for i, image in enumerate(images):
                    # Sauvegarder temporairement l'image
                    temp_path = self.temp_dir / f"temp_page_{i}.png"
                    image.save(temp_path)

                    # OCR
                    text = pytesseract.image_to_string(temp_path, lang='fra+eng')
                    text_parts.append(text)

                    # Nettoyer
                    temp_path.unlink()

                    result["pages"].append({
                        "page_number": i + 1,
                        "text_length": len(text),
                        "ocr_used": True
                    })

                result["text"] = "\n\n".join(text_parts)
                result["metadata"] = {
                    "page_count": len(images),
                    "file_size": file_path.stat().st_size,
                    "ocr_used": True
                }

            else:
                result["error"] = "Aucune bibliothèque PDF disponible"

        except Exception as e:
            result["error"] = f"Erreur lors du traitement PDF: {str(e)}"

        result["success"] = result["text"] != ""
        return result

    def _process_image(self, file_path: Path) -> Dict[str, Any]:
        """Traite une image avec OCR"""
        result = {
            "success": False,
            "error": None,
            "text": "",
            "metadata": {},
            "ocr_used": False
        }

        try:
            if OCR_AVAILABLE:
                # Utiliser Tesseract OCR
                text = pytesseract.image_to_string(file_path, lang='fra+eng')
                result["text"] = text
                result["ocr_used"] = True
                result["metadata"] = {
                    "file_size": file_path.stat().st_size,
                    "ocr_used": True
                }
            else:
                result["error"] = "OCR non disponible"

        except Exception as e:
            result["error"] = f"Erreur lors du traitement image: {str(e)}"

        result["success"] = result["text"] != ""
        return result

    def _process_text_file(self, file_path: Path) -> Dict[str, Any]:
        """Traite un fichier texte ou JSON"""
        result = {
            "success": False,
            "error": None,
            "text": "",
            "metadata": {}
        }

        try:
            # Essayer différents encodages
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            text = None

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        text = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if text:
                # Si c'est un fichier JSON, extraire le contenu
                if file_path.suffix.lower() == '.json':
                    try:
                        import json
                        data = json.loads(text)
                        # Extraire le contenu textuel des champs pertinents
                        content_parts = []
                        for key, value in data.items():
                            if isinstance(value, str):
                                content_parts.append(f"{key}: {value}")
                            elif isinstance(value, (int, float)):
                                content_parts.append(f"{key}: {value}")
                        text = "\n".join(content_parts)
                    except json.JSONDecodeError:
                        # Si ce n'est pas du JSON valide, utiliser le texte brut
                        pass

                result["text"] = text
                result["metadata"] = {
                    "file_size": file_path.stat().st_size,
                    "encoding": encoding,
                    "file_type": file_path.suffix.lower()
                }
                result["success"] = True
            else:
                result["error"] = "Impossible de lire le fichier avec les encodages supportés"

        except Exception as e:
            result["error"] = f"Erreur lors du traitement fichier texte: {str(e)}"

        return result


class VectorStore:
    """
    Stocke et recherche des vecteurs d'embeddings pour la recherche sémantique.
    Utilise TF-IDF pour la vectorisation.
    """

    def __init__(self):
        self.vectorizer = None
        self.vectors = None
        self.documents = None
        self.texts = None
        self.metadata = None
        self.index_path = Path("vector_store")
        self.index_path.mkdir(exist_ok=True)

        # Initialiser le vectorizer TF-IDF
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(
                max_features=10000,
                ngram_range=(1, 2),
                stop_words='french' if JIEBA_AVAILABLE else None,
                lowercase=True
            )

    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Génère les embeddings TF-IDF pour une liste de textes"""
        if self.vectorizer is None:
            return np.zeros((len(texts), 100))

        try:
            # Ajuster le vectorizer si c'est la première fois
            if self.vectors is None:
                return self.vectorizer.fit_transform(texts).toarray()
            else:
                return self.vectorizer.transform(texts).toarray()
        except Exception as e:
            print(f"Erreur lors de la vectorisation: {e}")
            return np.zeros((len(texts), 100))

    def add_documents(self, documents: List[Dict[str, Any]], texts: List[str],
                     metadatas: List[Dict[str, Any]] = None) -> bool:
        """
        Ajoute des documents à la base vectorielle.

        Args:
            documents: Liste des documents
            texts: Liste des textes extraits
            metadatas: Liste des métadonnées (optionnel)

        Returns:
            True si succès
        """
        try:
            # Générer les embeddings TF-IDF
            embeddings = self._get_embeddings(texts)

            # Stocker les données
            if self.vectors is None:
                self.vectors = embeddings
            else:
                # Ajouter les nouveaux vecteurs
                self.vectors = np.vstack([self.vectors, embeddings])

            self.documents = (self.documents or []) + documents
            self.texts = (self.texts or []) + texts
            self.metadata = (self.metadata or []) + (metadatas or [{} for _ in documents])

            # Sauvegarder l'index
            self._save_index()

            return True

        except Exception as e:
            print(f"Erreur lors de l'ajout des documents: {e}")
            return False

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche les documents les plus similaires à une requête.

        Args:
            query: Requête de recherche
            top_k: Nombre de résultats à retourner

        Returns:
            Liste des documents les plus similaires
        """
        try:
            if self.vectors is None or len(self.vectors) == 0:
                return []

            # Générer l'embedding de la requête
            query_embedding = self._get_embeddings([query])[0]

            # Calculer les similarités cosinus
            similarities = cosine_similarity([query_embedding], self.vectors)[0]

            # Obtenir les indices des top_k plus similaires
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            # Construire les résultats
            results = []
            for idx in top_indices:
                results.append({
                    "document": self.documents[idx],
                    "text": self.texts[idx],
                    "metadata": self.metadata[idx] if self.metadata else {},
                    "similarity": float(similarities[idx]),
                    "rank": len(results) + 1
                })

            return results

        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return []

    def _save_index(self):
        """Sauvegarde l'index vectoriel"""
        try:
            index_file = self.index_path / "vector_index.pkl"
            with open(index_file, 'wb') as f:
                pickle.dump({
                    "vectors": self.vectors,
                    "documents": self.documents,
                    "texts": self.texts,
                    "metadata": self.metadata,
                    "vectorizer": self.vectorizer
                }, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de l'index: {e}")

    def _load_index(self):
        """Charge l'index vectoriel"""
        try:
            index_file = self.index_path / "vector_index.pkl"
            if index_file.exists():
                with open(index_file, 'rb') as f:
                    data = pickle.load(f)
                    self.vectors = data.get("vectors")
                    self.documents = data.get("documents")
                    self.texts = data.get("texts")
                    self.metadata = data.get("metadata")
                    self.vectorizer = data.get("vectorizer")
                    return True
        except Exception as e:
            print(f"Erreur lors du chargement de l'index: {e}")
        return False


class KnowledgeBase:
    """
    Base de connaissances documentaire pour l'UIP.
    """

    def __init__(self, kb_path: str = "knowledge_base"):
        self.kb_path = Path(kb_path)
        self.kb_path.mkdir(exist_ok=True)

        self.documents_path = self.kb_path / "documents"
        self.documents_path.mkdir(exist_ok=True)

        self.vector_store = VectorStore()
        self.document_processor = DocumentProcessor()

        # Charger la base de connaissances existante
        self._load_knowledge_base()

    def add_document(self, file_path: str, doc_type: str = "general",
                    tags: List[str] = None) -> Dict[str, Any]:
        """
        Ajoute un document à la base de connaissances.

        Args:
            file_path: Chemin vers le document
            doc_type: Type de document
            tags: Tags pour le document

        Returns:
            Résultat de l'ajout
        """
        # Traiter le document
        processed = self.document_processor.process_document(file_path)

        if not processed["success"]:
            return {
                "success": False,
                "error": processed["error"],
                "document": None
            }

        # Créer l'entrée de document
        doc_id = hashlib.md5(f"{file_path}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]

        document_entry = {
            "id": doc_id,
            "file_path": str(file_path),
            "doc_type": doc_type,
            "tags": tags or [],
            "processed_at": datetime.now().isoformat(),
            "metadata": processed["metadata"],
            "text_length": len(processed["text"])
        }

        # Sauvegarder le document
        doc_file = self.documents_path / f"{doc_id}.json"
        with open(doc_file, 'w', encoding='utf-8') as f:
            json.dump(document_entry, f, indent=2, ensure_ascii=False)

        # Ajouter au vector store
        self.vector_store.add_documents(
            [document_entry],
            [processed["text"]],
            [{"doc_id": doc_id, "doc_type": doc_type, "tags": tags}]
        )

        return {
            "success": True,
            "document": document_entry,
            "text_preview": processed["text"][:200] + "..." if len(processed["text"]) > 200 else processed["text"]
        }

    def search(self, query: str, top_k: int = 5,
               doc_type: str = None) -> List[Dict[str, Any]]:
        """
        Recherche dans la base de connaissances.

        Args:
            query: Requête de recherche
            top_k: Nombre de résultats
            doc_type: Filtrer par type de document

        Returns:
            Liste des documents trouvés
        """
        results = self.vector_store.search(query, top_k)

        # Filtrer par type si spécifié
        if doc_type:
            results = [r for r in results if r["metadata"].get("doc_type") == doc_type]

        return results

    def _load_knowledge_base(self):
        """Charge la base de connaissances existante"""
        try:
            # Charger tous les documents
            documents = []
            texts = []
            metadatas = []

            for doc_file in self.documents_path.glob("*.json"):
                with open(doc_file, 'r', encoding='utf-8') as f:
                    doc = json.load(f)
                    documents.append(doc)

                    # Charger le texte du document
                    text = self._get_document_text(doc)
                    texts.append(text)
                    metadatas.append({
                        "doc_id": doc["id"],
                        "doc_type": doc.get("doc_type", "general"),
                        "tags": doc.get("tags", [])
                    })

            if documents:
                self.vector_store.add_documents(documents, texts, metadatas)

        except Exception as e:
            print(f"Erreur lors du chargement de la base de connaissances: {e}")

    def _get_document_text(self, doc: Dict[str, Any]) -> str:
        """Récupère le texte d'un document"""
        # Pour l'instant, retourner un texte vide
        # Dans une implémentation complète, cela chargerait le texte depuis le fichier original
        return f"Document {doc.get('id', 'unknown')} - {doc.get('doc_type', 'general')}"

    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de la base de connaissances"""
        doc_count = len(list(self.documents_path.glob("*.json")))

        return {
            "total_documents": doc_count,
            "kb_path": str(self.kb_path),
            "vector_store_size": len(self.vector_store.vectors) if self.vector_store.vectors is not None else 0
        }


# Import json pour la sérialisation
import json


class RAGSystem:
    """
    Système RAG complet pour l'UIP.
    """

    def __init__(self):
        self.knowledge_base = KnowledgeBase()
        self.document_processor = DocumentProcessor()

    def process_and_index_document(self, file_path: str, doc_type: str = "general",
                                  tags: List[str] = None) -> Dict[str, Any]:
        """
        Traite et indexe un document dans la base de connaissances.

        Args:
            file_path: Chemin vers le document
            doc_type: Type de document
            tags: Tags pour le document

        Returns:
            Résultat du traitement
        """
        return self.knowledge_base.add_document(file_path, doc_type, tags)

    def answer_question(self, question: str, context: Dict[str, Any] = None,
                       top_k: int = 5) -> Dict[str, Any]:
        """
        Répond à une question en utilisant la base de connaissances.

        Args:
            question: Question à répondre
            context: Contexte additionnel
            top_k: Nombre de documents à considérer

        Returns:
            Réponse avec les sources
        """
        # Rechercher les documents pertinents
        search_results = self.knowledge_base.search(question, top_k)

        # Construire le contexte
        context_texts = []
        sources = []

        for result in search_results:
            context_texts.append(result["text"])
            sources.append({
                "document_id": result["metadata"].get("doc_id"),
                "similarity": result["similarity"],
                "doc_type": result["metadata"].get("doc_type")
            })

        # Pour l'instant, retourner une réponse simple
        # Dans une implémentation complète, cela utiliserait un LLM
        answer = self._generate_answer(question, context_texts, context)

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "confidence": self._calculate_confidence(search_results),
            "timestamp": datetime.now().isoformat()
        }

    def _generate_answer(self, question: str, context_texts: List[str],
                        context: Dict[str, Any] = None) -> str:
        """
        Génère une réponse basée sur le contexte.
        Pour l'instant, retourne une réponse template.
        """
        if not context_texts:
            return "Je n'ai pas trouvé d'informations pertinentes dans la base de connaissances."

        # Réponse simple basée sur les documents trouvés
        answer = f"Basé sur {len(context_texts)} document(s) pertinent(s), voici ce que j'ai trouvé:\n\n"

        for i, text in enumerate(context_texts[:3], 1):
            # Extraire un extrait pertinent
            excerpt = text[:200] + "..." if len(text) > 200 else text
            answer += f"{i}. {excerpt}\n\n"

        answer += "Pour une réponse plus détaillée, veuillez consulter les documents sources."

        return answer

    def _calculate_confidence(self, search_results: List[Dict[str, Any]]) -> float:
        """Calcule le score de confiance basé sur les similarités"""
        if not search_results:
            return 0.0

        # Utiliser la similarité moyenne des top résultats
        similarities = [r["similarity"] for r in search_results[:3]]
        return sum(similarities) / len(similarities) if similarities else 0.0

    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du système RAG"""
        return {
            "knowledge_base": self.knowledge_base.get_statistics(),
            "document_processor": {
                "supported_formats": self.document_processor.supported_formats,
                "pymupdf_available": PYMUPDF_AVAILABLE,
                "ocr_available": OCR_AVAILABLE,
                "sklearn_available": SKLEARN_AVAILABLE,
                "jieba_available": JIEBA_AVAILABLE
            }
        }


# Instance globale du système RAG
rag_system = RAGSystem()
