import logging
from pathlib import Path
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = ['.txt', '.md']

def load_file(file_path: Path) -> str:
    """Reads content from a single text file cleanly."""
    return file_path.read_text(encoding='utf-8')
    
def load_folder(folder_path: str) -> List[Dict[str, str]]:
    """Recursively crawls a directory for supported text files."""
    folder = Path(folder_path)
    documents = []

    if not folder.exists():
        logger.warning(f"Target folder path does not exist: {folder_path}")
        return documents    
    
    for file_path in folder.rglob('*'):
        if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                content = load_file(file_path)
                
                documents.append({
                    'path': str(file_path),
                    'content': content
                })
            except Exception as e:
                logger.error(f"[Error loading {file_path}]: {e}")
    
    return documents