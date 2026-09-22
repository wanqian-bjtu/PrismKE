源码：[nodes.py:1](../../../src/workflow/nodes.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：18

**模块职责**：Workflow node implementations.
**在系统中的位置**：应用服务、LangGraph 编排、执行状态、审核接续、图提交及纠正流程。
**阅读重点**：节点将结构化 WorkflowState 交给相应 Agent 或确定性服务；prepare_graph_commit 负责准备提交，commit_graph 才触及存储。不要把预览看成已提交。
**直接依赖**：[src.agents.entity_governance_agent](../agents/entity_governance_agent.md)、[src.agents.fusion_review_agent](../agents/fusion_review_agent.md)、[src.agents.multimodal_extraction_agent](../agents/multimodal_extraction_agent.md)、[src.core.errors](../core/errors.md)、[src.core.execution_control](../core/execution_control.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.governance](../governance/__init__.md)、[src.governance.validation](../governance/validation/__init__.md)、[src.parsing](../parsing/__init__.md)、[src.persistence.base](../persistence/base.md)、[src.persistence.reviews](../persistence/reviews.md)、[src.providers.base](../providers/base.md)、[src.providers.embedding](../providers/embedding.md)、[src.providers.semantic](../providers/semantic.md)、[src.workflow.reflection](reflection.md)；外部/标准库：`__future__`、`pathlib`。
**主要调用方（静态导入）**：[workflow/graph.py](graph.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

## 核心路径解读

- 前段节点准备 DocumentIR、媒体资产、OCR 文本、证据与 Schema；抽取/对齐/实体治理/融合审核分别转交对应 Agent。节点粒度让检查点和取消停在明确位置。
- `prepare_graph_commit` 收集 Document、Evidence、Entity、Claim、Conflict、Revision 及校验上下文。只构造待提交事务；审核工作区还需要人工确认。
- `commit_graph` 进入最终 GraphStore 边界；预览后证据或父版本变化仍要靠存储层重新校验，不能信任预览快照。

---

# WorkflowNodes ⭐⭐⭐⭐

**位置与等级**：[nodes.py:42](../../../src/workflow/nodes.py#L42)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- `review_repository`：`ReviewRepository | None`；默认 `None`。

**内部成员**：`WorkflowNodes.__init__`、`WorkflowNodes.ingest`、`WorkflowNodes.parse_document`、`WorkflowNodes.materialize_visual_assets`、`WorkflowNodes.run_ocr`、`WorkflowNodes.persist_evidence`、`WorkflowNodes.load_schema`、`WorkflowNodes.extract_text_claims`、`WorkflowNodes.extract_visual_claims`、`WorkflowNodes.align_modalities`、`WorkflowNodes.reflect_candidates`、`WorkflowNodes.resolve_entities`、`WorkflowNodes.normalize_claims`、`WorkflowNodes.detect_conflicts`、`WorkflowNodes.route_by_risk`、`WorkflowNodes.prepare_graph_commit`、`WorkflowNodes.commit_graph`


---

# WorkflowNodes.__init__ ⭐⭐

**位置与等级**：[nodes.py:45](../../../src/workflow/nodes.py#L45)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, provider: LLMProvider, ocr_provider: OCRProvider, vlm_provider: VLMProvider, graph_store: GraphStore, evidence_store: EvidenceStore, parsers: ParserRegistry, *, embedding_provider: EmbeddingProvider | None=None, entity_top_k: int=10, entity_auto_link_threshold: float=0.88, entity_review_threshold: float=0.65, entity_min_margin: float=0.08, reflection_service: BoundedReflectionService | None=None, semantic_advisor: SemanticAdvisor | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`provider`（LLMProvider）；`ocr_provider`（OCRProvider）；`vlm_provider`（VLMProvider）；`graph_store`（GraphStore；图持久化接口，具体实现由配置注入）；`evidence_store`（EvidenceStore；证据元数据和原始内容的存储接口）；`parsers`（ParserRegistry）；`embedding_provider`（EmbeddingProvider | None；默认 `None`）；`entity_top_k`（int；默认 `10`）；`entity_auto_link_threshold`（float；默认 `0.88`）；`entity_review_threshold`（float；默认 `0.65`）；`entity_min_margin`（float；默认 `0.08`）；`reflection_service`（BoundedReflectionService | None；默认 `None`）；`semantic_advisor`（SemanticAdvisor | None；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.provider`，值来自 `provider`。
2. 更新 `self.ocr_provider`，值来自 `ocr_provider`。
3. 更新 `self.vlm_provider`，值来自 `vlm_provider`。
4. 更新 `self.embedding_provider`，值来自 `embedding_provider or DisabledEmbeddingProvider()`。
5. 更新 `self.graph_store`，值来自 `graph_store`。
6. 更新 `self.evidence_store`，值来自 `evidence_store`。
7. 更新 `self.parsers`，值来自 `parsers`。
8. 更新 `self.entity_top_k`，值来自 `entity_top_k`。
9. 更新 `self.entity_auto_link_threshold`，值来自 `entity_auto_link_threshold`。
10. 更新 `self.entity_review_threshold`，值来自 `entity_review_threshold`。
11. 更新 `self.entity_min_margin`，值来自 `entity_min_margin`。
12. 更新 `self.reflection_service`，值来自 `reflection_service`。
13. 更新 `advisor`，值来自 `semantic_advisor or DisabledSemanticAdvisor()`。
14. 更新 `self.extraction_agent`，值来自 `MultimodalExtractionAgent(provider, ocr_provider, vlm_provider, evidence_store)`。
15. 更新 `self.governance_agent`，值来自 `EntityGovernanceAgent(graph_store, evidence_store, self.embedding_provider, advisor, top_k=entity_t…`。
16. 更新 `self.fusion_agent`，值来自 `FusionReviewAgent(graph_store, advisor, reflection_service)`。

**调用与被调用**：
- `DisabledEmbeddingProvider`（调用点 [nodes.py:65](../../../src/workflow/nodes.py#L65)）→ [DisabledEmbeddingProvider](../providers/embedding.md)，静态可定位。
- `DisabledSemanticAdvisor`（调用点 [nodes.py:74](../../../src/workflow/nodes.py#L74)）→ [DisabledSemanticAdvisor](../providers/semantic.md)，静态可定位。
- `MultimodalExtractionAgent`（调用点 [nodes.py:75](../../../src/workflow/nodes.py#L75)）→ [MultimodalExtractionAgent](../agents/multimodal_extraction_agent.md)，静态可定位。
- `EntityGovernanceAgent`（调用点 [nodes.py:78](../../../src/workflow/nodes.py#L78)）→ [EntityGovernanceAgent](../agents/entity_governance_agent.md)，静态可定位。
- `FusionReviewAgent`（调用点 [nodes.py:88](../../../src/workflow/nodes.py#L88)）→ [FusionReviewAgent](../agents/fusion_review_agent.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.provider`、`self.ocr_provider`、`self.vlm_provider`、`self.embedding_provider`、`self.graph_store`、`self.evidence_store`、`self.parsers`、`self.entity_top_k`、`self.entity_auto_link_threshold`、`self.entity_review_threshold`、`self.entity_min_margin`、`self.reflection_service`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.ingest ⭐⭐

**位置与等级**：[nodes.py:90](../../../src/workflow/nodes.py#L90)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def ingest(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `ingest` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not SourceDocument(path=state.input_path).path.is_file()`；按条件分流，else 分支不存在。
2. 返回 `state`。

**关键条件与保护**：
- [nodes.py:91](../../../src/workflow/nodes.py#L91)：`not SourceDocument(path=state.input_path).path.is_file()`，不满足时跳过本分支。

**调用与被调用**：
- `SourceDocument(path=state.input_path).path.is_file`（[nodes.py:91](../../../src/workflow/nodes.py#L91)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `SourceDocument`（[nodes.py:91](../../../src/workflow/nodes.py#L91)）：来自 `src.domain.SourceDocument`；具体实现可能由依赖注入或运行时分派决定。
- `FileNotFoundError`（[nodes.py:92](../../../src/workflow/nodes.py#L92)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`FileNotFoundError(state.input_path)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.parse_document ⭐⭐

**位置与等级**：[nodes.py:95](../../../src/workflow/nodes.py#L95)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def parse_document(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `parse_document` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state.document`，值来自 `await self.parsers.parse(SourceDocument(path=state.input_path))`。
2. 调用 `state.warnings.extend`，结果未直接赋值。
3. 返回 `state`。

**调用与被调用**：
- `self.parsers.parse`（[nodes.py:96](../../../src/workflow/nodes.py#L96)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `SourceDocument`（[nodes.py:96](../../../src/workflow/nodes.py#L96)）：来自 `src.domain.SourceDocument`；具体实现可能由依赖注入或运行时分派决定。
- `state.warnings.extend`（[nodes.py:97](../../../src/workflow/nodes.py#L97)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.document`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.materialize_visual_assets ⭐⭐

**位置与等级**：[nodes.py:100](../../../src/workflow/nodes.py#L100)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def materialize_visual_assets(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `materialize_visual_assets` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 断言 `state.document is not None`。
2. 更新 `missing`，值来自 `[asset.id for asset in state.document.media_assets if not Path(asset.path).is_file()]`。
3. 检查 `missing`；按条件分流，else 分支不存在。
4. 返回 `state`。

**关键条件与保护**：
- [nodes.py:105](../../../src/workflow/nodes.py#L105)：`missing`，不满足时跳过本分支。

**调用与被调用**：
- `Path(asset.path).is_file`（[nodes.py:103](../../../src/workflow/nodes.py#L103)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Path`（[nodes.py:103](../../../src/workflow/nodes.py#L103)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `EvidenceIntegrityError`（调用点 [nodes.py:106](../../../src/workflow/nodes.py#L106)）→ [EvidenceIntegrityError](../core/errors.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`EvidenceIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.run_ocr ⭐⭐⭐⭐

**位置与等级**：[nodes.py:109](../../../src/workflow/nodes.py#L109)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def run_ocr(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `run_ocr` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self.extraction_agent.recognize(state)`。

**调用与被调用**：
- `self.extraction_agent.recognize`（[nodes.py:110](../../../src/workflow/nodes.py#L110)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.persist_evidence ⭐⭐

**位置与等级**：[nodes.py:112](../../../src/workflow/nodes.py#L112)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def persist_evidence(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `persist_evidence` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 断言 `state.document is not None`。
2. 等待 `self.evidence_store.put_document(state.document)` 完成。
3. 返回 `state`。

**调用与被调用**：
- `self.evidence_store.put_document`（[nodes.py:114](../../../src/workflow/nodes.py#L114)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.load_schema ⭐⭐

**位置与等级**：[nodes.py:117](../../../src/workflow/nodes.py#L117)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def load_schema(self, state: WorkflowState) -> WorkflowState`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state.output_schema`，值来自 `load_schema(SourceDocument(path=state.schema_path).path)`。
2. 返回 `state`。

**调用与被调用**：
- `load_schema`（[nodes.py:118](../../../src/workflow/nodes.py#L118)）：来自 `src.domain.load_schema`；具体实现可能由依赖注入或运行时分派决定。
- `SourceDocument`（[nodes.py:118](../../../src/workflow/nodes.py#L118)）：来自 `src.domain.SourceDocument`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.output_schema`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.extract_text_claims ⭐⭐⭐⭐

**位置与等级**：[nodes.py:121](../../../src/workflow/nodes.py#L121)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def extract_text_claims(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `extract_text_claims` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self.extraction_agent.extract_text(state)`。

**调用与被调用**：
- `self.extraction_agent.extract_text`（[nodes.py:122](../../../src/workflow/nodes.py#L122)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.extract_visual_claims ⭐⭐⭐⭐

**位置与等级**：[nodes.py:124](../../../src/workflow/nodes.py#L124)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def extract_visual_claims(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `extract_visual_claims` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self.extraction_agent.extract_visual(state)`。

**调用与被调用**：
- `self.extraction_agent.extract_visual`（[nodes.py:125](../../../src/workflow/nodes.py#L125)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.align_modalities ⭐⭐

**位置与等级**：[nodes.py:127](../../../src/workflow/nodes.py#L127)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def align_modalities(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `align_modalities` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self.extraction_agent.align(state)`。

**调用与被调用**：
- `self.extraction_agent.align`（[nodes.py:128](../../../src/workflow/nodes.py#L128)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.reflect_candidates ⭐⭐⭐⭐⭐

**位置与等级**：[nodes.py:130](../../../src/workflow/nodes.py#L130)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`async def reflect_candidates(self, state: WorkflowState) -> WorkflowState`。

**作用**：处理 `reflect_candidates` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self.fusion_agent.triage_candidates(state)`。

**调用与被调用**：
- `self.fusion_agent.triage_candidates`（[nodes.py:131](../../../src/workflow/nodes.py#L131)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.resolve_entities ⭐⭐⭐⭐

**位置与等级**：[nodes.py:133](../../../src/workflow/nodes.py#L133)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def resolve_entities(self, state: WorkflowState) -> WorkflowState`。

**作用**：将提及映射到规范实体或审核任务；未确认草稿不得污染正式候选库。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self.governance_agent.resolve(state)`。

**调用与被调用**：
- `self.governance_agent.resolve`（[nodes.py:134](../../../src/workflow/nodes.py#L134)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.normalize_claims ⭐⭐⭐⭐

**位置与等级**：[nodes.py:136](../../../src/workflow/nodes.py#L136)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def normalize_claims(self, state: WorkflowState) -> WorkflowState`。

**作用**：将实体提及和候选关系规范化为 Claim，同时保留证据来源。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self.governance_agent.normalize(state)`。

**调用与被调用**：
- `self.governance_agent.normalize`（[nodes.py:137](../../../src/workflow/nodes.py#L137)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.detect_conflicts ⭐⭐⭐⭐

**位置与等级**：[nodes.py:139](../../../src/workflow/nodes.py#L139)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def detect_conflicts(self, state: WorkflowState) -> WorkflowState`。

**作用**：对规范事实做支持/冲突识别，不由冲突分数直接替代人工审核。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self.fusion_agent.detect_conflicts(state)`。

**调用与被调用**：
- `self.fusion_agent.detect_conflicts`（[nodes.py:140](../../../src/workflow/nodes.py#L140)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.route_by_risk ⭐⭐

**位置与等级**：[nodes.py:142](../../../src/workflow/nodes.py#L142)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def route_by_risk(self, state: WorkflowState) -> WorkflowState`。

**作用**：按风险规则决定后续审核或提交路径，不直接更改原始证据。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.fusion_agent.review_repository`，值来自 `self.review_repository`。
2. 返回 `await self.fusion_agent.route_by_risk(state)`。

**调用与被调用**：
- `self.fusion_agent.route_by_risk`（[nodes.py:144](../../../src/workflow/nodes.py#L144)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.fusion_agent.review_repository`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.prepare_graph_commit ⭐⭐⭐⭐⭐

**位置与等级**：[nodes.py:146](../../../src/workflow/nodes.py#L146)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`async def prepare_graph_commit(self, state: WorkflowState) -> WorkflowState`。

**作用**：准备图提交和预览；它与实际事务提交是两个边界。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 断言 `state.document is not None`。
2. 检查 `state.validation.blocking_count`；按条件分流，else 分支不存在。
3. 断言 `state.output_schema is not None`。
4. 更新 `accepted`，值来自 `[claim for claim in state.claims if claim.status in {ClaimStatus.AUTO_APPROVED, ClaimStatus.APPROVE…`。
5. 遍历 `accepted`，逐项处理 `claim`。
6. 更新 `existing_claims`，值来自 `{claim.id: claim for claim in await self.graph_store.list_claims()}`。
7. 更新 `existing_entities`，值来自 `{entity.id: entity for entity in await self.graph_store.list_entities()}`。
8. 更新 `existing_claim_ids`，值来自 `set(existing_claims)`。
9. 更新 `persisted_claim_ids`，值来自 `existing_claim_ids | {claim.id for claim in accepted}`。
10. 更新 `conflicts`，值来自 `[item for item in state.conflicts if set(item.claim_ids) <= persisted_claim_ids]`。
11. 更新 `parent`，值来自 `await self.graph_store.latest_revision()`。
12. 更新 `entity_ids`，值来自 `{entity_id for claim in accepted for entity_id in (claim.subject_id, claim.object_entity_id) if ent…`。
13. 更新 `entities`，值来自 `[entity.model_copy(update={'active': True}) for entity in state.entities if entity.id in entity_ids]`。
14. 更新 `changes`，值来自 `[GraphChange(resource_type='entity', resource_id=entity.id, action='update' if entity.id in existin…`。
15. 调用 `changes.extend`，结果未直接赋值。
16. 调用 `changes.extend`，结果未直接赋值。
17. 更新 `revision`，值来自 `GraphRevision(id=stable_id('revision', state.run_id, parent.id if parent else 'root', *sorted((clai…`。
18. 更新 `state.revision`，值来自 `revision`。
19. 更新 `schema_id`，值来自 `canonical_hash(state.output_schema.model_dump(mode='json'))`。
20. 更新 `context`，值来自 `CommitValidationContext(schemas={schema_id: state.output_schema}, claim_schema_ids={claim.id: schem…`。
21. 更新 `revision.validation_context`，值来自 `context`。
22. 更新 `state.graph_commit`，值来自 `GraphCommit(documents=[GraphDocument(id=state.document.id, filename=state.document.source_filename …`。
23. 检查 `state.pending_correction_id and self.review_repository is not None`；按条件分流，else 分支不存在。
24. 等待 `ValidationService().commit(state.graph_commit, {**existing_entities, **{e.id: e for e in entities}}, {e.…` 完成。
后续还有 1 个语句级步骤，见源码对应行；这里优先保留主要控制流。

**关键条件与保护**：
- [nodes.py:148](../../../src/workflow/nodes.py#L148)：`state.validation.blocking_count`，不满足时跳过本分支。
- [nodes.py:259](../../../src/workflow/nodes.py#L259)：`state.pending_correction_id and self.review_repository is not None`，不满足时跳过本分支。

**调用与被调用**：
- `GraphIntegrityError`（调用点 [nodes.py:149](../../../src/workflow/nodes.py#L149)）→ [GraphIntegrityError](../core/errors.md)，静态可定位。
- `sorted`（[nodes.py:159](../../../src/workflow/nodes.py#L159)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[nodes.py:159](../../../src/workflow/nodes.py#L159)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.list_claims`（[nodes.py:160](../../../src/workflow/nodes.py#L160)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.list_entities`（[nodes.py:161](../../../src/workflow/nodes.py#L161)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.latest_revision`（[nodes.py:165](../../../src/workflow/nodes.py#L165)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `entity.model_copy`（[nodes.py:173](../../../src/workflow/nodes.py#L173)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphChange`（[nodes.py:178](../../../src/workflow/nodes.py#L178)）：来自 `src.domain.GraphChange`；具体实现可能由依赖注入或运行时分派决定。
- `existing_entities[entity.id].model_dump`（[nodes.py:183](../../../src/workflow/nodes.py#L183)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `entity.model_dump`（[nodes.py:187](../../../src/workflow/nodes.py#L187)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `changes.extend`（[nodes.py:191](../../../src/workflow/nodes.py#L191)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `existing_claims[claim.id].model_dump`（[nodes.py:197](../../../src/workflow/nodes.py#L197)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `claim.model_dump`（[nodes.py:201](../../../src/workflow/nodes.py#L201)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `conflict.model_dump`（[nodes.py:210](../../../src/workflow/nodes.py#L210)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphRevision`（[nodes.py:214](../../../src/workflow/nodes.py#L214)）：来自 `src.domain.GraphRevision`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [nodes.py:215](../../../src/workflow/nodes.py#L215)）→ [stable_id](../core/ids.md)，静态可定位。
- `canonical_hash`（调用点 [nodes.py:229](../../../src/workflow/nodes.py#L229)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `state.output_schema.model_dump`（[nodes.py:229](../../../src/workflow/nodes.py#L229)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CommitValidationContext`（[nodes.py:230](../../../src/workflow/nodes.py#L230)）：来自 `src.domain.CommitValidationContext`；具体实现可能由依赖注入或运行时分派决定。
- `GraphCommit`（[nodes.py:236](../../../src/workflow/nodes.py#L236)）：来自 `src.domain.GraphCommit`；具体实现可能由依赖注入或运行时分派决定。
- `GraphDocument`（[nodes.py:238](../../../src/workflow/nodes.py#L238)）：来自 `src.domain.GraphDocument`；具体实现可能由依赖注入或运行时分派决定。
- `Path`（[nodes.py:241](../../../src/workflow/nodes.py#L241)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `compensation_commit`（调用点 [nodes.py:262](../../../src/workflow/nodes.py#L262)）→ [compensation_commit](corrections.md)，静态可定位。
- `self.review_repository.correction`（[nodes.py:265](../../../src/workflow/nodes.py#L265)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService().commit`（[nodes.py:270](../../../src/workflow/nodes.py#L270)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService`（[nodes.py:270](../../../src/workflow/nodes.py#L270)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`claim.source_run_ids`、`state.revision`、`revision.validation_context`、`state.graph_commit`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`GraphIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# WorkflowNodes.commit_graph ⭐⭐⭐⭐⭐

**位置与等级**：[nodes.py:279](../../../src/workflow/nodes.py#L279)；位于工作流推进、硬校验或原子事务的关键边界；错误可能影响审核停顿或图状态。

**签名**：`async def commit_graph(self, state: WorkflowState) -> WorkflowState`。

**作用**：在最终确认及硬校验后调用 GraphStore 写图。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 断言 `state.graph_commit is not None`。
2. 遍历 `state.graph_commit.claims`，逐项处理 `claim`。
3. 更新 `control`，值来自 `current_execution.get()`。
4. 检查 `control`；按条件分流，else 分支不存在。
5. 等待 `self.graph_store.commit(state.graph_commit)` 完成。
6. 检查 `control`；按条件分流，else 分支不存在。
7. 检查 `self.embedding_provider.fingerprint() != 'embedding:disabled' and state.graph_commit.entities`；按条件分流，else 分支不存在。
8. 更新 `state.status`，值来自 `'completed'`。
9. 返回 `state`。

**关键条件与保护**：
- [nodes.py:283](../../../src/workflow/nodes.py#L283)：`not await self.evidence_store.verify(evidence_id)`，不满足时跳过本分支。
- [nodes.py:288](../../../src/workflow/nodes.py#L288)：`control`，不满足时跳过本分支。
- [nodes.py:291](../../../src/workflow/nodes.py#L291)：`control`，不满足时跳过本分支。
- [nodes.py:293](../../../src/workflow/nodes.py#L293)：`self.embedding_provider.fingerprint() != 'embedding:disabled' and state.graph_commit.entities`，不满足时跳过本分支。

**调用与被调用**：
- `self.evidence_store.verify`（[nodes.py:283](../../../src/workflow/nodes.py#L283)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EvidenceIntegrityError`（调用点 [nodes.py:284](../../../src/workflow/nodes.py#L284)）→ [EvidenceIntegrityError](../core/errors.md)，静态可定位。
- `current_execution.get`（[nodes.py:287](../../../src/workflow/nodes.py#L287)）：来自 `src.core.execution_control.current_execution`；具体实现可能由依赖注入或运行时分派决定。
- `control.commit_started`（[nodes.py:289](../../../src/workflow/nodes.py#L289)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.commit`（[nodes.py:290](../../../src/workflow/nodes.py#L290)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `control.commit_finished`（[nodes.py:292](../../../src/workflow/nodes.py#L292)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.embedding_provider.fingerprint`（[nodes.py:294](../../../src/workflow/nodes.py#L294)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `entity_embedding_text`（[nodes.py:298](../../../src/workflow/nodes.py#L298)）：来自 `src.governance.entity_embedding_text`；具体实现可能由依赖注入或运行时分派决定。
- `self.embedding_provider.encode`（[nodes.py:299](../../../src/workflow/nodes.py#L299)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.upsert_entity_embeddings`（[nodes.py:300](../../../src/workflow/nodes.py#L300)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityEmbedding`（[nodes.py:302](../../../src/workflow/nodes.py#L302)）：来自 `src.domain.EntityEmbedding`；具体实现可能由依赖注入或运行时分派决定。
- `canonical_hash`（调用点 [nodes.py:305](../../../src/workflow/nodes.py#L305)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `len`（[nodes.py:306](../../../src/workflow/nodes.py#L306)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `zip`（[nodes.py:309](../../../src/workflow/nodes.py#L309)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.status`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`EvidenceIntegrityError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
