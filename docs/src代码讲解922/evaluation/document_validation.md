源码：[document_validation.py:1](../../../src/evaluation/document_validation.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：18

**模块职责**：Live document validation against an isolated JSON graph, without gold-assisted review.
**在系统中的位置**：离线评测、预算账本、标注导出及报告；不等于生产工作流。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.core.settings](../core/settings.md)、[src.domain](../domain/__init__.md)、[src.evaluation.request_budget](request_budget.md)、[src.governance.entity_index](../governance/entity_index.md)、[src.persistence.json_graph](../persistence/json_graph.md)、[src.providers.base](../providers/base.md)、[src.providers.openai_compatible](../providers/openai_compatible.md)、[src.providers.vlm](../providers/vlm.md)、[src.workflow.service](../workflow/service.md)；外部/标准库：`__future__`、`json`、`os`、`pathlib`、`subprocess`、`tempfile`、`time`、`typing`。
**主要调用方（静态导入）**：未见静态直接导入；可能由包入口、框架注册或动态加载。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# _EvaluationLLM ⭐⭐

**位置与等级**：[document_validation.py:37](../../../src/evaluation/document_validation.py#L37)；局部辅助逻辑，需理解其调用条件与失败传播。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：`OpenAICompatibleLLMProvider`。

**字段与类级约束**：
- `cached_state`：`dict[str, Any] | None`；默认 `None`。
- `cache_dir`：`Path | None`；默认 `None`。

**内部成员**：`_EvaluationLLM.fingerprint`、`_EvaluationLLM.extract`


---

# _EvaluationLLM.fingerprint ⭐⭐

**位置与等级**：[document_validation.py:41](../../../src/evaluation/document_validation.py#L41)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `stable_id('provider', super().fingerprint(), 'evaluation-output-limit-v4', 4096, 12000, self.cached_stat…`。

**调用与被调用**：
- `stable_id`（调用点 [document_validation.py:42](../../../src/evaluation/document_validation.py#L42)）→ [stable_id](../core/ids.md)，静态可定位。
- `super().fingerprint`（[document_validation.py:44](../../../src/evaluation/document_validation.py#L44)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `super`（[document_validation.py:44](../../../src/evaluation/document_validation.py#L44)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.cached_state.get`（[document_validation.py:48](../../../src/evaluation/document_validation.py#L48)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _EvaluationLLM.extract ⭐⭐⭐⭐

**位置与等级**：[document_validation.py:51](../../../src/evaluation/document_validation.py#L51)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def extract(self, request: ExtractionRequest) -> ExtractionResult`。

**作用**：处理 `extract` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（ExtractionRequest）。
- 输出类型：`ExtractionResult`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `combined`，值来自 `ExtractionResult()`。
2. 更新 `blocks`，值来自 `request.document.text_blocks`。
3. 检查 `self.cached_state`；按条件分流，else 分支不存在。
4. 更新 `batches`，值来自 `text_batches(blocks)`。
5. 遍历 `batches`，逐项处理 `batch`。
6. 调用 `combined.warnings.append`，结果未直接赋值。
7. 检查 `any((len(block.text.encode('utf-8')) > 12000 for block in request.document.text_blocks))`；按条件分流，else 分支不存在。
8. 返回 `combined`。

**关键条件与保护**：
- [document_validation.py:54](../../../src/evaluation/document_validation.py#L54)：`self.cached_state`，不满足时跳过本分支。
- [document_validation.py:60](../../../src/evaluation/document_validation.py#L60)：`cached.get('provider_fingerprint') != expected_fingerprint or cached.get('status') not in {'completed', 'awaiting_…`，不满足时跳过本分支。
- [document_validation.py:64](../../../src/evaluation/document_validation.py#L64)：`old_doc['source_hash'] != request.document.source_hash`，不满足时跳过本分支。
- [document_validation.py:66](../../../src/evaluation/document_validation.py#L66)：`cached['output_schema'] != request.output_schema.model_dump(mode='json')`，不满足时跳过本分支。
- [document_validation.py:70](../../../src/evaluation/document_validation.py#L70)：`[block for block in blocks if block.id in ids] != old_blocks`，不满足时跳过本分支。
- [document_validation.py:73](../../../src/evaluation/document_validation.py#L73)：`not llm_calls or any((row['requested_model'] != self.model or row['status'] != 'succeeded' or row['prompt_version'…`，不满足时跳过本分支。
- [document_validation.py:84](../../../src/evaluation/document_validation.py#L84)：`any((eid not in current_refs for candidate in combined.candidates for eid in candidate.evidence_ids))`，不满足时跳过本分支。
- [document_validation.py:98](../../../src/evaluation/document_validation.py#L98)：`self.cache_dir`，不满足时跳过本分支。
- [document_validation.py:109](../../../src/evaluation/document_validation.py#L109)：`cache_path and cache_path.exists()`，不满足时有 else 分支。
- [document_validation.py:117](../../../src/evaluation/document_validation.py#L117)：`cache_path`，不满足时跳过本分支。
- [document_validation.py:133](../../../src/evaluation/document_validation.py#L133)：`any((len(block.text.encode('utf-8')) > 12000 for block in request.document.text_blocks))`，不满足时跳过本分支。

**调用与被调用**：
- `ExtractionResult`（[document_validation.py:52](../../../src/evaluation/document_validation.py#L52)）：来自 `src.domain.ExtractionResult`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [document_validation.py:57](../../../src/evaluation/document_validation.py#L57)）→ [stable_id](../core/ids.md)，静态可定位。
- `super().fingerprint`（[document_validation.py:58](../../../src/evaluation/document_validation.py#L58)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `super`（[document_validation.py:58](../../../src/evaluation/document_validation.py#L58)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `cached.get`（[document_validation.py:60](../../../src/evaluation/document_validation.py#L60)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[document_validation.py:63](../../../src/evaluation/document_validation.py#L63)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `request.output_schema.model_dump`（[document_validation.py:66](../../../src/evaluation/document_validation.py#L66)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `TextBlock.model_validate`（[document_validation.py:68](../../../src/evaluation/document_validation.py#L68)）：来自 `src.domain.TextBlock`；具体实现可能由依赖注入或运行时分派决定。
- `any`（[document_validation.py:73](../../../src/evaluation/document_validation.py#L73)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CandidateClaim.model_validate`（[document_validation.py:81](../../../src/evaluation/document_validation.py#L81)）：来自 `src.domain.CandidateClaim`；具体实现可能由依赖注入或运行时分派决定。
- `combined.warnings.extend`（[document_validation.py:90](../../../src/evaluation/document_validation.py#L90)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `w.startswith`（[document_validation.py:90](../../../src/evaluation/document_validation.py#L90)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `combined.warnings.append`（[document_validation.py:91](../../../src/evaluation/document_validation.py#L91)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[document_validation.py:92](../../../src/evaluation/document_validation.py#L92)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `text_batches`（调用点 [document_validation.py:94](../../../src/evaluation/document_validation.py#L94)）→ [text_batches](document_validation.md)，静态可定位。
- `request.document.model_copy`（[document_validation.py:96](../../../src/evaluation/document_validation.py#L96)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.cache_dir.mkdir`（[document_validation.py:99](../../../src/evaluation/document_validation.py#L99)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `block.model_dump`（[document_validation.py:106](../../../src/evaluation/document_validation.py#L106)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `key.replace`（[document_validation.py:108](../../../src/evaluation/document_validation.py#L108)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `cache_path.exists`（[document_validation.py:109](../../../src/evaluation/document_validation.py#L109)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ExtractionResult.model_validate_json`（[document_validation.py:110](../../../src/evaluation/document_validation.py#L110)）：来自 `src.domain.ExtractionResult`；具体实现可能由依赖注入或运行时分派决定。
- `cache_path.read_text`（[document_validation.py:111](../../../src/evaluation/document_validation.py#L111)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.warnings.append`（[document_validation.py:114](../../../src/evaluation/document_validation.py#L114)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `super().extract`（[document_validation.py:116](../../../src/evaluation/document_validation.py#L116)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `request.model_copy`（[document_validation.py:116](../../../src/evaluation/document_validation.py#L116)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `tempfile.NamedTemporaryFile`（[document_validation.py:118](../../../src/evaluation/document_validation.py#L118)）：来自 `tempfile`；具体实现可能由依赖注入或运行时分派决定。
- `Path`（[document_validation.py:121](../../../src/evaluation/document_validation.py#L121)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `stream.write`（[document_validation.py:122](../../../src/evaluation/document_validation.py#L122)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `result.model_dump_json`（[document_validation.py:122](../../../src/evaluation/document_validation.py#L122)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `stream.flush`（[document_validation.py:123](../../../src/evaluation/document_validation.py#L123)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 此处列出前 30 个不同调用表达式，另有 7 个，需按源码继续追踪。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`combined.candidates`、`result.call_records`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# text_batches ⭐⭐

**位置与等级**：[document_validation.py:138](../../../src/evaluation/document_validation.py#L138)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def text_batches(blocks: list[TextBlock], max_bytes: int=12000) -> list[list[TextBlock]]`。

**作用**：处理 `text_batches` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`blocks`（list[TextBlock]）；`max_bytes`（int；默认 `12000`）。
- 输出类型：`list[list[TextBlock]]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `batches`，值来自 `[]`。
2. 更新 `batch`，值来自 `[]`。
3. 更新 `size`，值来自 `0`。
4. 遍历 `blocks`，逐项处理 `block`。
5. 检查 `batch`；按条件分流，else 分支不存在。
6. 返回 `batches`。

**关键条件与保护**：
- [document_validation.py:144](../../../src/evaluation/document_validation.py#L144)：`batch and size + block_size > max_bytes`，不满足时跳过本分支。
- [document_validation.py:149](../../../src/evaluation/document_validation.py#L149)：`batch`，不满足时跳过本分支。

**调用与被调用**：
- `len`（[document_validation.py:143](../../../src/evaluation/document_validation.py#L143)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `block.text.encode`（[document_validation.py:143](../../../src/evaluation/document_validation.py#L143)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `batches.append`（[document_validation.py:145](../../../src/evaluation/document_validation.py#L145)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `batch.append`（[document_validation.py:147](../../../src/evaluation/document_validation.py#L147)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[_EvaluationLLM.extract](document_validation.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _ReusedOCR ⭐⭐

**位置与等级**：[document_validation.py:154](../../../src/evaluation/document_validation.py#L154)；局部辅助逻辑，需理解其调用条件与失败传播。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`_ReusedOCR.__init__`、`_ReusedOCR.fingerprint`、`_ReusedOCR.recognize`


---

# _ReusedOCR.__init__ ⭐⭐

**位置与等级**：[document_validation.py:155](../../../src/evaluation/document_validation.py#L155)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, original: OCRProvider, state: dict[str, Any]) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`original`（OCRProvider）；`state`（dict[str, Any]；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `(self.original, self.state)`，值来自 `(original, state)`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _ReusedOCR.fingerprint ⭐⭐

**位置与等级**：[document_validation.py:158](../../../src/evaluation/document_validation.py#L158)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `stable_id('provider', self.original.fingerprint(), 'evaluation-reused-ocr-v1', self.state['run_id'])`。

**调用与被调用**：
- `stable_id`（调用点 [document_validation.py:159](../../../src/evaluation/document_validation.py#L159)）→ [stable_id](../core/ids.md)，静态可定位。
- `self.original.fingerprint`（[document_validation.py:161](../../../src/evaluation/document_validation.py#L161)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _ReusedOCR.recognize ⭐⭐

**位置与等级**：[document_validation.py:166](../../../src/evaluation/document_validation.py#L166)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def recognize(self, request: OCRRequest) -> OCRResult`。

**作用**：处理 `recognize` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（OCRRequest）。
- 输出类型：`OCRResult`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self.state.get('ocr_provider_fingerprint') != self.original.fingerprint()`；按条件分流，else 分支不存在。
2. 更新 `downstream`，值来自 `{'load_schema', 'extract_text_claims', 'extract_visual_claims', 'align_modalities', 'resolve_entiti…`。
3. 检查 `self.state.get('status') not in {'completed', 'awaiting_review'} and self.state.get('failed_node') not i…`；按条件分流，else 分支不存在。
4. 更新 `cached`，值来自 `DocumentIR.model_validate(self.state['document'])`。
5. 检查 `cached.source_hash != request.document.source_hash`；按条件分流，else 分支不存在。
6. 检查 `signature(cached) != signature(request.document)`；按条件分流，else 分支不存在。
7. 遍历 `request.document.media_assets`，逐项处理 `asset`。
8. 更新 `warnings`，值来自 `[w for w in self.state.get('warnings', []) if w.startswith(('low_confidence_ocr:', 'ocr_failed:'))]`。
9. 检查 `any((w.startswith('ocr_failed:') for w in warnings))`；按条件分流，else 分支不存在。
10. 返回 `OCRResult(text_blocks=[b for b in cached.text_blocks if b.modality == 'ocr'], evidence=[e for e in cache…`。

**关键条件与保护**：
- [document_validation.py:167](../../../src/evaluation/document_validation.py#L167)：`self.state.get('ocr_provider_fingerprint') != self.original.fingerprint()`，不满足时跳过本分支。
- [document_validation.py:177](../../../src/evaluation/document_validation.py#L177)：`self.state.get('status') not in {'completed', 'awaiting_review'} and self.state.get('failed_node') not in downstre…`，不满足时跳过本分支。
- [document_validation.py:182](../../../src/evaluation/document_validation.py#L182)：`cached.source_hash != request.document.source_hash`，不满足时跳过本分支。
- [document_validation.py:191](../../../src/evaluation/document_validation.py#L191)：`signature(cached) != signature(request.document)`，不满足时跳过本分支。
- [document_validation.py:194](../../../src/evaluation/document_validation.py#L194)：`not asset.blob_hash or file_sha256(Path(asset.path)) != asset.blob_hash`，不满足时跳过本分支。
- [document_validation.py:201](../../../src/evaluation/document_validation.py#L201)：`any((w.startswith('ocr_failed:') for w in warnings))`，不满足时跳过本分支。

**调用与被调用**：
- `self.state.get`（[document_validation.py:167](../../../src/evaluation/document_validation.py#L167)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.original.fingerprint`（[document_validation.py:167](../../../src/evaluation/document_validation.py#L167)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[document_validation.py:168](../../../src/evaluation/document_validation.py#L168)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `DocumentIR.model_validate`（[document_validation.py:181](../../../src/evaluation/document_validation.py#L181)）：来自 `src.domain.DocumentIR`；具体实现可能由依赖注入或运行时分派决定。
- `signature`（[document_validation.py:191](../../../src/evaluation/document_validation.py#L191)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `file_sha256`（调用点 [document_validation.py:194](../../../src/evaluation/document_validation.py#L194)）→ [file_sha256](../core/ids.md)，静态可定位。
- `Path`（[document_validation.py:194](../../../src/evaluation/document_validation.py#L194)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `w.startswith`（[document_validation.py:199](../../../src/evaluation/document_validation.py#L199)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[document_validation.py:201](../../../src/evaluation/document_validation.py#L201)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `OCRResult`（[document_validation.py:203](../../../src/evaluation/document_validation.py#L203)）：来自 `src.domain.OCRResult`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _ReusedOCR.recognize.signature ⭐⭐

**位置与等级**：[document_validation.py:185](../../../src/evaluation/document_validation.py#L185)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def signature(document: DocumentIR) -> list[tuple[Any, ...]]`。

**作用**：处理 `signature` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`document`（DocumentIR；解析后的文档及其文本、媒体、证据定位）。
- 输出类型：`list[tuple[Any, ...]]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `[(a.id, a.blob_hash, a.width, a.height, a.page_number, a.origin) for a in document.media_assets]`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _EvaluationVLM ⭐⭐

**位置与等级**：[document_validation.py:210](../../../src/evaluation/document_validation.py#L210)；局部辅助逻辑，需理解其调用条件与失败传播。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：`OpenAICompatibleVLMProvider`。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`_EvaluationVLM.fingerprint`、`_EvaluationVLM._post`


---

# _EvaluationVLM.fingerprint ⭐⭐

**位置与等级**：[document_validation.py:211](../../../src/evaluation/document_validation.py#L211)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def fingerprint(self) -> str`。

**作用**：处理 `fingerprint` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `stable_id('provider', super().fingerprint(), 'evaluation-vision-output-limit-v3', 8192)`。

**调用与被调用**：
- `stable_id`（调用点 [document_validation.py:212](../../../src/evaluation/document_validation.py#L212)）→ [stable_id](../core/ids.md)，静态可定位。
- `super().fingerprint`（[document_validation.py:213](../../../src/evaluation/document_validation.py#L213)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `super`（[document_validation.py:213](../../../src/evaluation/document_validation.py#L213)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _EvaluationVLM._post ⭐⭐

**位置与等级**：[document_validation.py:216](../../../src/evaluation/document_validation.py#L216)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _post(self, body: dict[str, Any], operation_id: str) -> tuple[dict[str, Any], ProviderCallRecord]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`body`（dict[str, Any]）；`operation_id`（str）。
- 输出类型：`tuple[dict[str, Any], ProviderCallRecord]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await super()._post({**body, <字符串常量>: 8192}, operation_id)`。

**调用与被调用**：
- `super()._post`（[document_validation.py:219](../../../src/evaluation/document_validation.py#L219)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `super`（[document_validation.py:219](../../../src/evaluation/document_validation.py#L219)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _EvaluationService ⭐⭐

**位置与等级**：[document_validation.py:222](../../../src/evaluation/document_validation.py#L222)；局部辅助逻辑，需理解其调用条件与失败传播。

**职责**：跨步骤服务；组合依赖并暴露可复用业务入口。基类：`PrismKEService`。

**字段与类级约束**：
- `cached_text_state`：`dict[str, Any] | None`；默认 `None`。
- `cached_ocr_state`：`dict[str, Any] | None`；默认 `None`。

**内部成员**：`_EvaluationService.__init__`、`_EvaluationService.ocr_provider`、`_EvaluationService.provider`、`_EvaluationService.vlm_provider`


---

# _EvaluationService.__init__ ⭐⭐

**位置与等级**：[document_validation.py:226](../../../src/evaluation/document_validation.py#L226)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, settings: Settings, store: JSONGraphStore, budget: RequestBudget) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`settings`（Settings；服务配置；敏感值不应进入输出或文档）；`store`（JSONGraphStore）；`budget`（RequestBudget）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `super().__init__`，结果未直接赋值。
2. 更新 `self.budget`，值来自 `budget`。

**调用与被调用**：
- `super().__init__`（[document_validation.py:227](../../../src/evaluation/document_validation.py#L227)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `super`（[document_validation.py:227](../../../src/evaluation/document_validation.py#L227)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.budget`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _EvaluationService.ocr_provider ⭐⭐

**位置与等级**：[document_validation.py:230](../../../src/evaluation/document_validation.py#L230)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def ocr_provider(self, name: str) -> OCRProvider`。

**作用**：处理 `ocr_provider` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`name`（str）。
- 输出类型：`OCRProvider`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `original`，值来自 `super().ocr_provider(name)`。
2. 返回 `_ReusedOCR(original, self.cached_ocr_state) if self.cached_ocr_state else original`。

**调用与被调用**：
- `super().ocr_provider`（[document_validation.py:231](../../../src/evaluation/document_validation.py#L231)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `super`（[document_validation.py:231](../../../src/evaluation/document_validation.py#L231)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_ReusedOCR`（调用点 [document_validation.py:232](../../../src/evaluation/document_validation.py#L232)）→ [_ReusedOCR](document_validation.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _EvaluationService.provider ⭐⭐

**位置与等级**：[document_validation.py:234](../../../src/evaluation/document_validation.py#L234)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def provider(self, name: str) -> LLMProvider`。

**作用**：处理 `provider` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`name`（str）。
- 输出类型：`LLMProvider`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `original`，值来自 `super().provider(name)`。
2. 检查 `not isinstance(original, OpenAICompatibleLLMProvider)`；按条件分流，else 分支不存在。
3. 更新 `provider`，值来自 `_EvaluationLLM(original.base_url, original.api_key, original.model, original.timeout, transport=Bud…`。
4. 更新 `provider.cached_state`，值来自 `self.cached_text_state`。
5. 更新 `cache_root`，值来自 `self.budget.ledger_path.parent if self.budget.ledger_path is not None else self.settings.runtime_dir`。
6. 更新 `provider.cache_dir`，值来自 `cache_root / 'extraction-cache' / 'text'`。
7. 返回 `provider`。

**关键条件与保护**：
- [document_validation.py:236](../../../src/evaluation/document_validation.py#L236)：`not isinstance(original, OpenAICompatibleLLMProvider)`，不满足时跳过本分支。

**调用与被调用**：
- `super().provider`（[document_validation.py:235](../../../src/evaluation/document_validation.py#L235)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `super`（[document_validation.py:235](../../../src/evaluation/document_validation.py#L235)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `isinstance`（[document_validation.py:236](../../../src/evaluation/document_validation.py#L236)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[document_validation.py:237](../../../src/evaluation/document_validation.py#L237)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_EvaluationLLM`（调用点 [document_validation.py:238](../../../src/evaluation/document_validation.py#L238)）→ [_EvaluationLLM](document_validation.md)，静态可定位。
- `BudgetedTransport`（调用点 [document_validation.py:243](../../../src/evaluation/document_validation.py#L243)）→ [BudgetedTransport](request_budget.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`provider.cached_state`、`provider.cache_dir`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _EvaluationService.vlm_provider ⭐⭐

**位置与等级**：[document_validation.py:254](../../../src/evaluation/document_validation.py#L254)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def vlm_provider(self, name: str) -> VLMProvider`。

**作用**：处理 `vlm_provider` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`name`（str）。
- 输出类型：`VLMProvider`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `original`，值来自 `super().vlm_provider(name)`。
2. 检查 `not isinstance(original, OpenAICompatibleVLMProvider)`；按条件分流，else 分支不存在。
3. 返回 `_EvaluationVLM(original.base_url, original.api_key, original.model, original.timeout, original.max_image…`。

**关键条件与保护**：
- [document_validation.py:256](../../../src/evaluation/document_validation.py#L256)：`not isinstance(original, OpenAICompatibleVLMProvider)`，不满足时跳过本分支。

**调用与被调用**：
- `super().vlm_provider`（[document_validation.py:255](../../../src/evaluation/document_validation.py#L255)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `super`（[document_validation.py:255](../../../src/evaluation/document_validation.py#L255)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `isinstance`（[document_validation.py:256](../../../src/evaluation/document_validation.py#L256)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[document_validation.py:257](../../../src/evaluation/document_validation.py#L257)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_EvaluationVLM`（调用点 [document_validation.py:258](../../../src/evaluation/document_validation.py#L258)）→ [_EvaluationVLM](document_validation.md)，静态可定位。
- `BudgetedTransport`（调用点 [document_validation.py:264](../../../src/evaluation/document_validation.py#L264)）→ [BudgetedTransport](request_budget.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# validate_documents ⭐⭐⭐⭐

**位置与等级**：[document_validation.py:268](../../../src/evaluation/document_validation.py#L268)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def validate_documents(manifest_path: Path, settings: Settings, output: Path, *, token_limit: int=100000, stop_at: int=90000, budget_ledger: Path | None=None, extend_budget: bool=False) -> dict[str, Any]`。

**作用**：处理 `validate_documents` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`manifest_path`（Path）；`settings`（Settings；服务配置；敏感值不应进入输出或文档）；`output`（Path）；`token_limit`（int；默认 `100000`）；`stop_at`（int；默认 `90000`）；`budget_ledger`（Path | None；默认 `None`）；`extend_budget`（bool；默认 `False`）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `budget`，值来自 `RequestBudget(limit=token_limit, stop_at=stop_at, ledger_path=budget_ledger or output / 'request-le…`。
2. 更新 `starting_tokens`，值来自 `budget.total_tokens`。
3. 更新 `manifest`，值来自 `json.loads(manifest_path.read_text(encoding='utf-8'))`。
4. 检查 `output.exists()`；按条件分流，else 分支不存在。
5. 更新 `cases`，值来自 `manifest['cases']`。
6. 检查 `len({item['id'] for item in cases}) != len(cases)`；按条件分流，else 分支不存在。
7. 更新 `inputs`，值来自 `[]`。
8. 遍历 `cases`，逐项处理 `case`。
9. 更新 `original_graph`，值来自 `settings.graph_dir / 'graph.json'`。
10. 更新 `before`，值来自 `file_sha256(original_graph) if original_graph.exists() else None`。
11. 更新 `isolated`，值来自 `settings.model_copy(update={'runtime_dir': output, 'graph_store': 'json', 'embedding_allow_download…`。
12. 更新 `store`，值来自 `JSONGraphStore(output / 'graph')`。
13. 更新 `service`，值来自 `_EvaluationService(isolated, store, budget)`。
14. 更新 `report`，值来自 `{'graph_backend': 'isolated_json', 'full_text_precision_f1': 'not_evaluated', 'manual_reviews_auto_…`。
15. 捕获 无显式捕获；另检查 finally/else 的清理和传播。
16. 返回 `report`。

**关键条件与保护**：
- [document_validation.py:287](../../../src/evaluation/document_validation.py#L287)：`output.exists()`，不满足时跳过本分支。
- [document_validation.py:290](../../../src/evaluation/document_validation.py#L290)：`len({item['id'] for item in cases}) != len(cases)`，不满足时跳过本分支。
- [document_validation.py:296](../../../src/evaluation/document_validation.py#L296)：`not path.is_file() or not schema.is_file()`，不满足时跳过本分支。
- [document_validation.py:298](../../../src/evaluation/document_validation.py#L298)：`case.get('sha256') and file_sha256(path) != case['sha256']`，不满足时跳过本分支。
- [document_validation.py:329](../../../src/evaluation/document_validation.py#L329)：`isolated.embedding_provider != 'bge-m3'`，不满足时跳过本分支。
- [document_validation.py:333](../../../src/evaluation/document_validation.py#L333)：`manifest.get('seed_kb')`，不满足时跳过本分支。
- [document_validation.py:353](../../../src/evaluation/document_validation.py#L353)：`budget.stopped_reason or budget.total_tokens >= budget.stop_at`，不满足时跳过本分支。
- [document_validation.py:391](../../../src/evaluation/document_validation.py#L391)：`matching`，不满足时跳过本分支。
- [document_validation.py:394](../../../src/evaluation/document_validation.py#L394)：`not budget.stopped_reason`，不满足时跳过本分支。
- [document_validation.py:426](../../../src/evaluation/document_validation.py#L426)：`budget.stopped_reason or (index < 2 and state.status == 'failed')`，不满足时跳过本分支。
- [document_validation.py:460](../../../src/evaluation/document_validation.py#L460)：`before != after`，不满足时跳过本分支。

**调用与被调用**：
- `RequestBudget`（调用点 [document_validation.py:278](../../../src/evaluation/document_validation.py#L278)）→ [RequestBudget](request_budget.md)，静态可定位。
- `json.loads`（[document_validation.py:286](../../../src/evaluation/document_validation.py#L286)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `manifest_path.read_text`（[document_validation.py:286](../../../src/evaluation/document_validation.py#L286)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `output.exists`（[document_validation.py:287](../../../src/evaluation/document_validation.py#L287)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[document_validation.py:288](../../../src/evaluation/document_validation.py#L288)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[document_validation.py:290](../../../src/evaluation/document_validation.py#L290)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `(manifest_path.parent / case['input_path']).resolve`（[document_validation.py:294](../../../src/evaluation/document_validation.py#L294)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `(manifest_path.parent / case['schema_path']).resolve`（[document_validation.py:295](../../../src/evaluation/document_validation.py#L295)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.is_file`（[document_validation.py:296](../../../src/evaluation/document_validation.py#L296)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `schema.is_file`（[document_validation.py:296](../../../src/evaluation/document_validation.py#L296)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `case.get`（[document_validation.py:298](../../../src/evaluation/document_validation.py#L298)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `file_sha256`（调用点 [document_validation.py:298](../../../src/evaluation/document_validation.py#L298)）→ [file_sha256](../core/ids.md)，静态可定位。
- `inputs.append`（[document_validation.py:300](../../../src/evaluation/document_validation.py#L300)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `original_graph.exists`（[document_validation.py:302](../../../src/evaluation/document_validation.py#L302)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `settings.model_copy`（[document_validation.py:303](../../../src/evaluation/document_validation.py#L303)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `settings.embedding_model_cache_dir.resolve`（[document_validation.py:308](../../../src/evaluation/document_validation.py#L308)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `JSONGraphStore`（调用点 [document_validation.py:311](../../../src/evaluation/document_validation.py#L311)）→ [JSONGraphStore](../persistence/json_graph.md)，静态可定位。
- `_EvaluationService`（调用点 [document_validation.py:312](../../../src/evaluation/document_validation.py#L312)）→ [_EvaluationService](document_validation.md)，静态可定位。
- `service.provider`（[document_validation.py:327](../../../src/evaluation/document_validation.py#L327)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.vlm_provider`（[document_validation.py:328](../../../src/evaluation/document_validation.py#L328)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.embedding_provider`（[document_validation.py:331](../../../src/evaluation/document_validation.py#L331)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `provider.fingerprint`（[document_validation.py:332](../../../src/evaluation/document_validation.py#L332)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `manifest.get`（[document_validation.py:333](../../../src/evaluation/document_validation.py#L333)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `(manifest_path.parent / manifest['seed_kb']).resolve`（[document_validation.py:334](../../../src/evaluation/document_validation.py#L334)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `seed_path.read_text`（[document_validation.py:335](../../../src/evaluation/document_validation.py#L335)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CanonicalEntity.model_validate`（[document_validation.py:336](../../../src/evaluation/document_validation.py#L336)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `store.commit`（[document_validation.py:339](../../../src/evaluation/document_validation.py#L339)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphCommit`（[document_validation.py:340](../../../src/evaluation/document_validation.py#L340)）：来自 `src.domain.GraphCommit`；具体实现可能由依赖注入或运行时分派决定。
- `GraphRevision`（[document_validation.py:342](../../../src/evaluation/document_validation.py#L342)）：来自 `src.domain.GraphRevision`；具体实现可能由依赖注入或运行时分派决定。
- `rebuild_entity_index`（调用点 [document_validation.py:349](../../../src/evaluation/document_validation.py#L349)）→ [rebuild_entity_index](../governance/entity_index.md)，静态可定位。
- 此处列出前 30 个不同调用表达式，另有 28 个，需按源码继续追踪。
- 静态可定位的调用方：[validate_real_documents](../cli.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`report['embedding_fingerprint']`、`report['seed_entities']`、`report['seed_kb_sha256']`、`budget.case_id`、`service.cached_text_state`、`service.cached_ocr_state`、`report['cases'][-1]['run_id']`、`report['cases'][-1]['failed_node']`、`budget.stopped_reason`、`report['code_commit']`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`、`ValueError(f<字符串常量>id<字符串常量>)`、`RuntimeError(<字符串常量>)`。
- 本地捕获：`Exception`、`(OSError, subprocess.CalledProcessError)`。


---
