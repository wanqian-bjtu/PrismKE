"""Environment-backed application settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration with a PrismKE-specific environment prefix."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="PRISMKE_", extra="ignore")

    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str | None = None
    llm_model: str | None = None
    vlm_base_url: str = "https://api.openai.com/v1"
    vlm_api_key: str | None = None
    vlm_model: str | None = None
    vlm_timeout: float = 120.0
    vlm_max_image_edge: int = 2048
    ocr_device: str = "cpu"
    ocr_lang: str = "ch"
    ocr_model: str = "PP-OCRv5"
    allow_remote_assets: bool = False
    runtime_dir: Path = Path("runtime")
    request_timeout: float = 60.0

    @property
    def runs_dir(self) -> Path:
        return self.runtime_dir / "runs"

    @property
    def graph_dir(self) -> Path:
        return self.runtime_dir / "graph"

    @property
    def evidence_dir(self) -> Path:
        return self.runtime_dir / "evidence"

    @property
    def assets_dir(self) -> Path:
        return self.runtime_dir / "assets"

    @property
    def checkpoint_path(self) -> Path:
        return self.runtime_dir / "checkpoints.sqlite3"
