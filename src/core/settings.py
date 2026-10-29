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
    ocr_device: str = "auto"
    ocr_lang: str = "mixed"
    ocr_model: str = "PP-OCRv5"
    allow_remote_assets: bool = False
    runtime_dir: Path = Path("runtime")
    request_timeout: float = 60.0
    graph_store: str = "json"
    neo4j_uri: str = "bolt://127.0.0.1:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str | None = None
    neo4j_database: str = "neo4j"
    api_token: str | None = None
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    embedding_provider: str = "disabled"
    embedding_model: str = "BAAI/bge-m3"
    embedding_model_revision: str = "5617a9f61b028005a4858fdac845db406aefb181"
    embedding_device: str = "cuda:0"
    embedding_use_fp16: bool = True
    embedding_batch_size: int = 32
    embedding_max_tokens: int = 512
    embedding_model_cache: Path | None = None
    embedding_allow_download: bool = False
    entity_top_k: int = 10
    entity_auto_link_threshold: float = 0.88
    entity_review_threshold: float = 0.65
    entity_min_margin: float = 0.08
    case_top_k: int = 5
    reflection_provider: str = "disabled"
    reflection_max_attempts: int = 2
    reflection_token_budget: int = 20_000
    reflection_time_budget_seconds: float = 180.0
    agent_token_budget: int = 20_000
    libreoffice_bin: Path | None = None
    document_conversion_timeout_seconds: int = 120
    max_batch_files: int = 20
    max_file_bytes: int = 200 * 1024 * 1024
    max_batch_bytes: int = 500 * 1024 * 1024
    max_archive_entries: int = 1000
    max_archive_compression_ratio: float = 200.0
    pdf_parse_mode: str = "auto"
    pdf_no_text_ratio: float = 0.15
    pdf_short_text_chars: int = 80
    pdf_short_text_ratio: float = 0.30
    pdf_table_ratio: float = 0.10
    pdf_drawing_count: int = 5
    pdf_drawing_ratio: float = 0.20
    pdf_multicolumn_ratio: float = 0.20
    mineru_base_url: str = "http://127.0.0.1:18020"
    mineru_version: str = "4.0.12"
    mineru_tier: str = "standard"
    mineru_request_timeout: float = 60.0
    mineru_transfer_timeout: float = 300.0
    mineru_poll_interval: float = 2.0
    mineru_max_polls: int = 300

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

    @property
    def uploads_dir(self) -> Path:
        return self.runtime_dir / "uploads"

    @property
    def audit_path(self) -> Path:
        return self.runtime_dir / "audit.jsonl"

    @property
    def embedding_cache_dir(self) -> Path:
        return self.runtime_dir / "embeddings"

    @property
    def embedding_model_cache_dir(self) -> Path:
        return self.embedding_model_cache or self.runtime_dir / "models" / "huggingface"

    @property
    def entity_governance_path(self) -> Path:
        return self.runtime_dir / "entity-governance.json"

    @property
    def cases_path(self) -> Path:
        return self.runtime_dir / "cases.sqlite"

    @property
    def batches_dir(self) -> Path:
        return self.runtime_dir / "batches"

    @property
    def derived_documents_dir(self) -> Path:
        return self.runtime_dir / "derived-documents"

    @property
    def mineru_runtime_dir(self) -> Path:
        return self.runtime_dir / "mineru"
