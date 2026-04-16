from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.embedder import get_embedder


COLLECTION_NAME = "rag_documents"
PERSIST_DIR = "./chroma_db"


def get_vector_store() -> Chroma:
    """Mevcut ChromaDB collection'ını döner (okuma/sorgu için)."""
    Path(PERSIST_DIR).mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embedder(),
        persist_directory=PERSIST_DIR,
    )


def rebuild_collection(documents: list[Document]) -> Chroma:
    """
    Collection'ı sıfırlayıp verilen dokümanları baştan ekler.
    Dosya değişikliği algılandığında kullanılır.
    """
    store = get_vector_store()
    try:
        store.delete_collection()
    except Exception:
        pass

    store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embedder(),
        persist_directory=PERSIST_DIR,
    )

    if documents:
        store.add_documents(documents)
    return store
