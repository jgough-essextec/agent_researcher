"""Context injection service for enriching research with relevant memories (AGE-16)."""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ContextResult:
    """Result of context retrieval."""
    client_profiles: List[Dict[str, Any]] = field(default_factory=list)
    sales_plays: List[Dict[str, Any]] = field(default_factory=list)
    memory_entries: List[Dict[str, Any]] = field(default_factory=list)
    relevance_summary: str = ""

    def to_prompt_context(self) -> str:
        """Convert to a string suitable for prompt injection."""
        sections = []

        if self.client_profiles:
            profiles_text = "\n".join([
                f"- {p.get('metadata', {}).get('client_name', 'Unknown')}: {p.get('document', '')[:200]}..."
                for p in self.client_profiles
            ])
            sections.append(f"## Related Client Profiles\n{profiles_text}")

        if self.sales_plays:
            plays_text = "\n".join([
                f"- {p.get('metadata', {}).get('title', 'Untitled')} ({p.get('metadata', {}).get('play_type', 'unknown')}): {p.get('document', '')[:200]}..."
                for p in self.sales_plays
            ])
            sections.append(f"## Relevant Sales Plays\n{plays_text}")

        if self.memory_entries:
            entries_text = "\n".join([
                f"- {e.get('metadata', {}).get('title', 'Untitled')}: {e.get('document', '')[:200]}..."
                for e in self.memory_entries
            ])
            sections.append(f"## Related Knowledge\n{entries_text}")

        if sections:
            return "\n\n".join(sections)
        return ""


class ContextInjector:
    """Service to retrieve and inject relevant context from vector store."""

    def __init__(self, vector_store=None):
        """Initialize the context injector.

        Args:
            vector_store: VectorStore instance (lazy loaded if not provided)
        """
        self._vector_store = vector_store

    @property
    def vector_store(self):
        """Lazy initialization of vector store."""
        if self._vector_store is None:
            from .vectorstore import VectorStore
            self._vector_store = VectorStore()
        return self._vector_store

    def get_context_for_research(
        self,
        client_name: str,
        industry: Optional[str] = None,
        query: Optional[str] = None,
        max_results_per_collection: int = 3,
    ) -> ContextResult:
        """Retrieve relevant context for a research job.

        Args:
            client_name: Name of the client being researched
            industry: Industry vertical (optional)
            query: Additional search query (optional)
            max_results_per_collection: Max results from each collection

        Returns:
            ContextResult with relevant items from each collection
        """
        search_text = f"{client_name} {industry or ''} {query or ''}".strip()
        result = ContextResult()

        try:
            # Search client profiles
            profiles = self._search_collection(
                'client_profiles',
                search_text,
                max_results_per_collection,
                where={'client_name': client_name} if client_name else None,
            )
            result.client_profiles = profiles

            # Search sales plays
            plays_filter = {'industry': industry} if industry else None
            plays = self._search_collection(
                'sales_plays',
                search_text,
                max_results_per_collection,
                where=plays_filter,
            )
            result.sales_plays = plays

            # Search memory entries
            entries = self._search_collection(
                'memory_entries',
                search_text,
                max_results_per_collection,
            )
            result.memory_entries = entries

            # Generate relevance summary
            total_results = len(profiles) + len(plays) + len(entries)
            result.relevance_summary = f"Found {total_results} relevant context items"

        except Exception as e:
            logger.exception("Error retrieving context")
            result.relevance_summary = f"Context retrieval failed: {str(e)}"

        return result

    def _search_collection(
        self,
        collection_name: str,
        query: str,
        n_results: int,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search a collection and format results.

        Args:
            collection_name: Name of the collection
            query: Search query
            n_results: Number of results
            where: Filter conditions

        Returns:
            List of result dicts
        """
        try:
            results = self.vector_store.query(
                collection_name,
                query,
                n_results=n_results,
                where=where,
            )

            # Format results
            formatted = []
            for i, doc_id in enumerate(results['ids'][0]):
                formatted.append({
                    'id': doc_id,
                    'document': results['documents'][0][i] if results['documents'] else '',
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results.get('distances') else 0,
                })
            return formatted

        except Exception as e:
            logger.warning(f"Error searching {collection_name}: {e}")
            return []

    def enrich_research_prompt(
        self,
        base_prompt: str,
        client_name: str,
        industry: Optional[str] = None,
    ) -> str:
        """Enrich a research prompt with relevant context.

        Args:
            base_prompt: The original research prompt
            client_name: Name of the client
            industry: Industry vertical

        Returns:
            Enriched prompt with injected context
        """
        context = self.get_context_for_research(client_name, industry)
        context_text = context.to_prompt_context()

        if context_text:
            return f"{base_prompt}\n\n---\n\n## Relevant Context from Knowledge Base\n\n{context_text}"

        return base_prompt
