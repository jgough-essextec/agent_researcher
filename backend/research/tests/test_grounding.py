"""Tests for research/services/grounding.py."""
from unittest.mock import MagicMock
from dataclasses import dataclass, field
from typing import List


# ── Minimal stubs matching gemini.py dataclasses ───────────────────────────

@dataclass
class WebSource:
    uri: str = ""
    title: str = ""


@dataclass
class GroundingMetadata:
    web_sources: List[WebSource] = field(default_factory=list)
    search_queries: List[str] = field(default_factory=list)


# ── Tests for extract_grounding_metadata ───────────────────────────────────

from research.services.grounding import extract_grounding_metadata, merge_grounding_metadata


def make_response(chunks=None, search_queries=None, has_candidates=True):
    """Build a mock Gemini response."""
    response = MagicMock()
    if not has_candidates:
        response.candidates = []
        return response

    candidate = MagicMock()
    grounding = MagicMock()

    if chunks is None and search_queries is None:
        candidate.grounding_metadata = None
    else:
        # Build grounding_chunks mocks
        built_chunks = []
        for uri, title in (chunks or []):
            chunk = MagicMock()
            chunk.web.uri = uri
            chunk.web.title = title
            built_chunks.append(chunk)
        grounding.grounding_chunks = built_chunks
        grounding.web_search_queries = search_queries or []
        candidate.grounding_metadata = grounding

    response.candidates = [candidate]
    return response


class TestExtractGroundingMetadata:
    def test_returns_none_when_no_candidates(self):
        response = make_response(has_candidates=False)
        result = extract_grounding_metadata(response, GroundingMetadata, WebSource)
        assert result is None

    def test_returns_none_when_no_grounding_metadata(self):
        response = make_response(chunks=None, search_queries=None)
        result = extract_grounding_metadata(response, GroundingMetadata, WebSource)
        assert result is None

    def test_extracts_web_sources(self):
        response = make_response(
            chunks=[('https://example.com', 'Example Site')],
            search_queries=['Acme Corp news'],
        )
        result = extract_grounding_metadata(response, GroundingMetadata, WebSource)
        assert result is not None
        assert len(result.web_sources) == 1
        assert result.web_sources[0].uri == 'https://example.com'
        assert result.web_sources[0].title == 'Example Site'

    def test_extracts_search_queries(self):
        response = make_response(
            chunks=[('https://example.com', 'Site')],
            search_queries=['query 1', 'query 2'],
        )
        result = extract_grounding_metadata(response, GroundingMetadata, WebSource)
        assert result is not None
        assert 'query 1' in result.search_queries
        assert 'query 2' in result.search_queries

    def test_returns_search_queries_only_when_no_chunks(self):
        response = make_response(chunks=[], search_queries=['fallback query'])
        result = extract_grounding_metadata(response, GroundingMetadata, WebSource)
        assert result is not None
        assert len(result.web_sources) == 0
        assert 'fallback query' in result.search_queries

    def test_returns_none_when_no_chunks_no_queries(self):
        response = make_response(chunks=[], search_queries=[])
        result = extract_grounding_metadata(response, GroundingMetadata, WebSource)
        assert result is None

    def test_handles_exception_gracefully(self):
        # When response.candidates raises, it should return None or an empty GroundingMetadata
        response = MagicMock()
        # Simulate a badly shaped response that causes downstream attribute access to fail
        response.candidates = [MagicMock(spec=[])]  # no grounding_metadata attr
        result = extract_grounding_metadata(response, GroundingMetadata, WebSource)
        # Either None or empty GroundingMetadata — both are acceptable fallbacks
        assert result is None or (result.web_sources == [] and result.search_queries == [])

    def test_multiple_chunks(self):
        response = make_response(
            chunks=[
                ('https://a.com', 'A'),
                ('https://b.com', 'B'),
                ('https://c.com', 'C'),
            ],
            search_queries=[],
        )
        result = extract_grounding_metadata(response, GroundingMetadata, WebSource)
        assert result is not None
        assert len(result.web_sources) == 3


class TestMergeGroundingMetadata:
    def _make_result(self, sources=None, queries=None, success=True):
        from research.services.gemini import GroundedQueryResult
        meta = None
        if sources is not None:
            from research.services.gemini import GroundingMetadata as GM, WebSource as WS
            web_sources = [WS(uri=u, title=t) for u, t in sources]
            meta = GM(web_sources=web_sources, search_queries=queries or [])
        return GroundedQueryResult(
            query_type='test',
            text='text',
            grounding_metadata=meta,
            success=success,
        )

    def test_merge_deduplicates_sources(self):
        results = {
            'q1': self._make_result([('https://a.com', 'A'), ('https://b.com', 'B')]),
            'q2': self._make_result([('https://a.com', 'A'), ('https://c.com', 'C')]),
        }
        merged = merge_grounding_metadata(results)
        uris = [s.uri for s in merged.web_sources]
        assert len(set(uris)) == len(uris)
        assert 'https://a.com' in uris
        assert 'https://b.com' in uris
        assert 'https://c.com' in uris

    def test_merge_handles_no_metadata(self):
        results = {
            'q1': self._make_result(sources=None),
            'q2': self._make_result(sources=None),
        }
        merged = merge_grounding_metadata(results)
        # Returns None when there are no sources or queries
        assert merged is None

    def test_merge_deduplicates_queries(self):
        results = {
            'q1': self._make_result([('https://a.com', 'A')], queries=['Acme news']),
            'q2': self._make_result([('https://b.com', 'B')], queries=['Acme news', 'Acme tech']),
        }
        merged = merge_grounding_metadata(results)
        assert merged.search_queries.count('Acme news') == 1
        assert 'Acme tech' in merged.search_queries
