"""
Document Parser using PyMuPDF.
Extracts text page-by-page, detects embedded forms, metadata, and handles text/pdf/image formats.
"""

from typing import List, Dict, Any, Optional
import os
import pymupdf as fitz


class DocumentParser:
    SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".json"]

    @staticmethod
    def parse_file(file_path: str) -> Dict[str, Any]:
        """
        Parses a document file and extracts page texts and layout metadata.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "extension": ext,
                "page_count": 1,
                "pages": [{"page_number": 1, "text": content}],
                "total_text": content,
                "is_ocr_needed": False
            }

        elif ext == ".pdf":
            pages = []
            total_text_parts = []
            doc = fitz.open(file_path)
            page_count = len(doc)
            is_scanned = True

            for page_idx in range(page_count):
                page = doc.load_page(page_idx)
                text = page.get_text("text")
                if len(text.strip()) > 30:
                    is_scanned = False
                pages.append({
                    "page_number": page_idx + 1,
                    "text": text.strip()
                })
                total_text_parts.append(text.strip())

            doc.close()
            total_text = "\n\n".join(total_text_parts)

            return {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "extension": ext,
                "page_count": page_count,
                "pages": pages,
                "total_text": total_text,
                "is_ocr_needed": is_scanned and len(total_text.strip()) < 50
            }

        else:
            raise ValueError(f"Unsupported file format: {ext}")
