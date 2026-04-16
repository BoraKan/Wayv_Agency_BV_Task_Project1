import io
import logging
import os
import sys

# Model yuklenmeden once env degiskenlerini set et
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TQDM_DISABLE"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

from langchain_huggingface import HuggingFaceEmbeddings  # noqa: E402

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

_embedder_instance: HuggingFaceEmbeddings | None = None


def get_embedder() -> HuggingFaceEmbeddings:
    """
    Singleton embedder. Model sadece bir kez yuklenir.
    Yukleme sirasindaki tum ciktilar susturulur.
    """
    global _embedder_instance
    if _embedder_instance is None:
        old_stderr, old_stdout = sys.stderr, sys.stdout
        sys.stderr = sys.stdout = io.StringIO()
        try:
            _embedder_instance = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
        finally:
            sys.stderr = old_stderr
            sys.stdout = old_stdout
    return _embedder_instance
