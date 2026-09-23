源码：[multimodal_extraction_agent.py:1](../../../src/agents/multimodal_extraction_agent.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：8

**模块职责**：MultimodalExtractionAgent with explicit tool choice and evidence handoff.
**在系统中的位置**：三个语义 Agent 及其预算、轨迹工具；把抽取、治理、融合审核的职责显式化，但不直接写图。
**阅读重点**：抽取 Agent 选择文本、视觉和对齐工具，保留证据 ID、模态失败状态及脱敏轨迹；某分支失败不可冒充空结果。
**直接依赖**：[src.agents.trace](trace.md)、[src.core.errors](../core/errors.md)、[src.core.execution_control](../core/execution_control.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.governance](../governance/__init__.md)、[src.parsing](../parsing/__init__.md)、[src.persistence.base](../persistence/base.md)、[src.providers.base](../providers/base.md)；外部/标准库：`__future__`、`time`。
**主要调用方（静态导入）**：[workflow/nodes.py](../workflow/nodes.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

## 核心路径解读

- `recognize` 在 OCR 禁用时标记 skipped；否则按 Provider 指纹与文档 ID 缓存结果，将新文本块/证据去重写回 DocumentIR。已知响应格式错误记为 failed，而不是把无候选当作成功。
- `extract_text` 在无文本块时跳过；成功后保留候选、ProviderCallRecord 与结构校验问题。调用缓存的逻辑请求键包含模型指纹与文档 ID，避免检查点重入时重复付费。
- `extract_visual` 每张分析资产前检查取消；提取与当前资产有关的 OCR 块，逐资产缓存 VLM 结果。某资产失败会留下 failed 状态，其他资产的候选、观察与证据仍保留。粗定位证据显式标为 coarse_visual_evidence。
- `align` 只在所有可用模态均失败时抛错；否则合并文本与视觉候选，并将候选 ID、证据 ID 和问题 ID 结构化交给下一 Agent。

---

# _known_response_failure ⭐⭐

**位置与等级**：[multimodal_extraction_agent.py:27](../../../src/agents/multimodal_extraction_agent.py#L27)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _known_response_failure(state: WorkflowState, exc: ProviderResponseError, modality: str) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`exc`（ProviderResponseError）；`modality`（str）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `records`，值来自 `getattr(exc, 'call_records', [])`。
2. 更新 `known`，值来自 `{item.id for item in state.provider_calls}`。
3. 调用 `state.provider_calls.extend`，结果未直接赋值。
4. 更新 `state.modality_status[modality]`，值来自 `'failed'`。
5. 更新 `state.modality_errors[modality]`，值来自 `'provider_response_invalid'`。
6. 调用 `state.warnings.append`，结果未直接赋值。

**调用与被调用**：
- `getattr`（[multimodal_extraction_agent.py:30](../../../src/agents/multimodal_extraction_agent.py#L30)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.provider_calls.extend`（[multimodal_extraction_agent.py:32](../../../src/agents/multimodal_extraction_agent.py#L32)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.warnings.append`（[multimodal_extraction_agent.py:35](../../../src/agents/multimodal_extraction_agent.py#L35)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[MultimodalExtractionAgent.recognize](multimodal_extraction_agent.md)、[MultimodalExtractionAgent.extract_text](multimodal_extraction_agent.md)、[MultimodalExtractionAgent.extract_visual](multimodal_extraction_agent.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.modality_status[modality]`、`state.modality_errors[modality]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# MultimodalExtractionAgent ⭐⭐⭐⭐

**位置与等级**：[multimodal_extraction_agent.py:38](../../../src/agents/multimodal_extraction_agent.py#L38)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：语义 Agent；通过受控工具和结构化状态交接完成本阶段任务，不能绕过硬校验。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`MultimodalExtractionAgent.__init__`、`MultimodalExtractionAgent.recognize`、`MultimodalExtractionAgent.extract_text`、`MultimodalExtractionAgent.extract_visual`、`MultimodalExtractionAgent.align`


---

# MultimodalExtractionAgent.__init__ ⭐⭐⭐⭐

**位置与等级**：[multimodal_extraction_agent.py:39](../../../src/agents/multimodal_extraction_agent.py#L39)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def __init__(self, provider: LLMProvider, ocr_provider: OCRProvider, vlm_provider: VLMProvider, evidence_store: EvidenceStore) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`provider`（LLMProvider）；`ocr_provider`（OCRProvider）；`vlm_provider`（VLMProvider）；`evidence_store`（EvidenceStore；证据元数据和原始内容的存储接口）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.provider`，值来自 `provider`。
2. 更新 `self.ocr_provider`，值来自 `ocr_provider`。
3. 更新 `self.vlm_provider`，值来自 `vlm_provider`。
4. 更新 `self.evidence_store`，值来自 `evidence_store`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.provider`、`self.ocr_provider`、`self.vlm_provider`、`self.evidence_store`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# MultimodalExtractionAgent.recognize ⭐⭐⭐⭐

**位置与等级**：[multimodal_extraction_agent.py:51](../../../src/agents/multimodal_extraction_agent.py#L51)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def recognize(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `recognize` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 断言 `state.document is not None`。
2. 更新 `started`，值来自 `perf_counter()`。
3. 检查 `self.ocr_provider.fingerprint() == 'disabled'`；按条件分流，else 分支不存在。
4. 更新 `request`，值来自 `OCRRequest(document=state.document)`。
5. 捕获 ProviderResponseError；另检查 finally/else 的清理和传播。
6. 更新 `existing`，值来自 `{block.id for block in state.document.text_blocks}`。
7. 调用 `state.document.text_blocks.extend`，结果未直接赋值。
8. 更新 `known_evidence`，值来自 `{item.id for item in state.document.evidence}`。
9. 调用 `state.document.evidence.extend`，结果未直接赋值。
10. 调用 `state.warnings.extend`，结果未直接赋值。
11. 更新 `state.modality_status['ocr']`，值来自 `'succeeded'`。
12. 调用 `trace_step`，结果未直接赋值。
13. 返回 `state`。

**关键条件与保护**：
- [multimodal_extraction_agent.py:54](../../../src/agents/multimodal_extraction_agent.py#L54)：`self.ocr_provider.fingerprint() == 'disabled'`，不满足时跳过本分支。

**调用与被调用**：
- `perf_counter`（[multimodal_extraction_agent.py:53](../../../src/agents/multimodal_extraction_agent.py#L53)）：来自 `time.perf_counter`；具体实现可能由依赖注入或运行时分派决定。
- `self.ocr_provider.fingerprint`（[multimodal_extraction_agent.py:54](../../../src/agents/multimodal_extraction_agent.py#L54)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `trace_step`（调用点 [multimodal_extraction_agent.py:56](../../../src/agents/multimodal_extraction_agent.py#L56)）→ [trace_step](trace.md)，静态可定位。
- `OCRRequest`（[multimodal_extraction_agent.py:58](../../../src/agents/multimodal_extraction_agent.py#L58)）：来自 `src.domain.OCRRequest`；具体实现可能由依赖注入或运行时分派决定。
- `cached_operation`（调用点 [multimodal_extraction_agent.py:60](../../../src/agents/multimodal_extraction_agent.py#L60)）→ [cached_operation](../core/execution_control.md)，静态可定位。
- `stable_id`（调用点 [multimodal_extraction_agent.py:61](../../../src/agents/multimodal_extraction_agent.py#L61)）→ [stable_id](../core/ids.md)，静态可定位。
- `_known_response_failure`（调用点 [multimodal_extraction_agent.py:66](../../../src/agents/multimodal_extraction_agent.py#L66)）→ [_known_response_failure](multimodal_extraction_agent.md)，静态可定位。
- `state.document.text_blocks.extend`（[multimodal_extraction_agent.py:78](../../../src/agents/multimodal_extraction_agent.py#L78)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.document.evidence.extend`（[multimodal_extraction_agent.py:82](../../../src/agents/multimodal_extraction_agent.py#L82)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.warnings.extend`（[multimodal_extraction_agent.py:85](../../../src/agents/multimodal_extraction_agent.py#L85)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `tuple`（[multimodal_extraction_agent.py:94](../../../src/agents/multimodal_extraction_agent.py#L94)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.modality_status['ocr']`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`ProviderResponseError`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# MultimodalExtractionAgent.extract_text ⭐⭐⭐⭐

**位置与等级**：[multimodal_extraction_agent.py:100](../../../src/agents/multimodal_extraction_agent.py#L100)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def extract_text(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `extract_text` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 断言 `state.document is not None and state.output_schema is not None`。
2. 更新 `started`，值来自 `perf_counter()`。
3. 检查 `not state.document.text_blocks`；按条件分流，else 分支不存在。
4. 更新 `request`，值来自 `ExtractionRequest(document=state.document, output_schema=state.output_schema)`。
5. 捕获 ProviderResponseError；另检查 finally/else 的清理和传播。
6. 更新 `state.text_candidates`，值来自 `result.candidates`。
7. 调用 `state.warnings.extend`，结果未直接赋值。
8. 调用 `state.provider_calls.extend`，结果未直接赋值。
9. 更新 `state.validation`，值来自 `ValidationService.merge(state.validation, result.validation.issues)`。
10. 更新 `state.modality_status['text']`，值来自 `'succeeded'`。
11. 调用 `trace_step`，结果未直接赋值。
12. 返回 `state`。

**关键条件与保护**：
- [multimodal_extraction_agent.py:103](../../../src/agents/multimodal_extraction_agent.py#L103)：`not state.document.text_blocks`，不满足时跳过本分支。

**调用与被调用**：
- `perf_counter`（[multimodal_extraction_agent.py:102](../../../src/agents/multimodal_extraction_agent.py#L102)）：来自 `time.perf_counter`；具体实现可能由依赖注入或运行时分派决定。
- `state.warnings.append`（[multimodal_extraction_agent.py:106](../../../src/agents/multimodal_extraction_agent.py#L106)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `trace_step`（调用点 [multimodal_extraction_agent.py:107](../../../src/agents/multimodal_extraction_agent.py#L107)）→ [trace_step](trace.md)，静态可定位。
- `ExtractionRequest`（[multimodal_extraction_agent.py:109](../../../src/agents/multimodal_extraction_agent.py#L109)）：来自 `src.domain.ExtractionRequest`；具体实现可能由依赖注入或运行时分派决定。
- `cached_operation`（调用点 [multimodal_extraction_agent.py:111](../../../src/agents/multimodal_extraction_agent.py#L111)）→ [cached_operation](../core/execution_control.md)，静态可定位。
- `stable_id`（调用点 [multimodal_extraction_agent.py:112](../../../src/agents/multimodal_extraction_agent.py#L112)）→ [stable_id](../core/ids.md)，静态可定位。
- `self.provider.fingerprint`（[multimodal_extraction_agent.py:112](../../../src/agents/multimodal_extraction_agent.py#L112)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_known_response_failure`（调用点 [multimodal_extraction_agent.py:117](../../../src/agents/multimodal_extraction_agent.py#L117)）→ [_known_response_failure](multimodal_extraction_agent.md)，静态可定位。
- `state.warnings.extend`（[multimodal_extraction_agent.py:129](../../../src/agents/multimodal_extraction_agent.py#L129)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.provider_calls.extend`（[multimodal_extraction_agent.py:130](../../../src/agents/multimodal_extraction_agent.py#L130)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService.merge`（[multimodal_extraction_agent.py:133](../../../src/agents/multimodal_extraction_agent.py#L133)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `tuple`（[multimodal_extraction_agent.py:142](../../../src/agents/multimodal_extraction_agent.py#L142)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sum`（[multimodal_extraction_agent.py:144](../../../src/agents/multimodal_extraction_agent.py#L144)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.text_candidates`、`state.modality_status['text']`、`state.validation`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`ProviderResponseError`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# MultimodalExtractionAgent.extract_visual ⭐⭐⭐⭐

**位置与等级**：[multimodal_extraction_agent.py:149](../../../src/agents/multimodal_extraction_agent.py#L149)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def extract_visual(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `extract_visual` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 断言 `state.document is not None and state.output_schema is not None`。
2. 更新 `started`，值来自 `perf_counter()`。
3. 更新 `state.visual_candidates`，值来自 `[]`。
4. 更新 `assets`，值来自 `select_analysis_assets(state.document)`。
5. 检查 `not assets or self.vlm_provider.fingerprint() == 'disabled'`；按条件分流，else 分支不存在。
6. 更新 `failed_assets`，值来自 `[]`。
7. 更新 `call_records`，值来自 `[]`。
8. 遍历 `assets`，逐项处理 `asset`。
9. 检查 `failed_assets`；按条件分流，else 分支存在。
10. 调用 `trace_step`，结果未直接赋值。
11. 返回 `state`。

**关键条件与保护**：
- [multimodal_extraction_agent.py:154](../../../src/agents/multimodal_extraction_agent.py#L154)：`not assets or self.vlm_provider.fingerprint() == 'disabled'`，不满足时跳过本分支。
- [multimodal_extraction_agent.py:191](../../../src/agents/multimodal_extraction_agent.py#L191)：`any((evidence_by_id[item].localization_level == LocalizationLevel.ASSET for item in candidate.evidence_ids if item…`，不满足时跳过本分支。
- [multimodal_extraction_agent.py:208](../../../src/agents/multimodal_extraction_agent.py#L208)：`failed_assets`，不满足时有 else 分支。

**调用与被调用**：
- `perf_counter`（[multimodal_extraction_agent.py:151](../../../src/agents/multimodal_extraction_agent.py#L151)）：来自 `time.perf_counter`；具体实现可能由依赖注入或运行时分派决定。
- `select_analysis_assets`（[multimodal_extraction_agent.py:153](../../../src/agents/multimodal_extraction_agent.py#L153)）：来自 `src.parsing.select_analysis_assets`；具体实现可能由依赖注入或运行时分派决定。
- `self.vlm_provider.fingerprint`（[multimodal_extraction_agent.py:154](../../../src/agents/multimodal_extraction_agent.py#L154)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `trace_step`（调用点 [multimodal_extraction_agent.py:156](../../../src/agents/multimodal_extraction_agent.py#L156)）→ [trace_step](trace.md)，静态可定位。
- `check_execution`（调用点 [multimodal_extraction_agent.py:161](../../../src/agents/multimodal_extraction_agent.py#L161)）→ [check_execution](../core/execution_control.md)，静态可定位。
- `VisualExtractionRequest`（[multimodal_extraction_agent.py:167](../../../src/agents/multimodal_extraction_agent.py#L167)）：来自 `src.domain.VisualExtractionRequest`；具体实现可能由依赖注入或运行时分派决定。
- `cached_operation`（调用点 [multimodal_extraction_agent.py:178](../../../src/agents/multimodal_extraction_agent.py#L178)）→ [cached_operation](../core/execution_control.md)，静态可定位。
- `stable_id`（调用点 [multimodal_extraction_agent.py:179](../../../src/agents/multimodal_extraction_agent.py#L179)）→ [stable_id](../core/ids.md)，静态可定位。
- `_known_response_failure`（调用点 [multimodal_extraction_agent.py:184](../../../src/agents/multimodal_extraction_agent.py#L184)）→ [_known_response_failure](multimodal_extraction_agent.md)，静态可定位。
- `failed_assets.append`（[multimodal_extraction_agent.py:185](../../../src/agents/multimodal_extraction_agent.py#L185)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[multimodal_extraction_agent.py:191](../../../src/agents/multimodal_extraction_agent.py#L191)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.visual_candidates.extend`（[multimodal_extraction_agent.py:197](../../../src/agents/multimodal_extraction_agent.py#L197)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.document.visual_observations.extend`（[multimodal_extraction_agent.py:198](../../../src/agents/multimodal_extraction_agent.py#L198)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.evidence_store.put_ref`（[multimodal_extraction_agent.py:200](../../../src/agents/multimodal_extraction_agent.py#L200)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.document.evidence.append`（[multimodal_extraction_agent.py:201](../../../src/agents/multimodal_extraction_agent.py#L201)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.warnings.extend`（[multimodal_extraction_agent.py:202](../../../src/agents/multimodal_extraction_agent.py#L202)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.provider_calls.extend`（[multimodal_extraction_agent.py:203](../../../src/agents/multimodal_extraction_agent.py#L203)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `call_records.extend`（[multimodal_extraction_agent.py:204](../../../src/agents/multimodal_extraction_agent.py#L204)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService.merge`（[multimodal_extraction_agent.py:207](../../../src/agents/multimodal_extraction_agent.py#L207)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `len`（[multimodal_extraction_agent.py:210](../../../src/agents/multimodal_extraction_agent.py#L210)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `tuple`（[multimodal_extraction_agent.py:219](../../../src/agents/multimodal_extraction_agent.py#L219)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sum`（[multimodal_extraction_agent.py:223](../../../src/agents/multimodal_extraction_agent.py#L223)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.visual_candidates`、`state.modality_status['visual']`、`candidate.coarse_visual_evidence`、`state.validation`、`state.modality_errors['visual']`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`ProviderResponseError`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# MultimodalExtractionAgent.extract_visual.visual_call ⭐⭐⭐⭐

**位置与等级**：[multimodal_extraction_agent.py:174](../../../src/agents/multimodal_extraction_agent.py#L174)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def visual_call(req: VisualExtractionRequest=request) -> ExtractionResult`。

**作用**：处理 `visual_call` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`req`（VisualExtractionRequest；默认 `request`）。
- 输出类型：`ExtractionResult`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self.vlm_provider.extract(req)`。

**调用与被调用**：
- `self.vlm_provider.extract`（[multimodal_extraction_agent.py:175](../../../src/agents/multimodal_extraction_agent.py#L175)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# MultimodalExtractionAgent.align ⭐⭐⭐⭐

**位置与等级**：[multimodal_extraction_agent.py:229](../../../src/agents/multimodal_extraction_agent.py#L229)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def align(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `align` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 断言 `state.output_schema is not None`。
2. 更新 `statuses`，值来自 `[state.modality_status.get(name) for name in ('ocr', 'text', 'visual')]`。
3. 检查 `'failed' in statuses and 'succeeded' not in statuses`；按条件分流，else 分支不存在。
4. 更新 `(state.candidates, state.alignment_records)`，值来自 `MultimodalAlignmentService().align(state.text_candidates, state.visual_candidates, SchemaIndex(stat…`。
5. 调用 `trace_step`，结果未直接赋值。
6. 调用 `handoff`，结果未直接赋值。
7. 返回 `state`。

**关键条件与保护**：
- [multimodal_extraction_agent.py:232](../../../src/agents/multimodal_extraction_agent.py#L232)：`'failed' in statuses and 'succeeded' not in statuses`，不满足时跳过本分支。

**调用与被调用**：
- `state.modality_status.get`（[multimodal_extraction_agent.py:231](../../../src/agents/multimodal_extraction_agent.py#L231)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ProviderResponseError`（调用点 [multimodal_extraction_agent.py:233](../../../src/agents/multimodal_extraction_agent.py#L233)）→ [ProviderResponseError](../core/errors.md)，静态可定位。
- `MultimodalAlignmentService().align`（[multimodal_extraction_agent.py:234](../../../src/agents/multimodal_extraction_agent.py#L234)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `MultimodalAlignmentService`（[multimodal_extraction_agent.py:234](../../../src/agents/multimodal_extraction_agent.py#L234)）：来自 `src.governance.MultimodalAlignmentService`；具体实现可能由依赖注入或运行时分派决定。
- `SchemaIndex`（[multimodal_extraction_agent.py:235](../../../src/agents/multimodal_extraction_agent.py#L235)）：来自 `src.domain.SchemaIndex`；具体实现可能由依赖注入或运行时分派决定。
- `trace_step`（调用点 [multimodal_extraction_agent.py:237](../../../src/agents/multimodal_extraction_agent.py#L237)）→ [trace_step](trace.md)，静态可定位。
- `tuple`（[multimodal_extraction_agent.py:243](../../../src/agents/multimodal_extraction_agent.py#L243)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `handoff`（调用点 [multimodal_extraction_agent.py:248](../../../src/agents/multimodal_extraction_agent.py#L248)）→ [handoff](trace.md)，静态可定位。
- `sorted`（[multimodal_extraction_agent.py:254](../../../src/agents/multimodal_extraction_agent.py#L254)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderResponseError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
