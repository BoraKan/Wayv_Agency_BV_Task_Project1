import pandas as pd
from langchain_core.documents import Document


def _humanize_column(col: str) -> str:
    """'aylik_fiyat_tl' -> 'Aylik Fiyat Tl'"""
    return col.replace("_", " ").strip().title()


def load_paket_fiyatlari(file_path: str) -> list[Document]:
    """
    CSV dosyasını satır bazında okur. Her satır için sütun başlıklarını
    değerlerle birleştirerek yapısal metin cümlesi üretir (tablo
    bağlamını kaybetmeden).

    Örnek: "Paket Adi: Pro | Aylik Fiyat Tl: 299 | ..."
    """
    df = pd.read_csv(file_path)
    docs: list[Document] = []

    for idx, row in df.iterrows():
        parts = []
        for col in df.columns:
            val = row[col]
            parts.append(f"{_humanize_column(col)}: {val}")
        content = " | ".join(parts)

        paket_adi = str(row.get("paket_adi", f"row_{idx}"))
        docs.append(
            Document(
                page_content=f"[Paket Bilgisi] {content}",
                metadata={
                    "source_file": "paket_fiyatlari.csv",
                    "chunk_type": "pricing_row",
                    "paket_adi": paket_adi,
                    "chunk_id": f"paket_{paket_adi.lower()}",
                },
            )
        )

    return docs
