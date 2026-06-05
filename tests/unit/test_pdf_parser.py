import pytest
from unittest.mock import MagicMock, patch
from talon.parsers.pdf import PdfParser

def test_extract_text_valid_pdf():
    # Mocking PdfReader to avoid needing a real PDF file
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Page content"

    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]

    with patch("talon.parsers.pdf.PdfReader", return_value=mock_reader):
        result = PdfParser.extract_text(b"fake pdf content")
        assert result == "Page content\n"

def test_extract_text_invalid_pdf():
    # PdfReader should raise an exception for random bytes
    result = PdfParser.extract_text(b"not a pdf")
    assert result == ""
