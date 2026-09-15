"""Environment-backed application settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration with a PrismKE-specific environment prefix."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="PRISMKE_", extra="ignore"
    )

    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str | None = None
    llm_model: str | None = None
    runtime_dir: Path = Path("runtime")
    request_timeout: float = 60.0

    @property
    def runs_dir(self) -> Path:
        return self.runtime_dir / "runs"

    @property
    def graph_dir(self) -> Path:
        return self.runtime_dir / "graph"

    @property
    def checkpoint_path(self) -> Path:
        return self.runtime_dir / "checkpoints.sqlite3"
