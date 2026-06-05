from embeddings import generate_embedding

vector = generate_embedding(
    "Portugal is located in Europe"
)

print(len(vector))