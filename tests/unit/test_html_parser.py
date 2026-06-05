import pytest
from talon.parsers.html import HtmlParser

def test_extract_links():
    html = """
    <html>
        <body>
            <a href="https://example.com">Example</a>
            <a href="/relative">Relative</a>
            <p>No link here</p>
            <a href="https://test.com">Test</a>
        </body>
    </html>
    """
    links = HtmlParser.extract_links(html)
    assert links == ["https://example.com", "/relative", "https://test.com"]

def test_extract_metadata():
    html = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="A test description">
            <meta property="og:title" content="Open Graph Title">
            <meta name="viewport" content="width=device-width">
        </head>
        <body></body>
    </html>
    """
    metadata = HtmlParser.extract_metadata(html)
    assert metadata["title"] == "Test Page"
    assert metadata["description"] == "A test description"
    assert metadata["og:title"] == "Open Graph Title"
    assert metadata["viewport"] == "width=device-width"

def test_extract_metadata_no_title():
    html = "<html><head></head><body></body></html>"
    metadata = HtmlParser.extract_metadata(html)
    assert "title" not in metadata
