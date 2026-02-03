"""ChromaDB vector store service (AGE-14)."""
import logging
from typing import List, Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Service for managing ChromaDB vector store collections."""

    COLLECTION_NAMES = {
        'client_profiles': 'client_profiles',
        'sales_plays': 'sales_plays',
        'memory_entries': 'memory_entries',
    }

    def __init__(self, persist_directory: Optional[str] = None):
        """Initialize the vector store.

        Args:
            persist_directory: Directory to persist ChromaDB data.
                             Defaults to settings.CHROMA_PERSIST_DIR.
        """
        self.persist_directory = persist_directory or getattr(
            settings, 'CHROMA_PERSIST_DIR', './chroma_data'
        )
        self._client = None
        self._embedding_function = None

    @property
    def client(self):
        """Lazy initialization of ChromaDB client."""
        if self._client is None:
            import chromadb
            from chromadb.config import Settings

            self._client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_directory,
                anonymized_telemetry=False,
            ))
        return self._client

    @property
    def embedding_function(self):
        """Lazy initialization of embedding function."""
        if self._embedding_function is None:
            from chromadb.utils import embedding_functions
            self._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        return self._embedding_function

    def get_or_create_collection(self, collection_name: str):
        """Get or create a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            ChromaDB collection
        """
        return self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
        )

    def add_document(
        self,
        collection_name: str,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a document to a collection.

        Args:
            collection_name: Name of the collection
            document_id: Unique ID for the document
            content: Text content to embed and store
            metadata: Optional metadata dict

        Returns:
            The document ID
        """
        collection = self.get_or_create_collection(collection_name)

        collection.add(
            ids=[document_id],
            documents=[content],
            metadatas=[metadata or {}],
        )

        logger.info(f"Added document {document_id} to collection {collection_name}")
        return document_id

    def update_document(
        self,
        collection_name: str,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Update a document in a collection.

        Args:
            collection_name: Name of the collection
            document_id: ID of the document to update
            content: New text content
            metadata: Optional new metadata

        Returns:
            The document ID
        """
        collection = self.get_or_create_collection(collection_name)

        collection.update(
            ids=[document_id],
            documents=[content],
            metadatas=[metadata or {}],
        )

        logger.info(f"Updated document {document_id} in collection {collection_name}")
        return document_id

    def delete_document(
        self,
        collection_name: str,
        document_id: str,
    ):
        """Delete a document from a collection.

        Args:
            collection_name: Name of the collection
            document_id: ID of the document to delete
        """
        collection = self.get_or_create_collection(collection_name)
        collection.delete(ids=[document_id])
        logger.info(f"Deleted document {document_id} from collection {collection_name}")

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Query a collection for similar documents.

        Args:
            collection_name: Name of the collection
            query_text: Text to search for
            n_results: Maximum number of results to return
            where: Optional filter conditions
            include: What to include in results (documents, metadatas, distances)

        Returns:
            Query results dict with ids, documents, metadatas, distances
        """
        collection = self.get_or_create_collection(collection_name)

        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            include=include or ["documents", "metadatas", "distances"],
        )

        logger.info(f"Query in {collection_name} returned {len(results['ids'][0])} results")
        return results

    def get_document(
        self,
        collection_name: str,
        document_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID.

        Args:
            collection_name: Name of the collection
            document_id: ID of the document

        Returns:
            Document dict with id, document, metadata, or None if not found
        """
        collection = self.get_or_create_collection(collection_name)

        result = collection.get(
            ids=[document_id],
            include=["documents", "metadatas"],
        )

        if result['ids'] and len(result['ids']) > 0:
            return {
                'id': result['ids'][0],
                'document': result['documents'][0] if result['documents'] else None,
                'metadata': result['metadatas'][0] if result['metadatas'] else {},
            }
        return None

    def count_documents(self, collection_name: str) -> int:
        """Get the count of documents in a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Number of documents
        """
        collection = self.get_or_create_collection(collection_name)
        return collection.count()

    def persist(self):
        """Persist the database to disk."""
        self.client.persist()
        logger.info("Persisted ChromaDB to disk")
