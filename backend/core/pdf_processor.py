import os
from datetime import datetime
from typing import Dict
from fastapi import UploadFile, HTTPException
from PyPDF2 import PdfReader, PdfException
from db.models import Document
from db.session import SessionLocal
import logging
import uuid

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.db = SessionLocal()

    async def process_pdf(self, file: UploadFile, doc_type: str) -> Dict:
        """
        Process uploaded PDF with comprehensive error handling
        Args:
            file: FastAPI UploadFile object
            doc_type: 'policy' or 'regulation'
        Returns:
            dict: {'id': str, 'text': str, 'path': str}
        Raises:
            HTTPException: For validation or processing errors
        """
        try:
            # Validate inputs
            if doc_type not in ["policy", "regulation"]:
                raise ValueError("Document type must be 'policy' or 'regulation'")
            
            if not file.filename.lower().endswith('.pdf'):
                raise ValueError("Only PDF files are allowed")

            # Create target directory
            target_dir = f"data/{doc_type}s/"
            os.makedirs(target_dir, exist_ok=True)

            # Generate unique filename
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(target_dir, unique_filename)

            # Save file
            file_content = await file.read()
            if not file_content:
                raise ValueError("Uploaded file is empty")
            
            with open(file_path, "wb") as f:
                f.write(file_content)

            # Extract text
            text = self._extract_text(file_path)
            
            # Save to database
            doc = self._save_to_db(
                filename=unique_filename,
                doc_type=doc_type,
                file_path=file_path,
                text=text
            )
            
            return {
                "id": doc.id,
                "text": text,
                "path": file_path
            }
            
        except ValueError as e:
            logger.warning(f"Validation error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except PdfException as e:
            logger.error(f"PDF processing error: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid PDF file")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")
        finally:
            # Cleanup if file was created but process failed
            if 'file_path' in locals() and os.path.exists(file_path) and ('doc' not in locals() or not doc):
                try:
                    os.remove(file_path)
                except:
                    pass
            await file.close()

    def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF with error handling"""
        try:
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                text = " ".join([page.extract_text() or "" for page in reader.pages])
                if not text.strip():
                    raise ValueError("PDF contains no extractable text")
                return text
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            raise ValueError(f"Could not extract text from PDF: {str(e)}")

    def _save_to_db(self, filename: str, doc_type: str, file_path: str, text: str) -> Document:
        """Save document metadata to database"""
        try:
            doc = Document(
                title=filename,
                source=doc_type,
                file_path=file_path,
                created_at=datetime.now()
            )
            self.db.add(doc)
            self.db.commit()
            self.db.refresh(doc)
            return doc
        except Exception as e:
            self.db.rollback()
            logger.error(f"Database error: {str(e)}")
            raise ValueError("Failed to save document to database")
        finally:
            self.db.close()

    def __del__(self):
        """Ensure DB connection is closed"""
        if hasattr(self, 'db'):
            self.db.close()