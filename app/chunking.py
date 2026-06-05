from pathlib import Path

from embeddings import generate_embeddings

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

    embeded_chunks = generate_embeddings(chunks) 

    print(f"Total chunks created: {len(chunks)}\n")
    print(f"Text of the first chunk: {embeded_chunks[0]['text']}...\n")
    print(f"Total embedded chunks: {len(embeded_chunks[0]['embedding'])}\n")

    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}:\n{chunk[:100]}\n")