import io
from pypdf import PdfReader
from typing import Optional

class PdfParser:
    @staticmethod
    def extract_text(content: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(content))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception:
            return ""
