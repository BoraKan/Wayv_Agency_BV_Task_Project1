import re

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.llm import get_llm
from src.retriever import retrieve


SYSTEM_PROMPT = """Sen bir sirket bilgi asistanisin. Kullanicinin sorularini SADECE
sana verilen BAGLAM bolumundeki bilgilere dayanarak cevaplayacaksin.

ONEMLI KURALLAR:

1. COKLU KAYNAK & CAKISMA COZUMU:
   - "guncellemeler.json" kaynagi en guncel bilgiyi tasir.
   - Eger bir konuda hem "sozlesme.txt"/"paket_fiyatlari.csv" hem de
     "guncellemeler.json" bilgi veriyorsa, JSON icindeki EN YUKSEK tarihli kaydi
     esas al. Eski bilgiyi cevabinda tekrar etme.

2. INLINE ATIF ZORUNLU:
   Her bilgiyi kullanirken, o bilginin kaynak numarasini cumlenin SONUNA [N] ekle.
   Birden fazla kaynaktan geliyorsa hepsini ekle: [2][5]
   Ayri bir "Kaynaklar" bolumu EKLEME — sadece inline atiflar yeterli.

   Ornek:
   Pro paket fiyati 299 TL'dir.[3] Iptal icin yazili bildirim gerekir.[1]
   Iade suresi Pro paketi icin 30 gundur.[5]

3. KAPSAMLI CEVAP:
   Iptal veya iade sorusu varsa mutlaka su 3 bilgiyi ver:
   a) Guncel iade suresi (JSON'dan en yeni guncelleme) [N]
   b) Iptal nasil yapilir — yontem ve adres (sozlesmeden) [N]
   c) Para ne zaman geri gelir — isleme suresi [N]

4. DIL & STIL:
   - Cevaplarini Turkce ver, dogal ve anlasilir yaz.
   - Hukuki jargonu sadelestir.

5. BILMEDIGINI SOYLE:
   Baglamda olmayan bilgileri UYDURMA.

BAGLAM:
{context}
"""

USER_TEMPLATE = "Soru: {question}"


def format_context(docs: list[Document]) -> str:
    """Retrieved chunk'ları numaralı bağlam metnine çevirir."""
    if not docs:
        return "(Baglamda hic dokuman bulunamadi.)"

    parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata or {}
        header_parts = [f"[Kaynak {i}] dosya={meta.get('source_file', '?')}"]

        if meta.get("date"):
            header_parts.append(f"tarih={meta['date']}")
        if meta.get("article_id"):
            header_parts.append(f"madde={meta['article_id']}")
        if meta.get("etkilenen_madde"):
            header_parts.append(f"etkilenen_madde={meta['etkilenen_madde']}")
        if meta.get("paket_adi"):
            header_parts.append(f"paket={meta['paket_adi']}")
        if meta.get("etkilenen_paket"):
            header_parts.append(f"etkilenen_paket={meta['etkilenen_paket']}")

        parts.append(" | ".join(header_parts) + "\n" + doc.page_content)

    return "\n\n".join(parts)


def parse_inline_citations(text: str, total_docs: int) -> tuple[str, list[int]]:
    """
    Cevap metnindeki [N] atıflarını çıkarsır.
    - Kullanılan kaynak indekslerini (0-tabanlı, sıralı, tekrarsız) döner.
    - [N] etiketlerini metinden temizler.
    - Hiç atıf yoksa fallback: boş liste (kaynak yok).
    """
    pattern = re.compile(r"\[(\d+)\]")
    indices: list[int] = []
    seen: set[int] = set()

    for match in pattern.finditer(text):
        n = int(match.group(1))
        idx = n - 1
        if 0 <= idx < total_docs and idx not in seen:
            indices.append(idx)
            seen.add(idx)

    clean = pattern.sub("", text)
    clean = re.sub(r" {2,}", " ", clean).strip()

    return clean, indices


def format_sources(docs: list[Document]) -> str:
    """Kullanılan dökümanlardan kaynak bölümü oluşturur."""
    if not docs:
        return ""
    lines = ["\n---\nKaynaklar:"]
    for doc in docs:
        meta = doc.metadata or {}
        parts = [meta.get("source_file", "?")]
        if meta.get("date"):
            parts.append(meta["date"])
        if meta.get("article_id"):
            parts.append(f"madde {meta['article_id']}")
        if meta.get("paket_adi"):
            parts.append(meta["paket_adi"])
        if meta.get("etkilenen_paket"):
            parts.append(meta["etkilenen_paket"])
        lines.append("• " + " | ".join(parts))
    return "\n".join(lines)


def build_chain():
    """
    Retrieval + Generation pipeline'ı kurar.
    Döndürülen callable: question (str) -> (answer: str, docs: list[Document])
    """
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), ("user", USER_TEMPLATE)]
    )
    chain = prompt | llm | StrOutputParser()

    def run(question: str) -> tuple[str, list[Document]]:
        docs = retrieve(question, k=6)
        context = format_context(docs)
        raw = chain.invoke({"context": context, "question": question})

        answer_text, used_indices = parse_inline_citations(raw, len(docs))
        used_docs = [docs[i] for i in used_indices]
        sources = format_sources(used_docs)
        return answer_text + sources, used_docs

    return run
