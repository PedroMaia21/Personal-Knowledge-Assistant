from pathlib import Path

SUPPORTED_EXTENSIONS = ['.txt', '.md']

def load_file(file_path: Path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()
    
def load_folder(folder_path: str):
    folder = Path(folder_path)
    
    documents = []
    for file_path in folder.rglob('*'):
        if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                content = load_file(file_path)
                
                documents.append({
                    'path': str(file_path),
                    'content': content
                })
            except Exception as e:
                print(f"[Error loading {file_path}]: {e}")
    
    return documents

if __name__ == "__main__":
    docs = load_folder("./data")
    print(f"Loaded {len(docs)} documents.\n")
    print(docs[0] if docs else "No documents found.")