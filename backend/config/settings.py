from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "Jarvis Engine"
    app_env: Literal["development", "production", "test"] = "development"
    app_port: int = Field(default=8000, ge=1, le=65535)
    app_host: str = "0.0.0.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:8080,http://localhost:5173"

    # LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    model_name: str = "gpt-4o-mini"
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    # Database & Cache
    database_url: str = "sqlite:///./data/app.db"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"

    # Vector Store
    chroma_persist_dir: str = "./data/chroma"

    # --- Agent (backend/core) -------------------------------------------- #
    # Which backend drives the tool-use loop: "anthropic" for the real API,
    # "openai_compat" for OpenAI / Ollama / Gemini-compat / proxy endpoints.
    llm_provider: str = Field(
        default="anthropic",
        validation_alias=AliasChoices("JARVIS_LLM_PROVIDER", "LLM_PROVIDER"),
    )
    agent_model: str = Field(
        default="claude-sonnet-5",
        validation_alias=AliasChoices("JARVIS_MODEL", "AGENT_MODEL"),
    )
    agent_max_tokens: int = Field(default=8192, ge=256, le=64000)
    agent_max_steps: int = Field(default=30, ge=1, le=200)
    bash_timeout: int = Field(default=120, ge=1, le=600)
    # Skips every permission prompt. Headless runs only -- the agent can then
    # write files and run shell commands with no human in the loop.
    auto_approve: bool = False
    anthropic_base_url: str = ""
    openai_base_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
