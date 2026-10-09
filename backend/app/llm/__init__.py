from app.config import settings


def get_provider():
    if settings.llm_provider == "gemini":
        from app.llm.gemini import GeminiProvider

        return GeminiProvider()
    if settings.llm_provider == "ollama":
        from app.llm.ollama import OllamaProvider

        return OllamaProvider()
    raise ValueError(f"unknown LLM_PROVIDER {settings.llm_provider!r} (use ollama or gemini)")
