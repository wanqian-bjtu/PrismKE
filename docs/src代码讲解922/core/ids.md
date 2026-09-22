源码：[ids.py:1](../../../src/core/ids.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：3

**模块职责**：Stable content-derived identifiers and fingerprints.
**在系统中的位置**：全局设置、稳定标识、执行控制与错误类型；为其他层提供通用约束。
**直接依赖**：无显式项目内模块导入；外部/标准库：`__future__`、`hashlib`、`orjson`、`pathlib`、`typing`。
**主要调用方（静态导入）**：[agents/entity_governance_agent.py](../agents/entity_governance_agent.md)、[agents/fusion_review_agent.py](../agents/fusion_review_agent.md)、[agents/multimodal_extraction_agent.py](../agents/multimodal_extraction_agent.md)、[agents/trace.py](../agents/trace.md)、[evaluation/document_validation.py](../evaluation/document_validation.md)、[evaluation/reflection.py](../evaluation/reflection.md)、[governance/alignment.py](../governance/alignment.md)、[governance/claim_normalization.py](../governance/claim_normalization.md)、[governance/conflicts.py](../governance/conflicts.md)、[governance/entity_index.py](../governance/entity_index.md)、[governance/entity_operations.py](../governance/entity_operations.md)、[governance/entity_resolution.py](../governance/entity_resolution.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# stable_id ⭐⭐

**位置与等级**：[ids.py:12](../../../src/core/ids.py#L12)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def stable_id(prefix: str, *parts: object) -> str`。

**作用**：处理 `stable_id` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`prefix`（str）；`parts`（object）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `normalized`，值来自 `<字符串常量>.join((str(part).strip() for part in parts))`。
2. 返回 `f<字符串常量>utf-8<字符串常量>`。

**调用与被调用**：
- `<字符串常量>.join`（[ids.py:13](../../../src/core/ids.py#L13)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str(part).strip`（[ids.py:13](../../../src/core/ids.py#L13)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[ids.py:13](../../../src/core/ids.py#L13)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sha256(normalized.encode('utf-8')).hexdigest`（[ids.py:14](../../../src/core/ids.py#L14)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sha256`（[ids.py:14](../../../src/core/ids.py#L14)）：来自 `hashlib.sha256`；具体实现可能由依赖注入或运行时分派决定。
- `normalized.encode`（[ids.py:14](../../../src/core/ids.py#L14)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[FusionReviewAgent._assess_related_groups](../agents/fusion_review_agent.md)、[FusionReviewAgent.route_by_risk](../agents/fusion_review_agent.md)、[MultimodalExtractionAgent.recognize](../agents/multimodal_extraction_agent.md)、[MultimodalExtractionAgent.extract_text](../agents/multimodal_extraction_agent.md)、[MultimodalExtractionAgent.extract_visual](../agents/multimodal_extraction_agent.md)、[trace_step](../agents/trace.md)、[handoff](../agents/trace.md)、[_EvaluationLLM.fingerprint](../evaluation/document_validation.md)、[_EvaluationLLM.extract](../evaluation/document_validation.md)、[_ReusedOCR.fingerprint](../evaluation/document_validation.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# canonical_hash ⭐⭐

**位置与等级**：[ids.py:17](../../../src/core/ids.py#L17)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def canonical_hash(value: Any) -> str`。

**作用**：处理 `canonical_hash` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`value`（Any）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `payload`，值来自 `orjson.dumps(value, option=orjson.OPT_SORT_KEYS)`。
2. 返回 `sha256(payload).hexdigest()`。

**调用与被调用**：
- `orjson.dumps`（[ids.py:18](../../../src/core/ids.py#L18)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `sha256(payload).hexdigest`（[ids.py:19](../../../src/core/ids.py#L19)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sha256`（[ids.py:19](../../../src/core/ids.py#L19)）：来自 `hashlib.sha256`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[EntityGovernanceAgent.normalize](../agents/entity_governance_agent.md)、[evaluate_reflection_manifest](../evaluation/reflection.md)、[rebuild_entity_index](../governance/entity_index.md)、[EntityGovernanceService.propose_split](../governance/entity_operations.md)、[EntityGovernanceService._embedding](../governance/entity_operations.md)、[EntityGovernanceService._apply](../governance/entity_operations.md)、[verify_correction](../governance/review_guards.md)、[bind_commit_provenance](../governance/validation/context.md)、[ValidationService.commit](../governance/validation/service.md)、[CaseRepository.add](../persistence/cases.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# file_sha256 ⭐⭐

**位置与等级**：[ids.py:22](../../../src/core/ids.py#L22)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def file_sha256(path: Path) -> str`。

**作用**：处理 `file_sha256` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`path`（Path）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `digest`，值来自 `sha256()`。
2. 进入上下文 `path.open('rb')`，由上下文管理器控制资源释放或事务范围。
3. 返回 `digest.hexdigest()`。

**调用与被调用**：
- `sha256`（[ids.py:23](../../../src/core/ids.py#L23)）：来自 `hashlib.sha256`；具体实现可能由依赖注入或运行时分派决定。
- `path.open`（[ids.py:24](../../../src/core/ids.py#L24)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `iter`（[ids.py:25](../../../src/core/ids.py#L25)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `digest.update`（[ids.py:26](../../../src/core/ids.py#L26)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `digest.hexdigest`（[ids.py:27](../../../src/core/ids.py#L27)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[_ReusedOCR.recognize](../evaluation/document_validation.md)、[validate_documents](../evaluation/document_validation.md)、[TextParser.parse](../parsing/adapters.md)、[MarkdownParser.parse](../parsing/adapters.md)、[HTMLParser.parse](../parsing/adapters.md)、[DOCXParser.parse](../parsing/adapters.md)、[PDFParser.parse](../parsing/adapters.md)、[ImageParser.parse](../parsing/adapters.md)、[FileEvidenceStore._store_blob](../persistence/file_evidence.md)、[FileEvidenceStore._store_blob_bytes](../persistence/file_evidence.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
