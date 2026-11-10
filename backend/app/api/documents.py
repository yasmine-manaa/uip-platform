"""
API Endpoints: Document Intelligence (F02, F03, F05).
Document upload, native PDF parsing, classification, field extraction with confidence, and RAG indexing.
"""

from typing import List, Optional
import os
import uuid
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case import Case, Document, AuditEvent
from app.document_engine.parser import DocumentParser
from app.document_engine.classifier import DocumentClassifier
from app.document_engine.extractor import FieldExtractor
from app.document_engine.vector_store import policy_vector_store

router = APIRouter(prefix="/cases/{case_id}/documents", tags=["Document Intelligence"])

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("")
async def upload_document(
    case_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Uploads a document (PDF, TXT), extracts text, classifies document type,
    extracts underwriting fields with confidence, indexes into vector store, and logs audit event.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    doc_id = f"DOC-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    filename = file.filename or "unknown_file.txt"
    dest_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{filename}")

    # Save original file
    content_bytes = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content_bytes)

    # 1. Parse document text
    try:
        parsed = DocumentParser.parse_file(dest_path)
    except Exception as e:
        # Fallback to plain text decode
        raw_text = content_bytes.decode("utf-8", errors="ignore")
        parsed = {
            "page_count": 1,
            "pages": [{"page_number": 1, "text": raw_text}],
            "total_text": raw_text,
            "is_ocr_needed": False
        }

    total_text = parsed["total_text"]

    # 2. Classify document
    classification = DocumentClassifier.classify(total_text, filename=filename)

    # 3. Extract underwriting fields with provenance
    extracted_fields = FieldExtractor.extract_from_text(
        text=total_text,
        doc_id=doc_id,
        doc_type=classification["document_type"]
    )

    # 4. Index into vector store for RAG
    page_texts = [p["text"] for p in parsed["pages"]]
    policy_vector_store.add_custom_document(
        doc_id=doc_id,
        doc_title=classification["document_label"],
        page_texts=page_texts,
        category="Pièce Justificative"
    )

    # 5. Persist to DB
    doc_record = Document(
        id=doc_id,
        case_id=case_id,
        filename=filename,
        doc_type=classification["document_type"],
        doc_label=classification["document_label"],
        page_count=parsed["page_count"],
        ocr_status="SUCCESS" if not parsed["is_ocr_needed"] else "OCR_APPLIED",
        confidence=classification["confidence"],
        file_path=dest_path,
        raw_text=total_text[:5000],  # store head for inspection
        extracted_fields_json=json.dumps(extracted_fields)
    )
    db.add(doc_record)

    # Audit event
    last_audit = db.query(AuditEvent).filter(AuditEvent.case_id == case_id).order_by(AuditEvent.timestamp.desc()).first()
    prev_hash = last_audit.current_hash if last_audit else ""
    audit = AuditEvent.create_event(
        case_id=case_id,
        event_type="DOCUMENT_UPLOADED",
        actor="Underwriter / Customer Portal",
        details={
            "doc_id": doc_id,
            "filename": filename,
            "classification": classification["document_type"],
            "fields_extracted_count": len(extracted_fields)
        },
        prev_hash=prev_hash
    )
    db.add(audit)
    db.commit()
    db.refresh(doc_record)

    return doc_record.to_dict()


@router.get("")
def list_case_documents(case_id: str, db: Session = Depends(get_db)):
    """
    Returns all uploaded documents and extracted fields for a case.
    """
    docs = db.query(Document).filter(Document.case_id == case_id).all()
    return [d.to_dict() for d in docs]
