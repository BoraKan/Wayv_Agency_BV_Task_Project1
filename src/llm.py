import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv()


def get_llm() -> ChatOpenAI:
    """
    LLM istemcisi döner. Önce OPENAI_API_KEY, yoksa OPENROUTER_API_KEY kontrol eder.

    OpenAI:    OPENAI_API_KEY    + OPENAI_MODEL    (opsiyonel, default: gpt-4o)
    OpenRouter: OPENROUTER_API_KEY + OPENROUTER_MODEL (opsiyonel, default: openai/gpt-4o)
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if openai_key:
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            api_key=openai_key,
            temperature=0.1,
        )

    if openrouter_key:
        return ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o"),
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.1,
            default_headers={
                "HTTP-Referer": "https://github.com/wayv-agency/rag-project",
                "X-Title": "Wayv RAG Project",
            },
        )

    raise RuntimeError(
        "Hic API anahtari bulunamadi.\n"
        "  OpenAI icin:     OPENAI_API_KEY=sk-...\n"
        "  OpenRouter icin: OPENROUTER_API_KEY=sk-or-v1-...\n"
        ".env dosyasina ekleyin."
    )
