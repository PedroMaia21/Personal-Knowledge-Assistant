import chromadb

client = chromadb.Client()

collection = client.create_collection(
    name = "test_collection"
)

print("Collection created successfully!")