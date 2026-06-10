from app.embeddings import generate_embedding
import numpy as np

def main():
    tests = {}

    tests["identical"] = {"text1": "Vector databases store embeddings.", "text2": "Vector databases store embeddings."}
    tests["similar"] = {"text1": "Vector databases store embeddings.", "text2": "Embeddings are stored in vector databases."}
    tests["related"] = {"text1": "Vector databases store embeddings.", "text2": "Machine learning uses embeddings."}
    tests["unrelated"] = {"text1": "Vector databases store embeddings.", "text2": "My dog likes tennis balls."}

    for type in tests:
        embedding1 = generate_embedding(tests.get(type).get("text1"))
        embedding2 = generate_embedding(tests.get(type).get("text2"))

        distance = calculate_distance(embedding1, embedding2)

        print(f"{type}: {distance}")


def calculate_distance(value1, value2):
    vec1 = np.array(value1)
    vec2 = np.array(value2)

    return np.linalg.norm(vec1 - vec2)

if __name__ == "__main__":
    main()