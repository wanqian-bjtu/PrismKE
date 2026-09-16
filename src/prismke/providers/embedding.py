"""Local dense embedding providers used by entity resolution."""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

from prismke.core.ids import canonical_hash


class DisabledEmbeddingProvider:
    def fingerprint(self) -> str:
        return "embedding:disabled"

    async def encode(self, texts: list[str]) -> list[list[float]]:
        if texts:
            raise RuntimeError("embedding provider is disabled")
        return []


class MockEmbeddingProvider:
    """Deterministic low-dimensional vectors for offline tests."""

    dimension = 32

    def fingerprint(self) -> str:
        return "embedding:mock:v1:32"

    async def encode(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    @classmethod
    def _vector(cls, text: str) -> list[float]:
        vector = [0.0] * cls.dimension
        normalized = " ".join(text.casefold().split())
        tokens = normalized.split() or [normalized]
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for index, value in enumerate(digest):
                slot = index % cls.dimension
                vector[slot] += (value / 127.5) - 1.0
        norm = math.sqrt(sum(item * item for item in vector)) or 1.0
        return [item / norm for item in vector]


class BGEM3EmbeddingProvider:
    """Lazy, cached BGE-M3 dense encoder."""

    dimension = 1024

    def __init__(
        self,
        model_name: str,
        device: str,
        use_fp16: bool,
        batch_size: int,
        max_tokens: int,
        cache_dir: Path,
        model_cache_dir: Path,
        allow_download: bool = False,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.use_fp16 = use_fp16
        self.batch_size = batch_size
        self.max_tokens = max_tokens
        self.cache_dir = cache_dir
        self.model_cache_dir = model_cache_dir
        self.allow_download = allow_download
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
        self._model: Any | None = None
        self._lock = asyncio.Lock()

    def fingerprint(self) -> str:
        return canonical_hash(
            {
                "provider": "bge-m3",
                "model": self.model_name,
                "dimension": self.dimension,
                "max_tokens": self.max_tokens,
                "implementation": "v1",
            }
        )

    def _cache_path(self, text: str) -> Path:
        key = canonical_hash({"fingerprint": self.fingerprint(), "text": text})
        return self.cache_dir / key[:2] / f"{key}.json"

    def _load_model(self) -> Any:
        if self._model is None:
            os.environ.setdefault("HF_HOME", str(self.model_cache_dir.resolve()))
            try:
                from FlagEmbedding import BGEM3FlagModel
                from huggingface_hub import snapshot_download
                from huggingface_hub.errors import LocalEntryNotFoundError
            except ImportError as exc:
                raise RuntimeError(
                    "BGE-M3 is not installed; run `uv sync --extra embedding`"
                ) from exc
            model_path = Path(self.model_name)
            try:
                resolved_model = (
                    str(model_path)
                    if model_path.exists()
                    else snapshot_download(
                        repo_id=self.model_name,
                        cache_dir=self.model_cache_dir / "hub",
                        local_files_only=not self.allow_download,
                    )
                )
            except LocalEntryNotFoundError as exc:
                raise RuntimeError(
                    "BGE-M3 model is not prepared; run "
                    "`prismke prepare-model --embedding BAAI/bge-m3`"
                ) from exc
            self._model = BGEM3FlagModel(
                resolved_model,
                use_fp16=self.use_fp16,
                devices=[self.device],
            )
        return self._model

    def _encode_missing(self, texts: list[str]) -> list[list[float]]:
        model = self._load_model()
        result = model.encode(
            texts,
            batch_size=self.batch_size,
            max_length=self.max_tokens,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )
        vectors = result["dense_vecs"]
        return [[float(value) for value in vector] for vector in vectors]

    async def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        async with self._lock:
            output: list[list[float] | None] = [None] * len(texts)
            missing_texts: list[str] = []
            missing_indexes: list[int] = []
            for index, text in enumerate(texts):
                path = self._cache_path(text)
                if path.is_file():
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    vector = [float(value) for value in payload["vector"]]
                    if len(vector) == self.dimension:
                        output[index] = vector
                        continue
                missing_texts.append(text)
                missing_indexes.append(index)
            if missing_texts:
                vectors = await asyncio.to_thread(self._encode_missing, missing_texts)
                for index, text, vector in zip(
                    missing_indexes, missing_texts, vectors, strict=True
                ):
                    if len(vector) != self.dimension:
                        raise ValueError(
                            f"BGE-M3 returned dimension {len(vector)}, expected {self.dimension}"
                        )
                    path = self._cache_path(text)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(
                        json.dumps({"vector": vector}, separators=(",", ":")),
                        encoding="utf-8",
                    )
                    output[index] = vector
            return [vector for vector in output if vector is not None]
