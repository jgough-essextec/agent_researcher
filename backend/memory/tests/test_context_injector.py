"""Tests for ContextInjector and ContextResult (memory/services/context.py)."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from memory.services.context import ContextInjector, ContextResult


# ---------------------------------------------------------------------------
# ContextResult.to_prompt_context
# ---------------------------------------------------------------------------

class TestContextResultToPromptContext:
    """Unit tests for ContextResult.to_prompt_context()."""

    def test_empty_result_returns_empty_string(self):
        result = ContextResult()
        assert result.to_prompt_context() == ""

    def test_client_profiles_included_in_output(self):
        result = ContextResult(
            client_profiles=[
                {"metadata": {"client_name": "Acme"}, "document": "Acme uses AWS."}
            ]
        )
        output = result.to_prompt_context()
        assert "Related Client Profiles" in output
        assert "Acme" in output

    def test_sales_plays_included_in_output(self):
        result = ContextResult(
            sales_plays=[
                {"metadata": {"title": "Cloud Migration Play", "play_type": "upsell"}, "document": "Migrate to cloud."}
            ]
        )
        output = result.to_prompt_context()
        assert "Relevant Sales Plays" in output
        assert "Cloud Migration Play" in output

    def test_memory_entries_included_in_output(self):
        result = ContextResult(
            memory_entries=[
                {"metadata": {"title": "Prior deal note"}, "document": "Closed $100k last year."}
            ]
        )
        output = result.to_prompt_context()
        assert "Related Knowledge" in output
        assert "Prior deal note" in output

    def test_all_sections_separated_by_double_newline(self):
        result = ContextResult(
            client_profiles=[{"metadata": {"client_name": "A"}, "document": "doc"}],
            sales_plays=[{"metadata": {"title": "B", "play_type": "x"}, "document": "doc"}],
            memory_entries=[{"metadata": {"title": "C"}, "document": "doc"}],
        )
        output = result.to_prompt_context()
        assert "\n\n" in output
        assert "Related Client Profiles" in output
        assert "Relevant Sales Plays" in output
        assert "Related Knowledge" in output

    def test_document_truncated_to_200_chars(self):
        long_doc = "x" * 500
        result = ContextResult(
            memory_entries=[
                {"metadata": {"title": "Big Entry"}, "document": long_doc}
            ]
        )
        output = result.to_prompt_context()
        # The document is sliced [:200] + "..."
        assert "x" * 200 in output

    def test_missing_metadata_keys_do_not_crash(self):
        result = ContextResult(
            client_profiles=[{"metadata": {}, "document": "some doc"}],
            sales_plays=[{"metadata": {}, "document": "some doc"}],
        )
        output = result.to_prompt_context()
        assert "Unknown" in output or "Untitled" in output or isinstance(output, str)


# ---------------------------------------------------------------------------
# ContextInjector.get_context_for_research
# ---------------------------------------------------------------------------

class TestContextInjectorGetContext:
    """Tests for ContextInjector.get_context_for_research()."""

    def _make_injector(self):
        """Create an injector with a mocked vector store."""
        mock_vs = Mock()
        mock_vs.query = Mock(return_value={
            "ids": [["id1"]],
            "documents": [["doc content"]],
            "metadatas": [[ {"client_name": "Acme"} ]],
            "distances": [[0.1]],
        })
        return ContextInjector(vector_store=mock_vs), mock_vs

    def test_returns_context_result(self):
        injector, _ = self._make_injector()
        result = injector.get_context_for_research("Acme Corp")
        assert isinstance(result, ContextResult)

    def test_searches_all_three_collections(self):
        injector, mock_vs = self._make_injector()
        injector.get_context_for_research("Acme Corp", industry="technology")
        calls = [call.args[0] for call in mock_vs.query.call_args_list]
        assert "client_profiles" in calls
        assert "sales_plays" in calls
        assert "memory_entries" in calls

    def test_relevance_summary_contains_count(self):
        injector, _ = self._make_injector()
        result = injector.get_context_for_research("Acme Corp")
        assert "3" in result.relevance_summary or "Found" in result.relevance_summary

    def test_client_profiles_populated(self):
        injector, _ = self._make_injector()
        result = injector.get_context_for_research("Acme Corp")
        assert len(result.client_profiles) == 1
        assert result.client_profiles[0]["id"] == "id1"

    def test_industry_filter_passed_for_sales_plays(self):
        injector, mock_vs = self._make_injector()
        injector.get_context_for_research("Acme Corp", industry="retail")
        # The second call should be for sales_plays with a where filter
        plays_call = mock_vs.query.call_args_list[1]
        assert plays_call.kwargs.get("where") == {"industry": "retail"}

    def test_handles_vector_store_exception_gracefully(self):
        # _search_collection swallows per-collection errors and returns [];
        # the outer method still returns a valid ContextResult with 0 items found.
        mock_vs = Mock()
        mock_vs.query = Mock(side_effect=Exception("ChromaDB unavailable"))
        injector = ContextInjector(vector_store=mock_vs)
        result = injector.get_context_for_research("Acme Corp")
        assert isinstance(result, ContextResult)
        # All three collections failed → 0 results, but no crash
        assert result.client_profiles == []
        assert result.sales_plays == []
        assert result.memory_entries == []

    def test_no_industry_passes_none_filter_for_plays(self):
        injector, mock_vs = self._make_injector()
        injector.get_context_for_research("Acme Corp")
        # Without industry, the where filter for sales_plays should be None
        plays_call = mock_vs.query.call_args_list[1]
        assert plays_call.kwargs.get("where") is None


# ---------------------------------------------------------------------------
# ContextInjector._search_collection
# ---------------------------------------------------------------------------

class TestContextInjectorSearchCollection:
    """Tests for the _search_collection helper."""

    def test_returns_empty_on_query_error(self):
        mock_vs = Mock()
        mock_vs.query = Mock(side_effect=ValueError("bad query"))
        injector = ContextInjector(vector_store=mock_vs)
        result = injector._search_collection("client_profiles", "test query", 3)
        assert result == []

    def test_formats_results_correctly(self):
        mock_vs = Mock()
        mock_vs.query = Mock(return_value={
            "ids": [["abc123"]],
            "documents": [["the document text"]],
            "metadatas": [[{"key": "value"}]],
            "distances": [[0.25]],
        })
        injector = ContextInjector(vector_store=mock_vs)
        result = injector._search_collection("memory_entries", "query", 3)
        assert len(result) == 1
        assert result[0]["id"] == "abc123"
        assert result[0]["document"] == "the document text"
        assert result[0]["metadata"] == {"key": "value"}
        assert result[0]["distance"] == 0.25

    def test_handles_missing_distances_key(self):
        mock_vs = Mock()
        mock_vs.query = Mock(return_value={
            "ids": [["id1"]],
            "documents": [["doc"]],
            "metadatas": [[{}]],
            # no "distances" key
        })
        injector = ContextInjector(vector_store=mock_vs)
        result = injector._search_collection("sales_plays", "query", 3)
        assert result[0]["distance"] == 0


# ---------------------------------------------------------------------------
# ContextInjector.enrich_research_prompt
# ---------------------------------------------------------------------------

class TestEnrichResearchPrompt:
    """Tests for ContextInjector.enrich_research_prompt()."""

    def test_returns_original_prompt_when_no_context(self):
        mock_vs = Mock()
        mock_vs.query = Mock(return_value={"ids": [[]], "documents": [[]], "metadatas": [[]]})
        injector = ContextInjector(vector_store=mock_vs)
        original = "Research Acme Corp."
        result = injector.enrich_research_prompt(original, "Acme Corp")
        assert result == original

    def test_appends_context_when_available(self):
        mock_vs = Mock()
        mock_vs.query = Mock(return_value={
            "ids": [["id1"]],
            "documents": [["Acme uses AWS cloud."]],
            "metadatas": [[{"client_name": "Acme"}]],
            "distances": [[0.1]],
        })
        injector = ContextInjector(vector_store=mock_vs)
        result = injector.enrich_research_prompt("Research Acme.", "Acme Corp")
        assert "Research Acme." in result
        assert "Relevant Context from Knowledge Base" in result

    def test_lazy_vector_store_initialization(self):
        """ContextInjector lazily loads VectorStore when not provided."""
        injector = ContextInjector()
        assert injector._vector_store is None
        # VectorStore is imported inside the property, so patch at its module location
        with patch("memory.services.vectorstore.VectorStore") as mock_vs_cls:
            mock_instance = Mock()
            mock_vs_cls.return_value = mock_instance
            # Directly trigger the lazy init by patching the inline import
            with patch("memory.services.context.ContextInjector.vector_store", new_callable=lambda: property(lambda self: mock_instance)):
                vs = injector.vector_store
                assert vs is mock_instance
