"""Source adapters namespace — lazy by design; import concrete adapters explicitly."""

from app.sources.base import AdapterSource, RawEvent, SourceAdapter, SourceFailure

__all__ = ["AdapterSource", "RawEvent", "SourceFailure", "SourceAdapter"]
