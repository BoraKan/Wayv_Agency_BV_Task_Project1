from langchain_core.documents import Document

from src.vector_store import get_vector_store


SOURCE_PRIORITY = {
    "guncellemeler.json": 0,
    "sozlesme.txt": 1,
    "paket_fiyatlari.csv": 2,
}

# Her kaynaktan LLM'e gönderilecek maksimum chunk sayısı
SOURCE_CAP = {
    "guncellemeler.json": 3,
    "sozlesme.txt": 4,
    "paket_fiyatlari.csv": 2,
}


def _date_key(date_str: str) -> int:
    """'2024-06-01' -> 20240601. Boşsa 0."""
    if not date_str:
        return 0
    try:
        return int(date_str.replace("-", ""))
    except ValueError:
        return 0


def _sort_key(doc: Document):
    meta = doc.metadata or {}
    source = meta.get("source_file", "")
    priority = SOURCE_PRIORITY.get(source, 99)
    date_val = _date_key(meta.get("date", ""))
    return (priority, -date_val)


def retrieve(query: str, k: int = 6) -> list[Document]:
    """
    ChromaDB'de geniş bir similarity search (k*2) yapar, ardından:
      1. Her kaynaktan SOURCE_CAP kadar chunk alır (TXT'nin ezilmesini önler)
      2. Kaynak önceliği + tarih sırasına göre sıralar

    Sıralama:
      1. guncellemeler.json (en yeni tarih önce)
      2. sozlesme.txt
      3. paket_fiyatlari.csv
    """
    store = get_vector_store()

    # Tum chunk havuzunu cek (toplam ~22 chunk, performans etkisi yok)
    # Boylece hicbir kaynak similarity rekabetinde ezilmez
    candidates = store.similarity_search(query, k=50)

    # Her kaynaktan en fazla SOURCE_CAP kadar al
    per_source: dict[str, list[Document]] = {}
    for doc in candidates:
        source = (doc.metadata or {}).get("source_file", "unknown")
        bucket = per_source.setdefault(source, [])
        cap = SOURCE_CAP.get(source, 2)
        if len(bucket) < cap:
            bucket.append(doc)

    # Tüm kaynaklardan seçilenleri birleştir ve öncelik sırasına koy
    selected = [doc for docs in per_source.values() for doc in docs]
    selected.sort(key=_sort_key)
    return selected
