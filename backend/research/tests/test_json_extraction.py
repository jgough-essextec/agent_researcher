"""Tests for the public extract_json_from_response utility."""
import json
import pytest

# These will FAIL until we rename the function (RED phase)
from research.services.gemini import extract_json_from_response


def test_extract_handles_preamble():
    text = 'Here are results:\n```json\n{"case_studies": []}\n```'
    result = extract_json_from_response(text)
    assert json.loads(result) == {"case_studies": []}


def test_extract_handles_trailing_text():
    text = '```json\n{"key": "val"}\n```\nHope this helps!'
    result = extract_json_from_response(text)
    assert json.loads(result) == {"key": "val"}


def test_extract_handles_no_fences():
    text = '{"case_studies": [{"competitor_name": "Acme"}]}'
    result = extract_json_from_response(text)
    assert json.loads(result)["case_studies"][0]["competitor_name"] == "Acme"


def test_extract_handles_plain_fence():
    text = '```\n{"key": "val"}\n```'
    result = extract_json_from_response(text)
    assert json.loads(result) == {"key": "val"}


def test_private_alias_still_works():
    """Backward compat — existing callers using _extract_json_from_response still work."""
    from research.services.gemini import _extract_json_from_response
    text = '{"key": "val"}'
    result = _extract_json_from_response(text)
    assert json.loads(result) == {"key": "val"}
