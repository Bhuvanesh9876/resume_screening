"""
Text Extractor Module

This module handles the extraction of text from PDF and DOCX files.
It employs multiple strategies (PyMuPDF, pdfplumber, pdfminer) to ensure
robust text extraction from various PDF formats.
"""

import io
import re
from typing import Any
import fitz
import pdfplumber
from pdfminer.high_level import extract_text as pdfminer_extract

def _extract_with_pymupdf(file: Any) -> str:
    """Extract text using PyMuPDF (fitz)."""
    try:
        if hasattr(file, "read"):
            data = file.read()
            file.seek(0)
        else:
            with open(file, "rb") as f:
                data = f.read()

        doc = fitz.open(stream=data, filetype="pdf")
        pages = []
        for page in doc:
            text = page.get_text("text")
            if text and text.strip():
                pages.append(text.strip())
        doc.close()
        return "\n".join(pages)
    except Exception:
        return ""

def _extract_with_pdfplumber(file: Any) -> str:
    """Extract text using pdfplumber."""
    try:
        if hasattr(file, "seek"):
            file.seek(0)
        with pdfplumber.open(file) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text and text.strip():
                    pages.append(text.strip())
        return "\n".join(pages)
    except Exception:
        return ""

def _extract_with_pdfminer(file: Any) -> str:
    """Extract text using pdfminer.six."""
    try:
        if hasattr(file, "read"):
            file.seek(0)
            data = file.read()
            file.seek(0)
            return pdfminer_extract(io.BytesIO(data))
        return pdfminer_extract(file)
    except Exception:
        return ""

def _extract_from_docx(file: Any) -> str:
    """Extract text from DOCX files using python-docx."""
    try:
        from docx import Document
        if hasattr(file, "read"):
            file.seek(0)
            doc = Document(file)
        else:
            doc = Document(file)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception:
        return ""

def _post_clean(text: str) -> str:
    """
    Clean and normalize extracted text.
    Removes invisible characters, weird hyphenation, and excessive newlines.
    """
    if not text:
        return ""
    text = text.replace("\xa0", " ").replace("\u200b", "")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("\x00", "")
    return text.strip()

def extract_text_from_pdf(file: Any) -> str:
    """
    Main entry point for text extraction.
    Handles DOCX files and attempts multiple PDF extraction methods in order of preference.
    """
    filename = ""
    if hasattr(file, "name"):
        filename = file.name.lower()

    if filename.endswith(".docx"):
        text = _extract_from_docx(file)
        return _post_clean(text)

    # Strategy 1: PyMuPDF (Fast & Good for standard PDFs)
    text = _extract_with_pymupdf(file)
    if len(text.strip()) > 50:
        return _post_clean(text)

    # Strategy 2: pdfplumber (Good for complex layouts)
    text = _extract_with_pdfplumber(file)
    if len(text.strip()) > 50:
        return _post_clean(text)

    # Strategy 3: pdfminer (Fallback)
    text = _extract_with_pdfminer(file)
    return _post_clean(text)
