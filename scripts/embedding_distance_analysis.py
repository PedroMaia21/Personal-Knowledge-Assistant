import numpy as np
from models.embedding import generate_embedding

def calculate_distance(value1, value2):
    vec1 = np.array(value1)
    vec2 = np.array(value2)
    return np.linalg.norm(vec1 - vec2)

def main():
    scenarios = {
        "identical": {"t1": "Vector databases store embeddings.", "t2": "Vector databases store embeddings."},
        "similar": {"t1": "Vector databases store embeddings.", "t2": "Embeddings are stored in vector databases."},
        "related": {"t1": "Vector databases store embeddings.", "t2": "Machine learning uses embeddings."},
        "unrelated": {"t1": "Vector databases store embeddings.", "t2": "My dog likes tennis balls."}
    }

    print("\n📐 Running Embedding Distance Analysis...")
    for case, texts in scenarios.items():
        emb1 = generate_embedding(texts["t1"])
        emb2 = generate_embedding(texts["t2"])
        distance = calculate_distance(emb1, emb2)
        print(f" -> {case.capitalize()}: L2 Distance = {distance:.4f}")

if __name__ == "__main__":
    main()