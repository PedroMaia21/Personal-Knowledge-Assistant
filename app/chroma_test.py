import chromadb

client = chromadb.Client()

collection = client.get_or_create_collection(
    name = "test_collection"
)

collection.add(
    documents = [
        "Productivity systems improve organization.",
        "SQL joins combine tables",
        "Kanban visualizes workflow"
    ],
    ids = [
        "1",
        "2",
        "3"
    ]
)

print("Documents added successfully!")

results = collection.get()

print(results)