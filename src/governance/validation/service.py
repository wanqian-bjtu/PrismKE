"""Validation does not repair facts or invoke models."""

from __future__ import annotations

import math
from collections.abc import Iterable
from io import BytesIO
from typing import Any

import pymupdf
from PIL import Image

from src.core.errors import GraphIntegrityError, SchemaValidationError
from src.core.ids import canonical_hash, stable_id
from src.domain import (
    CandidateClaim,
    CanonicalEntity,
    DocumentIR,
    EntityMention,
    EvidenceRef,
    GraphCommit,
    SchemaIndex,
    ValidationIssue,
    ValidationResult,
)
from src.governance.claim_normalization import normalize_claims
from src.persistence.base import EvidenceStore


class ValidationService:
    @staticmethod
    def blocked_candidate_ids(
        candidates: list[CandidateClaim], result: ValidationResult
    ) -> set[str]:
        targets = {
            i.target_id for i in result.issues if i.severity == "blocking" and i.status == "open"
        }
        return {
            c.id
            for c in candidates
            if c.id in targets or targets.intersection(c.visual_observation_ids)
        }

    @staticmethod
    async def physical_location_error(ref: EvidenceRef, store: EvidenceStore) -> str | None:
        content = await store.get_blob(ref.source_hash)
        if ref.bbox is not None:
            if ref.coordinate_space == "pdf_points":
                with pymupdf.open(stream=content, filetype="pdf") as pdf:  # type: ignore[no-untyped-call]
                    if ref.page_number is None or not 1 <= ref.page_number <= len(pdf):
                        return "PDF 页码不存在"
                    page = pdf[ref.page_number - 1]
                    width, height = float(page.rect.width), float(page.rect.height)
            else:
                with Image.open(BytesIO(content)) as image:
                    width, height = image.size
            if ref.canvas_width != width or ref.canvas_height != height:
                return "画布尺寸与原始证据不一致"
        if ref.char_end is not None and ref.char_end > len(
            content.decode("utf-8", errors="replace")
        ):
            return "字符范围超出证据内容"
        return None

    @staticmethod
    def issue(
        code: str,
        stage: Any,
        target_type: Any,
        target_id: str,
        field_path: str,
        message: str,
        evidence_ids: list[str] | None = None,
        summary: dict[str, Any] | None = None,
    ) -> ValidationIssue:
        return ValidationIssue(
            id=stable_id("validation", code, stage, target_type, target_id, field_path),
            code=code,
            stage=stage,
            target_type=target_type,
            target_id=target_id,
            field_path=field_path,
            message=message,
            evidence_ids=evidence_ids or [],
            candidate_summary=summary or {},
        )

    @staticmethod
    def merge(
        previous: ValidationResult,
        issues: Iterable[ValidationIssue],
        fingerprint: str = "",
        passed_count: int = 0,
    ) -> ValidationResult:
        merged = {item.id: item for item in previous.issues}
        for item in issues:
            if item.id not in merged:
                merged[item.id] = item
        values = list(merged.values())
        return ValidationResult(
            input_fingerprint=fingerprint or previous.input_fingerprint,
            issues=values,
            passed_count=passed_count,
            blocking_count=sum(i.severity == "blocking" and i.status == "open" for i in values),
        )

    @staticmethod
    def location_error(ref: EvidenceRef, document: DocumentIR | None = None) -> str | None:
        if (ref.char_start is None) != (ref.char_end is None):
            return "字符范围缺少起点或终点"
        if (
            ref.char_start is not None
            and ref.char_end is not None
            and (ref.char_start < 0 or ref.char_end <= ref.char_start)
        ):
            return "字符范围非法"
        if ref.page_number is not None and ref.page_number < 1:
            return "页码必须从 1 开始"
        if document is not None:
            if ref.document_id != document.id:
                return "证据文档引用不匹配"
            if ref.media_asset_id and ref.media_asset_id not in {
                a.id for a in document.media_assets
            }:
                return "证据引用的视觉资产不存在"
            if (
                document.pages
                and ref.page_number is not None
                and ref.page_number not in {p.page_number for p in document.pages}
            ):
                return "证据页码超出文档范围"
            if ref.char_start is not None:
                blocks = [b for b in document.text_blocks if b.evidence_id == ref.id]
                if not blocks or any(
                    b.char_start != ref.char_start or b.char_end != ref.char_end for b in blocks
                ):
                    return "字符范围与文本块不匹配"
        if ref.bbox is not None:
            b = ref.bbox
            if not all(math.isfinite(v) for v in (b.x0, b.y0, b.x1, b.y1)):
                return "区域坐标不是有限数值"
            if (
                ref.coordinate_space is None
                or ref.canvas_width is None
                or ref.canvas_height is None
            ):
                return "区域证据缺少坐标系或画布尺寸"
            width, height = (
                (1.0, 1.0)
                if ref.coordinate_space == "normalized"
                else (ref.canvas_width, ref.canvas_height)
            )
            if not (0 <= b.x0 < b.x1 <= width and 0 <= b.y0 < b.y1 <= height):
                return "区域坐标超出画布范围"
        return None

    async def candidates(
        self,
        candidates: list[CandidateClaim],
        schema: SchemaIndex,
        document: DocumentIR,
        evidence_store: EvidenceStore,
        entities: dict[str, CanonicalEntity] | None = None,
        mention_map: dict[str, str] | None = None,
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        refs = {r.id: r for r in document.evidence}
        type_ids = {t.id for t in schema.schema.entity_types}
        for c in candidates:

            def add(code: str, stage: Any, field: str, message: str, c: CandidateClaim = c) -> None:
                issues.append(
                    self.issue(
                        code,
                        stage,
                        "candidate",
                        c.id,
                        field,
                        message,
                        c.evidence_ids,
                        {
                            "subject": c.subject.name,
                            "relation": c.relation,
                            "object": (
                                c.object.name if isinstance(c.object, EntityMention) else c.object
                            ),
                        },
                    )
                )

            mentions = [c.subject] + ([c.object] if isinstance(c.object, EntityMention) else [])
            for mention in mentions:
                if not set(mention.evidence_ids) <= refs.keys():
                    add("UNKNOWN_EVIDENCE", "reference", "mention.evidence_ids", "提及引用未知证据")
            if not set(c.visual_observation_ids) <= {o.id for o in document.visual_observations}:
                add(
                    "UNKNOWN_OBSERVATION",
                    "reference",
                    "visual_observation_ids",
                    "候选引用未知视觉观察",
                )
            for mention in mentions:
                normalized = schema.entity_type(mention.entity_type)
                if normalized not in type_ids:
                    add(
                        "UNKNOWN_ENTITY_TYPE", "schema", "entity_type", "实体类型未在 Schema 中声明"
                    )
            if schema.relation(c.relation) is None:
                add("UNKNOWN_RELATION", "schema", "relation", "关系未声明，宽松模式也不允许写图")
            relation = schema.relation(c.relation)
            if relation and relation.domain:
                subject_type = schema.entity_type(c.subject.entity_type)
                if subject_type not in relation.domain:
                    add(
                        "SCHEMA_DOMAIN_RANGE",
                        "schema",
                        "subject.entity_type",
                        "主语类型不满足关系 domain 约束",
                    )
            if relation and relation.range and isinstance(c.object, EntityMention):
                object_type = schema.entity_type(c.object.entity_type)
                if object_type not in relation.range:
                    add(
                        "SCHEMA_DOMAIN_RANGE",
                        "schema",
                        "object.entity_type",
                        "宾语类型不满足关系 range 约束",
                    )
            if relation and relation.range and not isinstance(c.object, EntityMention):
                add(
                    "SCHEMA_DOMAIN_RANGE",
                    "schema",
                    "object",
                    "关系要求实体型宾语，不能使用文字值替代",
                )
            if not c.evidence_ids:
                add("MISSING_EVIDENCE", "evidence", "evidence_ids", "候选缺少证据")
            for eid in c.evidence_ids:
                if eid not in refs:
                    add("UNKNOWN_EVIDENCE", "reference", "evidence_ids", "候选引用未知证据")
                    continue
                ref = refs[eid]
                if not await evidence_store.exists(eid):
                    add("MISSING_EVIDENCE", "evidence", "evidence_ids", "证据文件不存在")
                elif not await evidence_store.verify(eid):
                    add("CORRUPT_EVIDENCE", "evidence", "evidence_ids", "证据完整性校验失败")
                elif await evidence_store.get(eid) != ref:
                    add(
                        "EVIDENCE_REF_MISMATCH",
                        "evidence",
                        "evidence_ids",
                        "运行证据与存储记录不一致",
                    )
                location = self.location_error(ref, document)
                if location:
                    add("INVALID_EVIDENCE_LOCATION", "evidence", "evidence_ids", location)
            if entities is not None and mention_map is not None:
                if any(
                    m.id not in mention_map or mention_map[m.id] not in entities for m in mentions
                ):
                    add(
                        "MISSING_ENTITY_REFERENCE",
                        "reference",
                        "mention_to_entity",
                        "提及未映射到规范实体",
                    )
                elif schema.relation(c.relation) is not None:
                    try:
                        normalize_claims([c], schema, entities, mention_map)
                    except SchemaValidationError:
                        add(
                            "SCHEMA_DOMAIN_RANGE",
                            "schema",
                            "relation",
                            "关系方向或 domain/range 与实体类型不匹配",
                        )
        return issues

    async def commit(
        self,
        transaction: GraphCommit,
        entities: dict[str, CanonicalEntity],
        evidence: dict[str, EvidenceRef],
        document_ids: set[str],
        evidence_store: EvidenceStore | None,
    ) -> None:
        context = transaction.validation_context
        failures: list[str] = []
        active = [c for c in transaction.claims if c.tx_to is None]
        if active and (context is None or context.policy_version != "validation-v1"):
            raise GraphIntegrityError("MISSING_SCHEMA_CONTEXT: 活动事实提交必须提供校验上下文")
        for claim in active:
            assert context is not None
            sid = context.claim_schema_ids.get(claim.id)
            output_schema = context.schemas.get(sid or "")
            if output_schema is None or sid != canonical_hash(
                output_schema.model_dump(mode="json")
            ):
                failures.append("MISSING_SCHEMA_CONTEXT")
                continue
            index = SchemaIndex(output_schema)
            relation = index.relation_by_id(claim.relation_id)
            subject = entities.get(claim.subject_id)
            obj = entities.get(claim.object_entity_id or "")
            known_types = {t.id for t in output_schema.entity_types}
            if relation is None:
                failures.append("UNKNOWN_RELATION")
            if (
                subject is None
                or not subject.active
                or (claim.object_entity_id and (obj is None or not obj.active))
            ):
                failures.append("MISSING_ENTITY_REFERENCE")
            if (
                subject
                and subject.entity_type not in known_types
                or obj
                and obj.entity_type not in known_types
            ):
                failures.append("UNKNOWN_ENTITY_TYPE")
            if (
                relation
                and subject
                and relation.domain
                and subject.entity_type not in relation.domain
            ):
                failures.append("SCHEMA_DOMAIN_RANGE")
            if (
                relation
                and relation.range
                and (obj is None or obj.entity_type not in relation.range)
            ):
                failures.append("SCHEMA_DOMAIN_RANGE")
            if not claim.evidence_ids:
                failures.append("MISSING_EVIDENCE")
            for eid in claim.evidence_ids:
                ref = evidence.get(eid)
                if ref is None or ref.document_id not in document_ids:
                    failures.append("UNKNOWN_EVIDENCE")
                elif evidence_store is None:
                    failures.append("EVIDENCE_STORE_UNAVAILABLE")
                elif not await evidence_store.verify(eid) or await evidence_store.get(eid) != ref:
                    failures.append("CORRUPT_EVIDENCE")
                elif self.location_error(ref):
                    failures.append("INVALID_EVIDENCE_LOCATION")
                elif (
                    ref.media_asset_id
                    and ref.media_asset_id
                    not in context.document_asset_ids.get(ref.document_id, [])
                ):
                    failures.append("UNKNOWN_MEDIA_ASSET")
                elif await self.physical_location_error(ref, evidence_store):
                    failures.append("INVALID_EVIDENCE_LOCATION")
        if failures:
            codes = ",".join(sorted(set(failures)))
            raise GraphIntegrityError(f"{codes}: 提交硬校验失败（{len(failures)} 项）")
