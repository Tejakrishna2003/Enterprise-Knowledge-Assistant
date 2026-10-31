import os
import re
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from pypdf import PdfReader
from pypdf.errors import PdfReadError

logger = logging.getLogger(__name__)

class DocumentProcessingError(Exception):
    pass

class DocumentService:
    @staticmethod
    def extract_text(file_path: str, file_type: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found on disk: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise DocumentProcessingError("File is empty (0 bytes).")

        # Plain Text and Markdown
        if file_type in ["text/plain", "text/markdown"] or file_path.endswith((".txt", ".md")):
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                if not content.strip():
                    raise DocumentProcessingError("Extracted text is empty or contains only whitespace.")
                return content
            except Exception as e:
                raise DocumentProcessingError(f"Failed to read plain text file: {str(e)}") from e

        # PDF Documents
        elif file_type == "application/pdf" or file_path.endswith(".pdf"):
            try:
                reader = PdfReader(file_path)
                if len(reader.pages) == 0:
                    raise DocumentProcessingError("PDF contains 0 pages.")

                extracted_pages = []
                for i, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text() or ""
                    except Exception as page_err:
                        logger.warning(f"Error extracting text from page {i+1}: {page_err}")
                        text = ""
                    extracted_pages.append(f"[Page {i+1}]\n{text}")

                full_text = "\n\n".join(extracted_pages)
                if not full_text.replace(f"[Page ", "").replace("]", "").strip():
                    raise DocumentProcessingError("PDF contains no extractable text. Scanned-document OCR is outside scope.")
                return full_text

            except PdfReadError as pdf_err:
                raise DocumentProcessingError(f"Corrupt or malformed PDF: {str(pdf_err)}") from pdf_err
            except Exception as e:
                raise DocumentProcessingError(f"PDF processing failed: {str(e)}") from e

        else:
            raise DocumentProcessingError(f"Unsupported file format: {file_type}. Supported formats: .txt, .md, .pdf")

    @staticmethod
    def chunk_document(content: str, doc_id: str, ws_id: str) -> List[Dict[str, Any]]:
        chunks = []
        # Split into logical sections by markdown headers (## ) or page delimiters ([Page X])
        section_pattern = r'(?=(?:^|\n)(?:##?\s+|\[Page\s+\d+\]))'
        raw_sections = re.split(section_pattern, content)

        chunk_idx = 0
        current_page = 1

        for sec in raw_sections:
            sec = sec.strip()
            if not sec:
                continue

            # Update page number if delimiter found
            page_match = re.search(r'\[Page\s+(\d+)\]', sec)
            if page_match:
                current_page = int(page_match.group(1))

            # Detect section title
            heading_match = re.search(r'^##?\s+([^\n]+)', sec, re.MULTILINE)
            if heading_match:
                section_title = heading_match.group(1).strip()
            else:
                section_title = f"Section {chunk_idx + 1}"

            # Sub-split long blocks into 500-700 character chunks with overlap
            if len(sec) > 750:
                paragraphs = sec.split("\n\n")
                buffer = ""
                for p in paragraphs:
                    if len(buffer) + len(p) > 650:
                        if buffer.strip():
                            chunks.append({
                                "_id": f"chk_{doc_id}_{chunk_idx}",
                                "document_id": doc_id,
                                "workspace_id": ws_id,
                                "chunk_index": chunk_idx,
                                "section_title": section_title,
                                "page_number": current_page,
                                "content": buffer.strip(),
                                "created_at": datetime.now(timezone.utc)
                            })
                            chunk_idx += 1
                        buffer = p + "\n\n"
                    else:
                        buffer += p + "\n\n"
                if buffer.strip():
                    chunks.append({
                        "_id": f"chk_{doc_id}_{chunk_idx}",
                        "document_id": doc_id,
                        "workspace_id": ws_id,
                        "chunk_index": chunk_idx,
                        "section_title": section_title,
                        "page_number": current_page,
                        "content": buffer.strip(),
                        "created_at": datetime.now(timezone.utc)
                    })
                    chunk_idx += 1
            else:
                chunks.append({
                    "_id": f"chk_{doc_id}_{chunk_idx}",
                    "document_id": doc_id,
                    "workspace_id": ws_id,
                    "chunk_index": chunk_idx,
                    "section_title": section_title,
                    "page_number": current_page,
                    "content": sec,
                    "created_at": datetime.now(timezone.utc)
                })
                chunk_idx += 1

        return chunks
