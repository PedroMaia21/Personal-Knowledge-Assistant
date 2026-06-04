from pathlib import Path

def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 100,
):
    chunks = []
    
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks

if __name__ == "__main__":

    text = Path("documents/test.txt").read_text(encoding="utf-8")  # Read text from a file
    
    chunks = chunk_text(text)
    
    print(f"Total chunks created: {len(chunks)}\n")
    
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}:\n{chunk[:100]}\n") 