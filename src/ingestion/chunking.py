from typing import List, Dict, Any

from src.config.config_chunking import (
    CHUNKER_V1_SIZE,
    CHUNKER_V1_OVERLAP,
    CHUNKER_V1_VERSION,
)


class ChunkerV1:
    """
    V1 baseline chunking strategy.

    Algorithm : sliding-window character splitter
    Chunk size : 1000 characters
    Overlap    : 100 characters

    Do NOT modify these parameters to experiment.
    Create ChunkerV2 for any new strategy so results stay comparable.
    """

    chunk_size: int = CHUNKER_V1_SIZE
    overlap: int = CHUNKER_V1_OVERLAP
    version: str = CHUNKER_V1_VERSION

    def chunk_document(
        self,
        text: str,
        source: str = "unknown",
    ) -> List[Dict[str, Any]]:
        """
        Splits *text* into overlapping character slices.

        Returns a list of chunk dicts, each containing:
            text            – the raw chunk string
            metadata        – source, chunk_index, chunk_length, chunker_version
        """
        if not text:
            return []

        chunks: List[Dict[str, Any]] = []
        start = 0
        index = 0

        while start < len(text):
            end = start + self.chunk_size
            slice_ = text[start:end]

            chunks.append({
                "text": slice_,
                "metadata": {
                    "source": source,
                    "chunk_index": index,
                    "chunk_length": len(slice_),
                    "chunker_version": self.version,
                },
            })

            start += max(1, self.chunk_size - self.overlap)
            index += 1

        return chunks