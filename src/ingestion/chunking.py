from typing import List

def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 100,
) -> List[str]:
    """Splits string text cleanly into sliding-window character slices."""
    chunks = []
    start = 0

    if not text:
        return chunks
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += max(1, chunk_size - overlap)

    return chunks