import hashlib
import json
from pathlib import Path


def compute_file_hash(file_path: str) -> str:
    """Dosyanın MD5 hash'ini hesaplar."""
    return hashlib.md5(Path(file_path).read_bytes()).hexdigest()


def load_hashes(hash_file: str) -> dict:
    """Kayıtlı hash dosyasını okur. Yoksa boş dict döner."""
    path = Path(hash_file)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_hashes(hash_file: str, hashes: dict) -> None:
    """Hash dosyasını diske kaydeder."""
    path = Path(hash_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(hashes, indent=2, ensure_ascii=False), encoding="utf-8")


def check_data_changed(data_files: list[str], hash_file: str) -> tuple[bool, dict]:
    """
    Veri dosyalarının değişip değişmediğini kontrol eder.

    Returns:
        (changed, current_hashes) — changed True ise re-index gerekli.
    """
    current: dict[str, str] = {}
    for f in data_files:
        p = Path(f)
        if p.exists():
            current[p.name] = compute_file_hash(f)

    saved = load_hashes(hash_file)
    return current != saved, current
