import json
from pathlib import Path
from langchain_core.documents import Document


def load_guncellemeler(file_path: str) -> list[Document]:
    """
    guncellemeler.json dosyasındaki her log kaydını bağımsız bir chunk'a çevirir.
    Tarih metadata olarak saklanır (çakışma çözümünde kritik).
    """
    data = json.loads(Path(file_path).read_text(encoding="utf-8"))
    docs: list[Document] = []

    for idx, entry in enumerate(data):
        tarih = entry.get("tarih", "")
        etkilenen_paket = entry.get("etkilenen_paket", "")
        etkilenen_madde = entry.get("etkilenen_madde", "")
        degisiklik = entry.get("degisiklik", "")

        content = (
            f"[Guncelleme Kaydi] "
            f"Tarih: {tarih} | "
            f"Etkilenen Paket: {etkilenen_paket} | "
            f"Etkilenen Madde: {etkilenen_madde} | "
            f"Degisiklik: {degisiklik}"
        )

        docs.append(
            Document(
                page_content=content,
                metadata={
                    "source_file": "guncellemeler.json",
                    "chunk_type": "update_log",
                    "date": tarih,
                    "etkilenen_paket": etkilenen_paket,
                    "etkilenen_madde": etkilenen_madde,
                    "chunk_id": f"guncelleme_{idx}_{tarih}",
                },
            )
        )

    return docs
