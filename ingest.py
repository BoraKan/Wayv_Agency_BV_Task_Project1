"""
Veri indexleme pipeline'i.

Kullanim:
  python ingest.py             # otomatik: hash degismisse yeniden indexle
  python ingest.py --force     # zorla yeniden indexle
"""
import sys
from pathlib import Path

from src.hash_check import check_data_changed, save_hashes
from src.loaders.csv_loader import load_paket_fiyatlari
from src.loaders.json_loader import load_guncellemeler
from src.loaders.txt_loader import load_sozlesme
from src.vector_store import rebuild_collection


DATA_DIR = Path("data")
HASH_FILE = "chroma_db/hashes.json"

SOZLESME_PATH = str(DATA_DIR / "sozlesme.txt")
CSV_PATH = str(DATA_DIR / "paket_fiyatlari.csv")
JSON_PATH = str(DATA_DIR / "guncellemeler.json")

DATA_FILES = [SOZLESME_PATH, CSV_PATH, JSON_PATH]


def ingest(force: bool = False) -> bool:
    """
    Veri dosyalarini kontrol eder, gerekirse yeniden indexler.

    Args:
        force: True ise hash fark etmese bile yeniden indexler.

    Returns:
        True => yeniden index yapildi, False => skip edildi.
    """
    changed, current_hashes = check_data_changed(DATA_FILES, HASH_FILE)

    if not changed and not force:
        return False

    all_docs = []
    all_docs.extend(load_sozlesme(SOZLESME_PATH))
    all_docs.extend(load_paket_fiyatlari(CSV_PATH))
    all_docs.extend(load_guncellemeler(JSON_PATH))

    rebuild_collection(all_docs)
    save_hashes(HASH_FILE, current_hashes)
    return True


if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    ingest(force=force_flag)
