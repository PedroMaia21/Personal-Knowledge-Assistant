from embeddings import generate_embeddings

vector = generate_embeddings(
    "Portugal is located in Europe"
)

print(len(vector))