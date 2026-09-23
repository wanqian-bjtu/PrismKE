源码：[reflection.py:1](../../../src/evaluation/reflection.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：10

**模块职责**：Isolated nine-cell case retrieval and Reflection release evaluation.
**在系统中的位置**：离线评测、预算账本、标注导出及报告；不等于生产工作流。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.core.settings](../core/settings.md)、[src.domain](../domain/__init__.md)、[src.evaluation.request_budget](request_budget.md)、[src.persistence](../persistence/__init__.md)、[src.providers](../providers/__init__.md)、[src.providers.base](../providers/base.md)、[src.workflow.cases](../workflow/cases.md)、[src.workflow.reflection](../workflow/reflection.md)；外部/标准库：`__future__`、`json`、`os`、`pathlib`、`tempfile`、`typing`。
**主要调用方（静态导入）**：[evaluation/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# _load ⭐⭐

**位置与等级**：[reflection.py:39](../../../src/evaluation/reflection.py#L39)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _load(path: Path) -> dict[str, Any]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`path`（Path）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `payload`，值来自 `json.loads(path.read_text(encoding='utf-8'))`。
2. 检查 `not isinstance(payload, dict)`；按条件分流，else 分支不存在。
3. 返回 `payload`。

**关键条件与保护**：
- [reflection.py:41](../../../src/evaluation/reflection.py#L41)：`not isinstance(payload, dict)`，不满足时跳过本分支。

**调用与被调用**：
- `json.loads`（[reflection.py:40](../../../src/evaluation/reflection.py#L40)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `path.read_text`（[reflection.py:40](../../../src/evaluation/reflection.py#L40)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `isinstance`（[reflection.py:41](../../../src/evaluation/reflection.py#L41)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[reflection.py:42](../../../src/evaluation/reflection.py#L42)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[evaluate_reflection_manifest](reflection.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _write_atomic ⭐⭐

**位置与等级**：[reflection.py:46](../../../src/evaluation/reflection.py#L46)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _write_atomic(path: Path, payload: dict[str, Any]) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`path`（Path）；`payload`（dict[str, Any]）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `path.parent.mkdir`，结果未直接赋值。
2. 更新 `temporary`，值来自 `None`。
3. 捕获 无显式捕获；另检查 finally/else 的清理和传播。

**关键条件与保护**：
- [reflection.py:60](../../../src/evaluation/reflection.py#L60)：`temporary is not None`，不满足时跳过本分支。

**调用与被调用**：
- `path.parent.mkdir`（[reflection.py:47](../../../src/evaluation/reflection.py#L47)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `tempfile.NamedTemporaryFile`（[reflection.py:50](../../../src/evaluation/reflection.py#L50)）：来自 `tempfile`；具体实现可能由依赖注入或运行时分派决定。
- `Path`（[reflection.py:53](../../../src/evaluation/reflection.py#L53)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `json.dump`（[reflection.py:54](../../../src/evaluation/reflection.py#L54)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `stream.write`（[reflection.py:55](../../../src/evaluation/reflection.py#L55)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `stream.flush`（[reflection.py:56](../../../src/evaluation/reflection.py#L56)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `os.fsync`（[reflection.py:57](../../../src/evaluation/reflection.py#L57)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `stream.fileno`（[reflection.py:57](../../../src/evaluation/reflection.py#L57)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `os.replace`（[reflection.py:58](../../../src/evaluation/reflection.py#L58)）：来自 `os`；具体实现可能由依赖注入或运行时分派决定。
- `temporary.unlink`（[reflection.py:61](../../../src/evaluation/reflection.py#L61)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[evaluate_reflection_manifest](reflection.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _candidate_content ⭐⭐

**位置与等级**：[reflection.py:64](../../../src/evaluation/reflection.py#L64)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _candidate_content(candidate: CandidateClaim) -> dict[str, Any]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`candidate`（CandidateClaim；尚未成为正式 Claim 的候选）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `candidate.model_dump(mode='json', exclude={'id'})`。

**调用与被调用**：
- `candidate.model_dump`（[reflection.py:65](../../../src/evaluation/reflection.py#L65)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[evaluate_reflection_manifest](reflection.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _summary ⭐⭐

**位置与等级**：[reflection.py:68](../../../src/evaluation/reflection.py#L68)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _summary(candidate: CandidateClaim) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`candidate`（CandidateClaim；尚未成为正式 Claim 的候选）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `target`，值来自 `candidate.object.name if hasattr(candidate.object, 'name') else candidate.object`。
2. 返回 `<字符串常量>.join([candidate.subject.name, candidate.subject.entity_type, candidate.relation, str(target), ca…`。

**调用与被调用**：
- `hasattr`（[reflection.py:69](../../../src/evaluation/reflection.py#L69)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `<字符串常量>.join`（[reflection.py:70](../../../src/evaluation/reflection.py#L70)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[reflection.py:75](../../../src/evaluation/reflection.py#L75)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[_seed_cases](reflection.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _seed_cases ⭐⭐

**位置与等级**：[reflection.py:81](../../../src/evaluation/reflection.py#L81)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _seed_cases(repository: CaseRepository, samples: list[dict[str, Any]], schema_fingerprint: str) -> dict[str, str]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`repository`（CaseRepository）；`samples`（list[dict[str, Any]]）；`schema_fingerprint`（str）。
- 输出类型：`dict[str, str]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `relevant`，值来自 `{}`。
2. 更新 `issue_codes`，值来自 `{'relation': 'UNKNOWN_RELATION', 'domain': 'SCHEMA_DOMAIN_RANGE', 'evidence': 'UNKNOWN_EVIDENCE'}`。
3. 遍历 `samples`，逐项处理 `sample`。
4. 返回 `relevant`。

**调用与被调用**：
- `CandidateClaim.model_validate`（[reflection.py:93](../../../src/evaluation/reflection.py#L93)）：来自 `src.domain.CandidateClaim`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[reflection.py:95](../../../src/evaluation/reflection.py#L95)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `repository.add`（[reflection.py:103](../../../src/evaluation/reflection.py#L103)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CaseRecord`（[reflection.py:104](../../../src/evaluation/reflection.py#L104)）：来自 `src.domain.CaseRecord`；具体实现可能由依赖注入或运行时分派决定。
- `_summary`（调用点 [reflection.py:112](../../../src/evaluation/reflection.py#L112)）→ [_summary](reflection.md)，静态可定位。
- `candidate.model_dump`（[reflection.py:114](../../../src/evaluation/reflection.py#L114)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `list`（[reflection.py:117](../../../src/evaluation/reflection.py#L117)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[evaluate_reflection_manifest](reflection.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`relevant[key]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _document ⭐⭐

**位置与等级**：[reflection.py:124](../../../src/evaluation/reflection.py#L124)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _document(sample: dict[str, Any], evidence_store: FileEvidenceStore) -> DocumentIR`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`sample`（dict[str, Any]）；`evidence_store`（FileEvidenceStore；证据元数据和原始内容的存储接口）。
- 输出类型：`DocumentIR`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `text`，值来自 `str(sample['text'])`。
2. 更新 `source_hash`，值来自 `await evidence_store.put_blob(text.encode('utf-8'), 'text/plain')`。
3. 更新 `evidence_id`，值来自 `f<字符串常量>id<字符串常量>`。
4. 更新 `reference`，值来自 `EvidenceRef(id=evidence_id, kind=EvidenceKind.TEXT_SPAN, document_id=f<字符串常量>id<字符串常量>, source_hash…`。
5. 等待 `evidence_store.put_ref(reference)` 完成。
6. 返回 `DocumentIR(id=reference.document_id, source_path=f<字符串常量>id<字符串常量>, source_filename=f<字符串常量>id<字符串常量>, s…`。

**调用与被调用**：
- `str`（[reflection.py:125](../../../src/evaluation/reflection.py#L125)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence_store.put_blob`（[reflection.py:126](../../../src/evaluation/reflection.py#L126)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `text.encode`（[reflection.py:126](../../../src/evaluation/reflection.py#L126)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EvidenceRef`（[reflection.py:128](../../../src/evaluation/reflection.py#L128)）：来自 `src.domain.EvidenceRef`；具体实现可能由依赖注入或运行时分派决定。
- `evidence_store.put_ref`（[reflection.py:135](../../../src/evaluation/reflection.py#L135)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `DocumentIR`（[reflection.py:136](../../../src/evaluation/reflection.py#L136)）：来自 `src.domain.DocumentIR`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[evaluate_reflection_manifest](reflection.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _reflection_provider ⭐⭐

**位置与等级**：[reflection.py:146](../../../src/evaluation/reflection.py#L146)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _reflection_provider(settings: Settings, name: str, budget: RequestBudget) -> ReflectionProvider`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`settings`（Settings；服务配置；敏感值不应进入输出或文档）；`name`（str）；`budget`（RequestBudget）。
- 输出类型：`ReflectionProvider`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `name == 'mock'`；按条件分流，else 分支不存在。
2. 检查 `name != 'openai-compatible'`；按条件分流，else 分支不存在。
3. 检查 `not settings.llm_api_key or not settings.llm_model or (not settings.llm_base_url)`；按条件分流，else 分支不存在。
4. 返回 `OpenAICompatibleReflectionProvider(settings.llm_base_url, settings.llm_api_key, settings.llm_model, sett…`。

**关键条件与保护**：
- [reflection.py:151](../../../src/evaluation/reflection.py#L151)：`name == 'mock'`，不满足时跳过本分支。
- [reflection.py:153](../../../src/evaluation/reflection.py#L153)：`name != 'openai-compatible'`，不满足时跳过本分支。
- [reflection.py:155](../../../src/evaluation/reflection.py#L155)：`not settings.llm_api_key or not settings.llm_model or (not settings.llm_base_url)`，不满足时跳过本分支。

**调用与被调用**：
- `MockReflectionProvider`（[reflection.py:152](../../../src/evaluation/reflection.py#L152)）：来自 `src.providers.MockReflectionProvider`；具体实现可能由依赖注入或运行时分派决定。
- `ValueError`（[reflection.py:154](../../../src/evaluation/reflection.py#L154)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `OpenAICompatibleReflectionProvider`（[reflection.py:157](../../../src/evaluation/reflection.py#L157)）：来自 `src.providers.OpenAICompatibleReflectionProvider`；具体实现可能由依赖注入或运行时分派决定。
- `BudgetedTransport`（调用点 [reflection.py:162](../../../src/evaluation/reflection.py#L162)）→ [BudgetedTransport](request_budget.md)，静态可定位。
- 静态可定位的调用方：[evaluate_reflection_manifest](reflection.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _embedding_provider ⭐⭐

**位置与等级**：[reflection.py:166](../../../src/evaluation/reflection.py#L166)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _embedding_provider(settings: Settings, name: str) -> EmbeddingProvider`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`settings`（Settings；服务配置；敏感值不应进入输出或文档）；`name`（str）。
- 输出类型：`EmbeddingProvider`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `name == 'mock'`；按条件分流，else 分支不存在。
2. 检查 `name != 'bge-m3'`；按条件分流，else 分支不存在。
3. 返回 `BGEM3EmbeddingProvider(model_name=settings.embedding_model, model_revision=settings.embedding_model_revi…`。

**关键条件与保护**：
- [reflection.py:167](../../../src/evaluation/reflection.py#L167)：`name == 'mock'`，不满足时跳过本分支。
- [reflection.py:169](../../../src/evaluation/reflection.py#L169)：`name != 'bge-m3'`，不满足时跳过本分支。

**调用与被调用**：
- `MockEmbeddingProvider`（[reflection.py:168](../../../src/evaluation/reflection.py#L168)）：来自 `src.providers.MockEmbeddingProvider`；具体实现可能由依赖注入或运行时分派决定。
- `ValueError`（[reflection.py:170](../../../src/evaluation/reflection.py#L170)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `BGEM3EmbeddingProvider`（[reflection.py:173](../../../src/evaluation/reflection.py#L173)）：来自 `src.providers.BGEM3EmbeddingProvider`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[evaluate_reflection_manifest](reflection.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _configuration_name ⭐⭐

**位置与等级**：[reflection.py:186](../../../src/evaluation/reflection.py#L186)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _configuration_name(case_mode: str, attempts: int) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`case_mode`（str）；`attempts`（int）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `f<字符串常量>`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态可定位的调用方：[evaluate_reflection_manifest](reflection.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# evaluate_reflection_manifest ⭐⭐⭐⭐

**位置与等级**：[reflection.py:190](../../../src/evaluation/reflection.py#L190)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def evaluate_reflection_manifest(manifest_path: Path, output: Path, *, settings: Settings | None=None, reflection_provider_name: str='mock', embedding_provider_name: str='mock', token_limit: int=200000, stop_at: int=180000) -> dict[str, Any]`。

**作用**：处理 `evaluate_reflection_manifest` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`manifest_path`（Path）；`output`（Path）；`settings`（Settings | None；默认 `None`；服务配置；敏感值不应进入输出或文档）；`reflection_provider_name`（str；默认 `'mock'`）；`embedding_provider_name`（str；默认 `'mock'`）；`token_limit`（int；默认 `200000`）；`stop_at`（int；默认 `180000`）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not 0 < stop_at < token_limit`；按条件分流，else 分支不存在。
2. 更新 `settings`，值来自 `settings or Settings()`。
3. 调用 `output.mkdir`，结果未直接赋值。
4. 更新 `manifest`，值来自 `_load(manifest_path)`。
5. 更新 `base`，值来自 `manifest_path.parent`。
6. 更新 `schema`，值来自 `OutputSchema.model_validate(_load(base / manifest['schema']))`。
7. 更新 `schema_fingerprint`，值来自 `canonical_hash(schema.model_dump(mode='json'))`。
8. 更新 `development`，值来自 `[_load(base / item) for item in manifest['development']]`。
9. 更新 `final`，值来自 `[_load(base / item) for item in manifest['test']]`。
10. 检查 `len(development) != 6 or len(final) != 12`；按条件分流，else 分支不存在。
11. 更新 `repository`，值来自 `CaseRepository(output / 'cases.sqlite')`。
12. 更新 `relevant`，值来自 `_seed_cases(repository, development, schema_fingerprint)`。
13. 更新 `embeddings`，值来自 `_embedding_provider(settings, embedding_provider_name)`。
14. 更新 `retriever`，值来自 `CaseRetriever(repository, embeddings)`。
15. 等待 `retriever.rebuild()` 完成。
16. 更新 `budget`，值来自 `RequestBudget(limit=token_limit, stop_at=stop_at, ledger_path=output / 'request-ledger.json')`。
17. 更新 `provider`，值来自 `_reflection_provider(settings, reflection_provider_name, budget)`。
18. 更新 `evidence_store`，值来自 `FileEvidenceStore(output / 'evidence')`。
19. 更新 `configurations`，值来自 `[(case_mode, attempts) for case_mode in ('none', 'good', 'good_bad') for attempts in (0, 1, 2)]`。
20. 更新 `report`，值来自 `{'version': str(manifest['version']), 'schema_fingerprint': schema_fingerprint, 'reflection_provide…`。
21. 更新 `stop`，值来自 `False`。
22. 遍历 `configurations`，逐项处理 `(case_mode, attempts)`。
23. 等待 `budget.settle()` 完成。
24. 更新 `rows`，值来自 `[row for config in report['configurations'] for row in config['samples']]`。
后续还有 13 个语句级步骤，见源码对应行；这里优先保留主要控制流。

**关键条件与保护**：
- [reflection.py:200](../../../src/evaluation/reflection.py#L200)：`not 0 < stop_at < token_limit`，不满足时跳过本分支。
- [reflection.py:210](../../../src/evaluation/reflection.py#L210)：`len(development) != 6 or len(final) != 12`，不满足时跳过本分支。
- [reflection.py:313](../../../src/evaluation/reflection.py#L313)：`budget.stopped_reason or budget.total_tokens >= stop_at`，不满足时跳过本分支。
- [reflection.py:318](../../../src/evaluation/reflection.py#L318)：`stop`，不满足时跳过本分支。

**调用与被调用**：
- `ValueError`（[reflection.py:201](../../../src/evaluation/reflection.py#L201)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Settings`（调用点 [reflection.py:202](../../../src/evaluation/reflection.py#L202)）→ [Settings](../core/settings.md)，静态可定位。
- `output.mkdir`（[reflection.py:203](../../../src/evaluation/reflection.py#L203)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_load`（调用点 [reflection.py:204](../../../src/evaluation/reflection.py#L204)）→ [_load](reflection.md)，静态可定位。
- `OutputSchema.model_validate`（[reflection.py:206](../../../src/evaluation/reflection.py#L206)）：来自 `src.domain.OutputSchema`；具体实现可能由依赖注入或运行时分派决定。
- `canonical_hash`（调用点 [reflection.py:207](../../../src/evaluation/reflection.py#L207)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `schema.model_dump`（[reflection.py:207](../../../src/evaluation/reflection.py#L207)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[reflection.py:210](../../../src/evaluation/reflection.py#L210)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CaseRepository`（[reflection.py:212](../../../src/evaluation/reflection.py#L212)）：来自 `src.persistence.CaseRepository`；具体实现可能由依赖注入或运行时分派决定。
- `_seed_cases`（调用点 [reflection.py:213](../../../src/evaluation/reflection.py#L213)）→ [_seed_cases](reflection.md)，静态可定位。
- `_embedding_provider`（调用点 [reflection.py:214](../../../src/evaluation/reflection.py#L214)）→ [_embedding_provider](reflection.md)，静态可定位。
- `CaseRetriever`（调用点 [reflection.py:215](../../../src/evaluation/reflection.py#L215)）→ [CaseRetriever](../workflow/cases.md)，静态可定位。
- `retriever.rebuild`（[reflection.py:216](../../../src/evaluation/reflection.py#L216)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `RequestBudget`（调用点 [reflection.py:217](../../../src/evaluation/reflection.py#L217)）→ [RequestBudget](request_budget.md)，静态可定位。
- `_reflection_provider`（调用点 [reflection.py:222](../../../src/evaluation/reflection.py#L222)）→ [_reflection_provider](reflection.md)，静态可定位。
- `FileEvidenceStore`（[reflection.py:223](../../../src/evaluation/reflection.py#L223)）：来自 `src.persistence.FileEvidenceStore`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[reflection.py:230](../../../src/evaluation/reflection.py#L230)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `provider.fingerprint`（[reflection.py:232](../../../src/evaluation/reflection.py#L232)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `embeddings.fingerprint`（[reflection.py:233](../../../src/evaluation/reflection.py#L233)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_configuration_name`（调用点 [reflection.py:243](../../../src/evaluation/reflection.py#L243)）→ [_configuration_name](reflection.md)，静态可定位。
- `_document`（调用点 [reflection.py:247](../../../src/evaluation/reflection.py#L247)）→ [_document](reflection.md)，静态可定位。
- `CandidateClaim.model_validate`（[reflection.py:248](../../../src/evaluation/reflection.py#L248)）：来自 `src.domain.CandidateClaim`；具体实现可能由依赖注入或运行时分派决定。
- `WorkflowState`（[reflection.py:249](../../../src/evaluation/reflection.py#L249)）：来自 `src.domain.WorkflowState`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [reflection.py:250](../../../src/evaluation/reflection.py#L250)）→ [stable_id](../core/ids.md)，静态可定位。
- `original.model_copy`（[reflection.py:256](../../../src/evaluation/reflection.py#L256)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `retriever.snapshot_ids`（[reflection.py:259](../../../src/evaluation/reflection.py#L259)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `BoundedReflectionService`（调用点 [reflection.py:268](../../../src/evaluation/reflection.py#L268)）→ [BoundedReflectionService](../workflow/reflection.md)，静态可定位。
- `service.run`（[reflection.py:274](../../../src/evaluation/reflection.py#L274)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sample.get`（[reflection.py:280](../../../src/evaluation/reflection.py#L280)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_candidate_content`（调用点 [reflection.py:282](../../../src/evaluation/reflection.py#L282)）→ [_candidate_content](reflection.md)，静态可定位。
- 此处列出前 30 个不同调用表达式，另有 16 个，需按源码继续追踪。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`budget.case_id`、`report['stopped_reason']`、`report['metrics']`、`report['request_ledger']`、`report['publish_ready']`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：`EvaluationBudgetStop`。


---
