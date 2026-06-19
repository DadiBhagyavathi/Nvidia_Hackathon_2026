from pathlib import Path
from typing import List

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    NVIDIA_API_KEY: str | None = Field(None, env="NVIDIA_API_KEY")
    NVIDIA_BASE_URL: str = Field(
        "https://integrate.api.nvidia.com/v1",
        env="NVIDIA_BASE_URL",
    )
    NIM_MODEL: str = Field(
        "nvidia/llama-3.1-nemotron-70b-instruct",
        env="NIM_MODEL",
    )

    SUPABASE_URL: str | None = Field(None, env="SUPABASE_URL")
    SUPABASE_KEY: str | None = Field(None, env="SUPABASE_KEY")

    CHROMA_DIR: Path = Field(Path("backend/rag/chroma_db"), env="CHROMA_DIR")
    EMBED_MODEL: str = Field("all-MiniLM-L6-v2", env="EMBED_MODEL")
    MODEL_PATH: Path = Field(Path("backend/ml/fraud_model.pkl"), env="MODEL_PATH")

    ALLOWED_ORIGINS: List[str] = Field(
        ["http://localhost:3000"],
        env="ALLOWED_ORIGINS",
    )
    PAYSIM_CSV: Path = Field(Path("data/paysim.csv"), env="PAYSIM_CSV")

    @validator("ALLOWED_ORIGINS", pre=True)
    def split_origins(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    def missing_environment(self) -> List[str]:
        missing = []
        if not self.NVIDIA_API_KEY:
            missing.append("NVIDIA_API_KEY")
        if not self.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not self.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        return missing

    @property
    def is_nim_configured(self) -> bool:
        return bool(self.NVIDIA_API_KEY)

    @property
    def is_supabase_configured(self) -> bool:
        return bool(self.SUPABASE_URL and self.SUPABASE_KEY)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
