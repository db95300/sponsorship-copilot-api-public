from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="COPILOT_",
        extra="ignore",
        env_file=".env",
    )

    env: str = "local"
    log_level: str = "INFO"
    database_url: str

    generation_mode: str = "template"  # "template" | "llm"
    llm_provider: str = "ollama"       # only "ollama" for now
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_temperature: float = 0.4


settings = Settings()