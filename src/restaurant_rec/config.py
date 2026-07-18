from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to the project's .env so it loads regardless of the process's
# working directory (uvicorn, pytest, and ad-hoc scripts all start elsewhere).
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Restaurant Recommendation API", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    # LLM provider
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    llm_model: str = Field(default="gemini-flash-latest", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.3, ge=0.0, le=2.0, alias="LLM_TEMPERATURE")
    llm_timeout_seconds: int = Field(default=30, ge=1, alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=3, ge=0, alias="LLM_MAX_RETRIES")
    # Cap on the model's JSON reply. Big enough for top_k picks + summary, small
    # enough to stay cheap and avoid runaway output. Prevents truncated JSON.
    llm_max_output_tokens: int = Field(
        default=2048, ge=256, alias="LLM_MAX_OUTPUT_TOKENS"
    )

    # Recommendation pipeline
    min_candidates: int = Field(default=10, ge=1, alias="MIN_CANDIDATES")
    max_candidates: int = Field(default=50, ge=1, alias="MAX_CANDIDATES")
    default_top_k: int = Field(default=5, ge=1, le=10, alias="DEFAULT_TOP_K")

    # Dataset
    hf_dataset_name: str = Field(
        default="ManikaSaini/zomato-restaurant-recommendation",
        alias="HF_DATASET_NAME",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
