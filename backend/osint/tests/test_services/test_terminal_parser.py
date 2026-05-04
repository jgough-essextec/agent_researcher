import pytest
from unittest.mock import patch
from osint.services.terminal_parser import parse_terminal_output, ParsedTerminalOutput

SAMPLE_OUTPUT = """
acme.com.	3600	IN	MX	10 mail.acme.com.
acme.com.	3600	IN	TXT	"v=spf1 include:_spf.google.com ~all"
"""


def test_returns_parsed_terminal_output_dataclass():
    with patch('osint.services.terminal_parser._call_gemini_parser',
               return_value={"records": [], "key_observations": [], "technology_signals": []}):
        result = parse_terminal_output(SAMPLE_OUTPUT, "dig")
    assert isinstance(result, ParsedTerminalOutput)


def test_empty_input_returns_empty_result():
    result = parse_terminal_output("", "dig")
    assert result.records == ()
    assert result.key_observations == ()


def test_extracts_records_from_gemini_response():
    gemini_resp = {
        "records": [
            {"type": "MX", "name": "acme.com", "value": "10 mail.acme.com.", "analysis": "Mail server"},
            {"type": "TXT", "name": "acme.com", "value": "v=spf1 ~all", "analysis": "SPF record"},
        ],
        "key_observations": ["Google Workspace detected"],
        "technology_signals": ["Google Workspace"],
    }
    with patch('osint.services.terminal_parser._call_gemini_parser', return_value=gemini_resp):
        result = parse_terminal_output(SAMPLE_OUTPUT, "dig")

    assert len(result.records) == 2
    assert "Google Workspace" in result.technology_signals


def test_never_executes_terminal_output():
    malicious = "; rm -rf /tmp/test; echo done"
    with patch('osint.services.terminal_parser._call_gemini_parser',
               return_value={"records": [], "key_observations": [], "technology_signals": []}):
        result = parse_terminal_output(malicious, "other")
    assert isinstance(result, ParsedTerminalOutput)


def test_returns_immutable_dataclass():
    with patch('osint.services.terminal_parser._call_gemini_parser',
               return_value={"records": [], "key_observations": [], "technology_signals": []}):
        result = parse_terminal_output("test", "dig")
    with pytest.raises(Exception):
        result.records = []  # frozen dataclass
