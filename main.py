"""
Coklu Kaynak ve Metadata Destekli RAG Sistemi — CLI Arayuzu

Kullanim:
  python main.py                     # interaktif mod
  python main.py -q "Pro fiyat ne?"  # tek soru
  python main.py --debug             # alinan chunk'lari goster
  python main.py --reindex           # veriyi zorla yeniden indexle
"""
import logging
import os
import warnings

# Tum ucuncu parti logging'i ve uyarilari bastir
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TQDM_DISABLE"] = "1"
warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

import argparse
import sys
from typing import List

from langchain_core.documents import Document

from ingest import ingest
from src.rag_chain import build_chain


def format_debug_sources(docs: List[Document]) -> str:
    """Debug modunda retrieved chunk'lari gosterir."""
    lines = ["", "=" * 60, "[DEBUG] Retrieval sonuclari (oncelik sirasiyla):", "=" * 60]
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata or {}
        tag_parts = [meta.get("source_file", "?")]
        if meta.get("date"):
            tag_parts.append(f"tarih={meta['date']}")
        if meta.get("article_id"):
            tag_parts.append(f"madde={meta['article_id']}")
        if meta.get("paket_adi"):
            tag_parts.append(f"paket={meta['paket_adi']}")
        if meta.get("etkilenen_paket"):
            tag_parts.append(f"etkilenen={meta['etkilenen_paket']}")
        lines.append(f"  {i}. {' | '.join(tag_parts)}")
        preview = doc.page_content[:120].replace("\n", " ")
        lines.append(f"     \"{preview}...\"")
    lines.append("=" * 60)
    return "\n".join(lines)


def ask_once(chain, question: str, debug: bool = False) -> None:
    try:
        answer, docs = chain(question)
    except Exception as e:
        print(f"\n[HATA] {e}\n", file=sys.stderr)
        return

    if debug:
        print(format_debug_sources(docs))

    print()
    print(answer)
    print()


def interactive_loop(chain, debug: bool) -> None:
    print()
    print("=" * 60)
    print(" RAG Sistemi hazir. Sorularinizi yazin.")
    print(" Cikmak icin: 'cikis', 'exit' veya Ctrl+C")
    print("=" * 60)
    print()

    while True:
        try:
            question = input("Soru > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGorusuruz!")
            return

        if not question:
            continue
        if question.lower() in ("cikis", "çıkış", "exit", "quit", "q"):
            print("Gorusuruz!")
            return

        # Her sorguda hash kontrolu — dosya degistiyse otomatik re-index
        try:
            reindexed = ingest(force=False)
            if reindexed:
                chain = build_chain()
        except Exception as e:
            print(f"[UYARI] Re-index basarisiz: {e}", file=sys.stderr)

        ask_once(chain, question, debug=debug)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Coklu Kaynak ve Metadata Destekli RAG Sistemi"
    )
    parser.add_argument(
        "-q", "--soru",
        type=str,
        help="Tek bir soru sor ve cevabi bas, sonra cik."
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Veri dosyalarini zorla yeniden indexle."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Retrieval sonucu alinan chunk'lari goster."
    )
    args = parser.parse_args()

    # Hash kontrolu ile otomatik indexleme (veya --reindex ile zorla)
    try:
        ingest(force=args.reindex)
    except Exception as e:
        print(f"[HATA] Indexleme basarisiz: {e}", file=sys.stderr)
        sys.exit(1)

    # RAG chain'i kur
    try:
        chain = build_chain()
    except Exception as e:
        print(f"[HATA] LLM baglantisi kurulamadi: {e}", file=sys.stderr)
        sys.exit(1)

    if args.soru:
        ask_once(chain, args.soru, debug=args.debug)
    else:
        interactive_loop(chain, debug=args.debug)


if __name__ == "__main__":
    main()
