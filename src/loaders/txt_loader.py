import re
from pathlib import Path
from langchain_core.documents import Document


MADDE_PATTERN = re.compile(r"^Madde\s+(\d+(?:\.\d+)?)", re.IGNORECASE)


def load_sozlesme(file_path: str) -> list[Document]:
    """
    sozlesme.txt'i madde bazında bölerek Document listesine çevirir.
    Her madde (örn. "Madde 4.1: ...") bağımsız bir chunk olur.
    """
    text = Path(file_path).read_text(encoding="utf-8")
    sections = [s.strip() for s in text.split("\n\n") if s.strip()]

    docs: list[Document] = []
    for idx, section in enumerate(sections):
        first_line = section.split("\n", 1)[0]
        match = MADDE_PATTERN.match(first_line)

        if match:
            article_id = match.group(1)
            chunk_id = f"sozlesme_madde_{article_id}"
        else:
            article_id = ""
            chunk_id = f"sozlesme_bolum_{idx}"

        docs.append(
            Document(
                page_content=section,
                metadata={
                    "source_file": "sozlesme.txt",
                    "chunk_type": "contract_article",
                    "article_id": article_id,
                    "chunk_id": chunk_id,
                },
            )
        )

    return docs
