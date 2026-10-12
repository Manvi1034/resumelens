import io

import pytest
from docx import Document
from reportlab.pdfgen import canvas

from resume_parser import ResumeParseError, extract_resume_text, validate_file

SAMPLE_TEXT = "Python developer with SQL, Pandas and machine learning skills"


def make_docx_bytes(text):
    """Create a small DOCX file in memory and return its bytes."""
    document = Document()
    document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def make_pdf_bytes(text):
    """Create a small one-page PDF in memory and return its bytes."""
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 750, text)
    pdf.save()
    return buffer.getvalue()


def test_docx_text_is_extracted():
    text = extract_resume_text("resume.docx", make_docx_bytes(SAMPLE_TEXT))
    assert "Python" in text and "Pandas" in text


def test_pdf_text_is_extracted():
    text = extract_resume_text("resume.pdf", make_pdf_bytes(SAMPLE_TEXT))
    assert "Python" in text and "Pandas" in text


def test_unsupported_extension_is_rejected():
    with pytest.raises(ResumeParseError, match="Unsupported"):
        validate_file("resume.txt", 100)


def test_empty_file_is_rejected():
    with pytest.raises(ResumeParseError, match="empty"):
        validate_file("resume.pdf", 0)


def test_oversized_file_is_rejected():
    with pytest.raises(ResumeParseError, match="larger"):
        validate_file("resume.pdf", 6 * 1024 * 1024)


def test_corrupted_pdf_is_rejected():
    with pytest.raises(ResumeParseError, match="could not be read"):
        extract_resume_text("resume.pdf", b"this is not a real pdf")


def test_corrupted_docx_is_rejected():
    with pytest.raises(ResumeParseError, match="could not be read"):
        extract_resume_text("resume.docx", b"this is not a real docx")


def test_blank_pdf_is_treated_as_unreadable():
    with pytest.raises(ResumeParseError, match="enough text"):
        extract_resume_text("resume.pdf", make_pdf_bytes(""))