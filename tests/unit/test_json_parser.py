import pytest
from talon.parsers.json import JsonParser

def test_parse_valid_json():
    data = '{"key": "value", "list": [1, 2, 3]}'
    result = JsonParser.parse(data)
    assert result == {"key": "value", "list": [1, 2, 3]}

def test_parse_invalid_json():
    data = '{"key": "value",'
    result = JsonParser.parse(data)
    assert result is None

def test_parse_none():
    result = JsonParser.parse(None)
    assert result is None

def test_parse_non_string():
    result = JsonParser.parse(123)
    assert result is None
