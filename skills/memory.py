import chromadb
import ollama
import uuid

EMBEDDING_MODEL = "nomic-embed-text"
DB_PATH = "memory_db"
COLLECTION_NAME = "jarvis_memory"

_client = chromadb.PersistentClient(path=DB_PATH)
_collection = _client.get_or_create_collection(name=COLLECTION_NAME)


def _embed(text: str) -> list:
    """Converts text into a vector embedding using the local embedding model."""
    response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)
    return response["embedding"]


def add_memory(text: str) -> None:
    """Stores a new fact/memory permanently, so it can be recalled in future sessions."""
    embedding = _embed(text)
    memory_id = str(uuid.uuid4())

    _collection.add(
        documents=[text],
        embeddings=[embedding],
        ids=[memory_id]
    )
    print(f"[LOG] Memory stored: {text}")


def search_memory(query: str, n_results: int = 3) -> list:
    """Searches stored memories for the most relevant ones to the given query.
    Returns a list of matching memory text strings (may be empty)."""
    if _collection.count() == 0:
        return []

    query_embedding = _embed(query)

    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, _collection.count())
    )

    documents = results.get("documents", [[]])[0]
    return documents