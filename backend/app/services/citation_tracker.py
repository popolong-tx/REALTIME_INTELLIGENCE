from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class Citation:
    """Citation for a piece of information."""

    def __init__(
        self,
        source: str,
        url: Optional[str] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        published_at: Optional[datetime] = None,
        accessed_at: Optional[datetime] = None,
        content_snippet: Optional[str] = None,
        confidence: float = 1.0,
    ):
        self.source = source
        self.url = url
        self.title = title
        self.author = author
        self.published_at = published_at
        self.accessed_at = accessed_at or datetime.utcnow()
        self.content_snippet = content_snippet
        self.confidence = confidence
        self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique ID for citation."""
        content = f"{self.source}:{self.url}:{self.title}:{self.published_at}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "source": self.source,
            "url": self.url,
            "title": self.title,
            "author": self.author,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "accessed_at": self.accessed_at.isoformat(),
            "content_snippet": self.content_snippet,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Citation":
        """Create from dictionary."""
        return cls(
            source=data.get("source", ""),
            url=data.get("url"),
            title=data.get("title"),
            author=data.get("author"),
            published_at=datetime.fromisoformat(data["published_at"]) if data.get("published_at") else None,
            accessed_at=datetime.fromisoformat(data["accessed_at"]) if data.get("accessed_at") else None,
            content_snippet=data.get("content_snippet"),
            confidence=data.get("confidence", 1.0),
        )


class QueryWindow:
    """Query window tracking for search results."""

    def __init__(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        source: str,
        result_count: int,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        self.query = query
        self.start_time = start_time
        self.end_time = end_time
        self.source = source
        self.result_count = result_count
        self.parameters = parameters or {}
        self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique ID for query window."""
        content = f"{self.query}:{self.start_time}:{self.end_time}:{self.source}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "query": self.query,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "source": self.source,
            "result_count": self.result_count,
            "parameters": self.parameters,
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
        }


class CitationTracker:
    """Tracker for citations and query windows."""

    def __init__(self):
        self.citations: Dict[str, Citation] = {}
        self.query_windows: Dict[str, QueryWindow] = {}

    def add_citation(self, citation: Citation) -> str:
        """Add a citation and return its ID."""
        self.citations[citation.id] = citation
        return citation.id

    def get_citation(self, citation_id: str) -> Optional[Citation]:
        """Get a citation by ID."""
        return self.citations.get(citation_id)

    def get_citations_for_content(self, content: str) -> List[Citation]:
        """Get citations relevant to content."""
        # Simple keyword matching - in production, use embeddings
        relevant_citations = []
        content_lower = content.lower()

        for citation in self.citations.values():
            if citation.content_snippet:
                snippet_lower = citation.content_snippet.lower()
                # Check if any words from snippet appear in content
                snippet_words = set(snippet_lower.split())
                content_words = set(content_lower.split())
                if snippet_words.intersection(content_words):
                    relevant_citations.append(citation)

        return relevant_citations

    def add_query_window(self, query_window: QueryWindow) -> str:
        """Add a query window and return its ID."""
        self.query_windows[query_window.id] = query_window
        return query_window.id

    def get_query_window(self, window_id: str) -> Optional[QueryWindow]:
        """Get a query window by ID."""
        return self.query_windows.get(window_id)

    def get_recent_queries(
        self,
        source: Optional[str] = None,
        limit: int = 10,
    ) -> List[QueryWindow]:
        """Get recent query windows."""
        windows = list(self.query_windows.values())

        if source:
            windows = [w for w in windows if w.source == source]

        windows.sort(key=lambda w: w.end_time, reverse=True)
        return windows[:limit]

    def create_citation_from_data(
        self,
        data: Dict[str, Any],
        source: str,
    ) -> Citation:
        """Create citation from data source response."""
        return Citation(
            source=source,
            url=data.get("url"),
            title=data.get("title"),
            author=data.get("author"),
            published_at=datetime.fromisoformat(data["published_at"]) if data.get("published_at") else None,
            content_snippet=data.get("description", "")[:200],
            confidence=data.get("confidence", 0.9),
        )

    def create_query_window_from_search(
        self,
        query: str,
        source: str,
        start_time: datetime,
        result_count: int,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> QueryWindow:
        """Create query window from search operation."""
        return QueryWindow(
            query=query,
            start_time=start_time,
            end_time=datetime.utcnow(),
            source=source,
            result_count=result_count,
            parameters=parameters,
        )

    def generate_citation_report(self) -> Dict[str, Any]:
        """Generate report of all citations."""
        return {
            "total_citations": len(self.citations),
            "total_query_windows": len(self.query_windows),
            "citations_by_source": self._count_by_source(),
            "recent_queries": [q.to_dict() for q in self.get_recent_queries(limit=5)],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _count_by_source(self) -> Dict[str, int]:
        """Count citations by source."""
        counts: Dict[str, int] = {}
        for citation in self.citations.values():
            counts[citation.source] = counts.get(citation.source, 0) + 1
        return counts

    def clear_old_data(self, days: int = 30) -> int:
        """Clear data older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        old_citations = [
            cid for cid, c in self.citations.items()
            if c.accessed_at < cutoff
        ]
        for cid in old_citations:
            del self.citations[cid]

        old_windows = [
            wid for wid, w in self.query_windows.items()
            if w.end_time < cutoff
        ]
        for wid in old_windows:
            del self.query_windows[wid]

        return len(old_citations) + len(old_windows)


# Global tracker instance
citation_tracker = CitationTracker()
