源码：[service.py:1](../../../src/workflow/service.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：50

**模块职责**：Application service shared by CLI and future API/UI adapters.
**在系统中的位置**：应用服务、LangGraph 编排、执行状态、审核接续、图提交及纠正流程。
**阅读重点**：PrismKEService 是 CLI/API/页面共同的应用入口。它配置 Provider 与存储，创建/执行/恢复运行，协调审核、案例、实体治理和提交；旧检查点兼容性由显式策略检查。
**直接依赖**：[src.agents](../agents/__init__.md)、[src.core.errors](../core/errors.md)、[src.core.ids](../core/ids.md)、[src.core.settings](../core/settings.md)、[src.domain](../domain/__init__.md)、[src.governance](../governance/__init__.md)、[src.governance.entity_resolution](../governance/entity_resolution.md)、[src.governance.validation](../governance/validation/__init__.md)、[src.parsing](../parsing/__init__.md)、[src.persistence](../persistence/__init__.md)、[src.persistence.base](../persistence/base.md)、[src.providers](../providers/__init__.md)、[src.providers.base](../providers/base.md)、[src.providers.semantic](../providers/semantic.md)、[src.workflow.cases](cases.md)、[src.workflow.graph](graph.md)、[src.workflow.reflection](reflection.md)、[src.workflow.review_workspace](review_workspace.md)；外部/标准库：`__future__`、`pathlib`、`typing`、`urllib`。
**主要调用方（静态导入）**：[evaluation/document_validation.py](../evaluation/document_validation.md)、[workflow/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

## 核心路径解读

- 服务构造函数连接配置、运行目录、证据库、审核库、执行管理与图后端；`provider`/`ocr_provider`/`vlm_provider`/`embedding_provider` 等工厂按运行配置选择实现。
- `create_run` 先构造可复现运行身份和初始状态，`execute_run`/`resume` 再经执行管理与 LangGraph 推进；创建运行、运行状态和写图完成是不同阶段。
- 审核相关入口保持任务版本、审核人、证据与流程策略检查；实体审核先于事实规范化。`confirm_review_commit` 只在隔离工作区提交预览已被确认时推进。
- GraphStore 与 EvidenceStore 的实际副作用在下游发生；CLI、API 和页面不应分别实现另一套业务校验。

---

# PrismKEService ⭐⭐⭐⭐

**位置与等级**：[service.py:88](../../../src/workflow/service.py#L88)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：跨步骤服务；组合依赖并暴露可复用业务入口。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`PrismKEService.__init__`、`PrismKEService.settings_view`、`PrismKEService.update_settings`、`PrismKEService._create_graph_store`、`PrismKEService.close`、`PrismKEService.workspace_summary`、`PrismKEService.validate_run`、`PrismKEService.exclude_validation_issue`、`PrismKEService._validate_endpoint`、`PrismKEService.provider`、`PrismKEService.ocr_provider`、`PrismKEService.vlm_provider`、`PrismKEService.embedding_provider`、`PrismKEService.reflection_provider`、`PrismKEService.semantic_advisor`、`PrismKEService.case_retriever`、`PrismKEService.list_cases`、`PrismKEService.get_case`、`PrismKEService.disable_case`、`PrismKEService.rebuild_case_index`、`PrismKEService.replay_case_projections`、`PrismKEService.entity_governance`、`PrismKEService.search_entities`、`PrismKEService.list_entity_reviews`、`PrismKEService.propose_entity_merge`、`PrismKEService.propose_entity_split`、`PrismKEService.review_entity_operation`、`PrismKEService.entity_history`、`PrismKEService._workflow`、`PrismKEService.run`、`PrismKEService.create_run`、`PrismKEService.execute_run`、`PrismKEService._execute_run`、`PrismKEService.show_run`、`PrismKEService.entity_review_detail`、`PrismKEService.claim_review_detail`、`PrismKEService.review_progress`、`PrismKEService.review_workflow`、`PrismKEService.review_tail_workflow`、`PrismKEService._validated_run_providers`、`PrismKEService._validate_agent_policy`、`PrismKEService._validate_reflection_policy`、`PrismKEService._validate_entity_policy`、`PrismKEService.review`、`PrismKEService.review_entity`、`PrismKEService.resume`、`PrismKEService._resume`、`PrismKEService.confirm_review_commit`、`PrismKEService._confirm_review_commit`


---

# PrismKEService.__init__ ⭐⭐

**位置与等级**：[service.py:89](../../../src/workflow/service.py#L89)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, settings: Settings | None=None, graph_store: GraphStore | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`settings`（Settings | None；默认 `None`；服务配置；敏感值不应进入输出或文档）；`graph_store`（GraphStore | None；默认 `None`；图持久化接口，具体实现由配置注入）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.settings`，值来自 `settings or Settings()`。
2. 更新 `self.runtime_config`，值来自 `RuntimeConfigRepository(self.settings.runtime_dir / 'config' / 'overrides.json')`。
3. 调用 `self.runtime_config.apply`，结果未直接赋值。
4. 更新 `self.review_metadata`，值来自 `workspace_metadata(self.settings.runtime_dir)`。
5. 检查 `self.review_metadata and self.settings.graph_store != 'json' and (graph_store is None)`；按条件分流，else 分支不存在。
6. 更新 `self.runs`，值来自 `RunRepository(self.settings.runs_dir)`。
7. 更新 `self.evidence_store`，值来自 `FileEvidenceStore(self.settings.evidence_dir)`。
8. 更新 `self.graph_store`，值来自 `graph_store or self._create_graph_store()`。
9. 检查 `isinstance(self.graph_store, (JSONGraphStore, Neo4jGraphStore))`；按条件分流，else 分支不存在。
10. 更新 `self.audit`，值来自 `AuditLog(self.settings.audit_path)`。
11. 更新 `self.entity_governance_repository`，值来自 `EntityGovernanceRepository(self.settings.entity_governance_path)`。
12. 更新 `self.case_repository`，值来自 `CaseRepository(self.settings.cases_path)`。
13. 更新 `self.cases`，值来自 `CaseService(self.case_repository, self.evidence_store)`。
14. 更新 `self._ocr_providers`，值来自 `{}`。
15. 更新 `self._embedding_provider`，值来自 `None`。
16. 更新 `self.reviews`，值来自 `ReviewService(self)`。
17. 更新 `self.corrections`，值来自 `CorrectionService(self)`。
18. 更新 `self.executions`，值来自 `ExecutionManager(self)`。

**关键条件与保护**：
- [service.py:98](../../../src/workflow/service.py#L98)：`self.review_metadata and self.settings.graph_store != 'json' and (graph_store is None)`，不满足时跳过本分支。
- [service.py:103](../../../src/workflow/service.py#L103)：`isinstance(self.graph_store, (JSONGraphStore, Neo4jGraphStore))`，不满足时跳过本分支。
- [service.py:104](../../../src/workflow/service.py#L104)：`isinstance(graph_store, (JSONGraphStore, Neo4jGraphStore)) and isinstance(graph_store.evidence_store, FileEvidence…`，不满足时跳过本分支。

**调用与被调用**：
- `Settings`（调用点 [service.py:92](../../../src/workflow/service.py#L92)）→ [Settings](../core/settings.md)，静态可定位。
- `RuntimeConfigRepository`（[service.py:93](../../../src/workflow/service.py#L93)）：来自 `src.persistence.RuntimeConfigRepository`；具体实现可能由依赖注入或运行时分派决定。
- `self.runtime_config.apply`（[service.py:96](../../../src/workflow/service.py#L96)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `workspace_metadata`（调用点 [service.py:97](../../../src/workflow/service.py#L97)）→ [workspace_metadata](review_workspace.md)，静态可定位。
- `ValueError`（[service.py:99](../../../src/workflow/service.py#L99)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `RunRepository`（[service.py:100](../../../src/workflow/service.py#L100)）：来自 `src.persistence.RunRepository`；具体实现可能由依赖注入或运行时分派决定。
- `FileEvidenceStore`（[service.py:101](../../../src/workflow/service.py#L101)）：来自 `src.persistence.FileEvidenceStore`；具体实现可能由依赖注入或运行时分派决定。
- `self._create_graph_store`（调用点 [service.py:102](../../../src/workflow/service.py#L102)）→ [PrismKEService._create_graph_store](service.md)，静态可定位。
- `isinstance`（[service.py:103](../../../src/workflow/service.py#L103)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `AuditLog`（[service.py:109](../../../src/workflow/service.py#L109)）：来自 `src.persistence.AuditLog`；具体实现可能由依赖注入或运行时分派决定。
- `EntityGovernanceRepository`（[service.py:110](../../../src/workflow/service.py#L110)）：来自 `src.persistence.EntityGovernanceRepository`；具体实现可能由依赖注入或运行时分派决定。
- `CaseRepository`（[service.py:113](../../../src/workflow/service.py#L113)）：来自 `src.persistence.CaseRepository`；具体实现可能由依赖注入或运行时分派决定。
- `CaseService`（调用点 [service.py:114](../../../src/workflow/service.py#L114)）→ [CaseService](cases.md)，静态可定位。
- `ReviewService`（调用点 [service.py:119](../../../src/workflow/service.py#L119)）→ [ReviewService](reviews.md)，静态可定位。
- `CorrectionService`（调用点 [service.py:122](../../../src/workflow/service.py#L122)）→ [CorrectionService](corrections.md)，静态可定位。
- `ExecutionManager`（调用点 [service.py:125](../../../src/workflow/service.py#L125)）→ [ExecutionManager](execution.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.settings`、`self.runtime_config`、`self.review_metadata`、`self.runs`、`self.evidence_store`、`self.graph_store`、`self.graph_store.evidence_store`、`self.audit`、`self.entity_governance_repository`、`self.case_repository`、`self.cases`、`self._ocr_providers`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.settings_view ⭐⭐

**位置与等级**：[service.py:127](../../../src/workflow/service.py#L127)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def settings_view(self) -> dict[str, Any]`。

**作用**：处理 `settings_view` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.runtime_config.public_view(self.settings)`。

**调用与被调用**：
- `self.runtime_config.public_view`（[service.py:128](../../../src/workflow/service.py#L128)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[PrismKEService.update_settings](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.update_settings ⭐⭐

**位置与等级**：[service.py:130](../../../src/workflow/service.py#L130)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def update_settings(self, values: dict[str, Any], clear_secrets: list[str], operator: str) -> dict[str, Any]`。

**作用**：创建、更新或记录相应资源；写入/审计边界以实际调用和状态赋值为准。

**输入与输出**：
- 输入：`values`（dict[str, Any]）；`clear_secrets`（list[str]）；`operator`（str）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not operator.strip()`；按条件分流，else 分支不存在。
2. 更新 `invalid_clear`，值来自 `set(clear_secrets) - SECRET_FIELDS`。
3. 检查 `invalid_clear`；按条件分流，else 分支不存在。
4. 更新 `clean`，值来自 `{key: value for key, value in values.items() if value is not None}`。
5. 遍历 `SECRET_FIELDS`，逐项处理 `field`。
6. 遍历 `clear_secrets`，逐项处理 `field`。
7. 遍历 `{'llm_base_url', 'vlm_base_url'} & clean.keys()`，逐项处理 `field`。
8. 检查 `'neo4j_uri' in clean`；按条件分流，else 分支不存在。
9. 检查 `clean.get('graph_store', self.settings.graph_store) not in {'json', 'neo4j'}`；按条件分流，else 分支不存在。
10. 检查 `clean.get('embedding_provider', self.settings.embedding_provider) not in {'disabled', 'mock', 'bge-m3'}`；按条件分流，else 分支不存在。
11. 更新 `candidate`，值来自 `Settings.model_validate({**self.settings.model_dump(), **clean})`。
12. 更新 `clean`，值来自 `{key: getattr(candidate, key) for key in clean}`。
13. 调用 `self.runtime_config.update`，结果未直接赋值。
14. 遍历 `clean.items()`，逐项处理 `(key, value)`。
15. 检查 `{'ocr_device', 'ocr_lang', 'ocr_model'} & clean.keys()`；按条件分流，else 分支不存在。
16. 检查 `any((key.startswith('embedding_') for key in clean))`；按条件分流，else 分支不存在。
17. 更新 `changed`，值来自 `sorted(clean)`。
18. 调用 `self.audit.record`，结果未直接赋值。
19. 返回 `{'settings': self.settings_view(), 'changed_fields': changed, 'restart_required': bool(RESTART_FIELDS & …`。

**关键条件与保护**：
- [service.py:138](../../../src/workflow/service.py#L138)：`not operator.strip()`，不满足时跳过本分支。
- [service.py:141](../../../src/workflow/service.py#L141)：`invalid_clear`，不满足时跳过本分支。
- [service.py:145](../../../src/workflow/service.py#L145)：`field in clean and (not str(clean[field]).strip())`，不满足时跳过本分支。
- [service.py:151](../../../src/workflow/service.py#L151)：`parsed.username or parsed.password or parsed.query or parsed.fragment`，不满足时跳过本分支。
- [service.py:154](../../../src/workflow/service.py#L154)：`'neo4j_uri' in clean`，不满足时跳过本分支。
- [service.py:156](../../../src/workflow/service.py#L156)：`parsed.username or parsed.password or parsed.query or parsed.fragment`，不满足时跳过本分支。
- [service.py:158](../../../src/workflow/service.py#L158)：`parsed.scheme not in {'bolt', 'neo4j', <字符串常量>, <字符串常量>} or not parsed.netloc`，不满足时跳过本分支。
- [service.py:160](../../../src/workflow/service.py#L160)：`clean.get('graph_store', self.settings.graph_store) not in {'json', 'neo4j'}`，不满足时跳过本分支。
- [service.py:162](../../../src/workflow/service.py#L162)：`clean.get('embedding_provider', self.settings.embedding_provider) not in {'disabled', 'mock', 'bge-m3'}`，不满足时跳过本分支。
- [service.py:173](../../../src/workflow/service.py#L173)：`{'ocr_device', 'ocr_lang', 'ocr_model'} & clean.keys()`，不满足时跳过本分支。
- [service.py:175](../../../src/workflow/service.py#L175)：`any((key.startswith('embedding_') for key in clean))`，不满足时跳过本分支。

**调用与被调用**：
- `operator.strip`（[service.py:138](../../../src/workflow/service.py#L138)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[service.py:139](../../../src/workflow/service.py#L139)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[service.py:140](../../../src/workflow/service.py#L140)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `values.items`（[service.py:143](../../../src/workflow/service.py#L143)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str(clean[field]).strip`（[service.py:145](../../../src/workflow/service.py#L145)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[service.py:145](../../../src/workflow/service.py#L145)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `clean.pop`（[service.py:146](../../../src/workflow/service.py#L146)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `clean.keys`（[service.py:149](../../../src/workflow/service.py#L149)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `urlparse`（[service.py:150](../../../src/workflow/service.py#L150)）：来自 `urllib.parse.urlparse`；具体实现可能由依赖注入或运行时分派决定。
- `self._validate_endpoint`（调用点 [service.py:153](../../../src/workflow/service.py#L153)）→ [PrismKEService._validate_endpoint](service.md)，静态可定位。
- `clean.get`（[service.py:160](../../../src/workflow/service.py#L160)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Settings.model_validate`（[service.py:168](../../../src/workflow/service.py#L168)）：来自 `src.core.settings.Settings`；具体实现可能由依赖注入或运行时分派决定。
- `self.settings.model_dump`（[service.py:168](../../../src/workflow/service.py#L168)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `getattr`（[service.py:169](../../../src/workflow/service.py#L169)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.runtime_config.update`（[service.py:170](../../../src/workflow/service.py#L170)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `clean.items`（[service.py:171](../../../src/workflow/service.py#L171)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `setattr`（[service.py:172](../../../src/workflow/service.py#L172)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._ocr_providers.clear`（[service.py:174](../../../src/workflow/service.py#L174)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[service.py:175](../../../src/workflow/service.py#L175)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `key.startswith`（[service.py:175](../../../src/workflow/service.py#L175)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[service.py:177](../../../src/workflow/service.py#L177)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.audit.record`（[service.py:178](../../../src/workflow/service.py#L178)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.settings_view`（调用点 [service.py:188](../../../src/workflow/service.py#L188)）→ [PrismKEService.settings_view](service.md)，静态可定位。
- `bool`（[service.py:190](../../../src/workflow/service.py#L190)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`clean[field]`、`self._embedding_provider`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`、`ValueError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService._create_graph_store ⭐⭐

**位置与等级**：[service.py:193](../../../src/workflow/service.py#L193)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _create_graph_store(self) -> GraphStore`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`GraphStore`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self.settings.graph_store == 'json'`；按条件分流，else 分支不存在。
2. 检查 `self.settings.graph_store != 'neo4j'`；按条件分流，else 分支不存在。
3. 检查 `not self.settings.neo4j_password`；按条件分流，else 分支不存在。
4. 返回 `Neo4jGraphStore(uri=self.settings.neo4j_uri, user=self.settings.neo4j_user, password=self.settings.neo4j…`。

**关键条件与保护**：
- [service.py:194](../../../src/workflow/service.py#L194)：`self.settings.graph_store == 'json'`，不满足时跳过本分支。
- [service.py:196](../../../src/workflow/service.py#L196)：`self.settings.graph_store != 'neo4j'`，不满足时跳过本分支。
- [service.py:198](../../../src/workflow/service.py#L198)：`not self.settings.neo4j_password`，不满足时跳过本分支。

**调用与被调用**：
- `JSONGraphStore`（[service.py:195](../../../src/workflow/service.py#L195)）：来自 `src.persistence.JSONGraphStore`；具体实现可能由依赖注入或运行时分派决定。
- `ValueError`（[service.py:197](../../../src/workflow/service.py#L197)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ProviderConfigurationError`（调用点 [service.py:199](../../../src/workflow/service.py#L199)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- `Neo4jGraphStore`（[service.py:200](../../../src/workflow/service.py#L200)）：来自 `src.persistence.Neo4jGraphStore`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[PrismKEService.__init__](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(f<字符串常量>)`、`ProviderConfigurationError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.close ⭐⭐

**位置与等级**：[service.py:207](../../../src/workflow/service.py#L207)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def close(self) -> None`。

**作用**：释放该对象管理的外部资源；重复调用是否安全取决于实现。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 等待 `self.executions.stop()` 完成。
2. 等待 `self.graph_store.close()` 完成。

**调用与被调用**：
- `self.executions.stop`（[service.py:208](../../../src/workflow/service.py#L208)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.close`（[service.py:209](../../../src/workflow/service.py#L209)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.workspace_summary ⭐⭐

**位置与等级**：[service.py:211](../../../src/workflow/service.py#L211)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def workspace_summary(self) -> dict[str, Any]`。

**作用**：处理 `workspace_summary` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `states`，值来自 `self.runs.list(limit=1000)`。
2. 更新 `run_counts`，值来自 `{}`。
3. 更新 `pending_reviews`，值来自 `0`。
4. 更新 `blocking_issues`，值来自 `0`。
5. 遍历 `states`，逐项处理 `state`。
6. 返回 `{'run_counts': run_counts, 'pending_reviews': pending_reviews, 'blocking_issues': blocking_issues, 'work…`。

**调用与被调用**：
- `self.runs.list`（[service.py:212](../../../src/workflow/service.py#L212)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.executions.view`（[service.py:217](../../../src/workflow/service.py#L217)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `run_counts.get`（[service.py:218](../../../src/workflow/service.py#L218)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sum`（[service.py:219](../../../src/workflow/service.py#L219)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.executions.health`（[service.py:226](../../../src/workflow/service.py#L226)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `(await self.graph_store.healthcheck()).model_dump`（[service.py:227](../../../src/workflow/service.py#L227)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.healthcheck`（[service.py:227](../../../src/workflow/service.py#L227)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`run_counts[execution_status]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.validate_run ⭐⭐⭐⭐

**位置与等级**：[service.py:230](../../../src/workflow/service.py#L230)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def validate_run(self, run_id: str) -> ValidationResult`。

**作用**：只读复核运行的校验结果；阻断问题不能由展示层忽略。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`ValidationResult`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state`，值来自 `self.show_run(run_id)`。
2. 检查 `state.document is None or state.output_schema is None`；按条件分流，else 分支不存在。
3. 更新 `blocked`，值来自 `ValidationService.blocked_candidate_ids(state.candidates, state.validation)`。
4. 更新 `issues`，值来自 `await ValidationService().candidates([c for c in state.candidates if c.id not in blocked], SchemaIn…`。
5. 更新 `sid`，值来自 `canonical_hash(state.output_schema.model_dump(mode='json'))`。
6. 更新 `context`，值来自 `CommitValidationContext(schemas={sid: state.output_schema}, claim_schema_ids={c.id: sid for c in st…`。
7. 遍历 `state.claims`，逐项处理 `claim`。
8. 更新 `claim_ids`，值来自 `{c.id for c in state.claims}`。
9. 遍历 `state.conflicts if state.claims or state.status == 'completed' else []`，逐项处理 `conflict`。
10. 检查 `state.status == 'failed'`；按条件分流，else 分支不存在。
11. 返回 `ValidationService.merge(state.validation, issues, canonical_hash(state.document.model_dump(mode='json'))…`。

**关键条件与保护**：
- [service.py:232](../../../src/workflow/service.py#L232)：`state.document is None or state.output_schema is None`，不满足时跳过本分支。
- [service.py:284](../../../src/workflow/service.py#L284)：`not set(conflict.claim_ids) <= claim_ids`，不满足时跳过本分支。
- [service.py:295](../../../src/workflow/service.py#L295)：`state.status == 'failed'`，不满足时跳过本分支。

**调用与被调用**：
- `self.show_run`（调用点 [service.py:231](../../../src/workflow/service.py#L231)）→ [PrismKEService.show_run](service.md)，静态可定位。
- `ValueError`（[service.py:233](../../../src/workflow/service.py#L233)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService.blocked_candidate_ids`（[service.py:236](../../../src/workflow/service.py#L236)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `ValidationService().candidates`（[service.py:237](../../../src/workflow/service.py#L237)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService`（[service.py:237](../../../src/workflow/service.py#L237)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `SchemaIndex`（[service.py:239](../../../src/workflow/service.py#L239)）：来自 `src.domain.SchemaIndex`；具体实现可能由依赖注入或运行时分派决定。
- `canonical_hash`（调用点 [service.py:245](../../../src/workflow/service.py#L245)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `state.output_schema.model_dump`（[service.py:245](../../../src/workflow/service.py#L245)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CommitValidationContext`（[service.py:247](../../../src/workflow/service.py#L247)）：来自 `src.domain.CommitValidationContext`；具体实现可能由依赖注入或运行时分派决定。
- `ValidationService().commit`（[service.py:257](../../../src/workflow/service.py#L257)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphCommit`（[service.py:258](../../../src/workflow/service.py#L258)）：来自 `src.domain.GraphCommit`；具体实现可能由依赖注入或运行时分派决定。
- `GraphRevision`（[service.py:260](../../../src/workflow/service.py#L260)）：来自 `src.domain.GraphRevision`；具体实现可能由依赖注入或运行时分派决定。
- `str(error).split(':', 1)[0].split`（[service.py:269](../../../src/workflow/service.py#L269)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str(error).split`（[service.py:269](../../../src/workflow/service.py#L269)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[service.py:269](../../../src/workflow/service.py#L269)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService.issue`（[service.py:270](../../../src/workflow/service.py#L270)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `code.strip`（[service.py:271](../../../src/workflow/service.py#L271)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `issues.append`（[service.py:280](../../../src/workflow/service.py#L280)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[service.py:284](../../../src/workflow/service.py#L284)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationService.merge`（[service.py:306](../../../src/workflow/service.py#L306)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `state.document.model_dump`（[service.py:309](../../../src/workflow/service.py#L309)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[service.py:310](../../../src/workflow/service.py#L310)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`issue.allowed_actions`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：`GraphIntegrityError`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.exclude_validation_issue ⭐⭐

**位置与等级**：[service.py:313](../../../src/workflow/service.py#L313)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def exclude_validation_issue(self, run_id: str, issue_id: str, reviewer: str, comment: str='') -> WorkflowState`。

**作用**：处理 `exclude_validation_issue` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`issue_id`（str）；`reviewer`（str；审核操作者，形成审计归属）；`comment`（str；默认 `''`）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not reviewer.strip()`；按条件分流，else 分支不存在。
2. 进入上下文 `self.runs.mutation_lock(run_id)`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [service.py:316](../../../src/workflow/service.py#L316)：`not reviewer.strip()`，不满足时跳过本分支。
- [service.py:321](../../../src/workflow/service.py#L321)：`state.pipeline_version != PIPELINE_VERSION or state.status != 'awaiting_review'`，不满足时跳过本分支。
- [service.py:324](../../../src/workflow/service.py#L324)：`issue is None or issue.status != 'open' or 'exclude' not in issue.allowed_actions`，不满足时跳过本分支。
- [service.py:344](../../../src/workflow/service.py#L344)：`state.current_node == 'resolve_entities'`，不满足时有 else 分支。
- [service.py:348](../../../src/workflow/service.py#L348)：`not updated`，不满足时跳过本分支。

**调用与被调用**：
- `reviewer.strip`（[service.py:316](../../../src/workflow/service.py#L316)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[service.py:317](../../../src/workflow/service.py#L317)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.runs.mutation_lock`（[service.py:318](../../../src/workflow/service.py#L318)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.reviews.recover`（[service.py:319](../../../src/workflow/service.py#L319)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.show_run`（调用点 [service.py:320](../../../src/workflow/service.py#L320)）→ [PrismKEService.show_run](service.md)，静态可定位。
- `next`（[service.py:323](../../../src/workflow/service.py#L323)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.validation_decisions.append`（[service.py:327](../../../src/workflow/service.py#L327)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValidationReviewDecision`（[service.py:328](../../../src/workflow/service.py#L328)）：来自 `src.domain.ValidationReviewDecision`；具体实现可能由依赖注入或运行时分派决定。
- `ValidationService.merge`（[service.py:332](../../../src/workflow/service.py#L332)）：来自 `src.governance.validation.ValidationService`；具体实现可能由依赖注入或运行时分派决定。
- `any`（[service.py:337](../../../src/workflow/service.py#L337)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.review_workflow`（调用点 [service.py:343](../../../src/workflow/service.py#L343)）→ [PrismKEService.review_workflow](service.md)，静态可定位。
- `workflow.record_entity_review`（[service.py:345](../../../src/workflow/service.py#L345)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `workflow.record_review`（[service.py:347](../../../src/workflow/service.py#L347)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `LegacyCheckpointError`（调用点 [service.py:349](../../../src/workflow/service.py#L349)）→ [LegacyCheckpointError](../core/errors.md)，静态可定位。
- `self.audit.record`（[service.py:350](../../../src/workflow/service.py#L350)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `state.validation_decisions[-1].model_dump`（[service.py:353](../../../src/workflow/service.py#L353)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`issue.status`、`state.validation`、`state.status`、`state.graph_commit`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`、`LegacyCheckpointError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService._validate_endpoint ⭐⭐

**位置与等级**：[service.py:358](../../../src/workflow/service.py#L358)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _validate_endpoint(value: str, variable: str) -> None`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`value`（str）；`variable`（str）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `parsed`，值来自 `urlparse(value.strip())`。
2. 检查 `not value.strip() or <字符串常量> in value or <字符串常量> in value or (parsed.scheme not in {'http', 'https'}) or…`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [service.py:360](../../../src/workflow/service.py#L360)：`not value.strip() or <字符串常量> in value or <字符串常量> in value or (parsed.scheme not in {'http', 'https'}) or (not pars…`，不满足时跳过本分支。

**调用与被调用**：
- `urlparse`（[service.py:359](../../../src/workflow/service.py#L359)）：来自 `urllib.parse.urlparse`；具体实现可能由依赖注入或运行时分派决定。
- `value.strip`（[service.py:359](../../../src/workflow/service.py#L359)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ProviderConfigurationError`（调用点 [service.py:367](../../../src/workflow/service.py#L367)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- 静态可定位的调用方：[PrismKEService.update_settings](service.md)、[PrismKEService.provider](service.md)、[PrismKEService.vlm_provider](service.md)、[PrismKEService.reflection_provider](service.md)、[PrismKEService.semantic_advisor](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderConfigurationError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.provider ⭐⭐

**位置与等级**：[service.py:369](../../../src/workflow/service.py#L369)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def provider(self, name: str) -> LLMProvider`。

**作用**：处理 `provider` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`name`（str）。
- 输出类型：`LLMProvider`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `name == 'mock'`；按条件分流，else 分支不存在。
2. 检查 `name != 'openai-compatible'`；按条件分流，else 分支不存在。
3. 检查 `not self.settings.llm_api_key`；按条件分流，else 分支不存在。
4. 检查 `not self.settings.llm_model`；按条件分流，else 分支不存在。
5. 调用 `self._validate_endpoint`，结果未直接赋值。
6. 返回 `OpenAICompatibleLLMProvider(base_url=self.settings.llm_base_url, api_key=self.settings.llm_api_key, mode…`。

**关键条件与保护**：
- [service.py:370](../../../src/workflow/service.py#L370)：`name == 'mock'`，不满足时跳过本分支。
- [service.py:372](../../../src/workflow/service.py#L372)：`name != 'openai-compatible'`，不满足时跳过本分支。
- [service.py:374](../../../src/workflow/service.py#L374)：`not self.settings.llm_api_key`，不满足时跳过本分支。
- [service.py:376](../../../src/workflow/service.py#L376)：`not self.settings.llm_model`，不满足时跳过本分支。

**调用与被调用**：
- `MockLLMProvider`（[service.py:371](../../../src/workflow/service.py#L371)）：来自 `src.providers.MockLLMProvider`；具体实现可能由依赖注入或运行时分派决定。
- `ProviderConfigurationError`（调用点 [service.py:373](../../../src/workflow/service.py#L373)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- `self._validate_endpoint`（调用点 [service.py:378](../../../src/workflow/service.py#L378)）→ [PrismKEService._validate_endpoint](service.md)，静态可定位。
- `OpenAICompatibleLLMProvider`（[service.py:379](../../../src/workflow/service.py#L379)）：来自 `src.providers.OpenAICompatibleLLMProvider`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[PrismKEService.create_run](service.md)、[PrismKEService._execute_run](service.md)、[PrismKEService._validated_run_providers](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderConfigurationError(f<字符串常量>)`、`ProviderConfigurationError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.ocr_provider ⭐⭐

**位置与等级**：[service.py:386](../../../src/workflow/service.py#L386)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def ocr_provider(self, name: str) -> OCRProvider`。

**作用**：处理 `ocr_provider` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`name`（str）。
- 输出类型：`OCRProvider`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `cached`，值来自 `self._ocr_providers.get(name)`。
2. 检查 `cached is not None`；按条件分流，else 分支不存在。
3. 检查 `name == 'disabled'`；按条件分流，else 分支存在。
4. 更新 `self._ocr_providers[name]`，值来自 `provider`。
5. 返回 `provider`。

**关键条件与保护**：
- [service.py:388](../../../src/workflow/service.py#L388)：`cached is not None`，不满足时跳过本分支。
- [service.py:390](../../../src/workflow/service.py#L390)：`name == 'disabled'`，不满足时有 else 分支。
- [service.py:392](../../../src/workflow/service.py#L392)：`name == 'mock'`，不满足时有 else 分支。
- [service.py:394](../../../src/workflow/service.py#L394)：`name == 'paddle'`，不满足时有 else 分支。

**调用与被调用**：
- `self._ocr_providers.get`（[service.py:387](../../../src/workflow/service.py#L387)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `DisabledOCRProvider`（[service.py:391](../../../src/workflow/service.py#L391)）：来自 `src.providers.DisabledOCRProvider`；具体实现可能由依赖注入或运行时分派决定。
- `MockOCRProvider`（[service.py:393](../../../src/workflow/service.py#L393)）：来自 `src.providers.MockOCRProvider`；具体实现可能由依赖注入或运行时分派决定。
- `PaddleOCRProvider`（[service.py:395](../../../src/workflow/service.py#L395)）：来自 `src.providers.PaddleOCRProvider`；具体实现可能由依赖注入或运行时分派决定。
- `ProviderConfigurationError`（调用点 [service.py:401](../../../src/workflow/service.py#L401)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- 静态可定位的调用方：[PrismKEService.create_run](service.md)、[PrismKEService._execute_run](service.md)、[PrismKEService._validated_run_providers](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self._ocr_providers[name]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderConfigurationError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.vlm_provider ⭐⭐

**位置与等级**：[service.py:405](../../../src/workflow/service.py#L405)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def vlm_provider(self, name: str) -> VLMProvider`。

**作用**：处理 `vlm_provider` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`name`（str）。
- 输出类型：`VLMProvider`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `name == 'disabled'`；按条件分流，else 分支不存在。
2. 检查 `name == 'mock'`；按条件分流，else 分支不存在。
3. 检查 `name != 'openai-compatible'`；按条件分流，else 分支不存在。
4. 检查 `not self.settings.vlm_api_key`；按条件分流，else 分支不存在。
5. 检查 `not self.settings.vlm_model`；按条件分流，else 分支不存在。
6. 调用 `self._validate_endpoint`，结果未直接赋值。
7. 返回 `OpenAICompatibleVLMProvider(base_url=self.settings.vlm_base_url, api_key=self.settings.vlm_api_key, mode…`。

**关键条件与保护**：
- [service.py:406](../../../src/workflow/service.py#L406)：`name == 'disabled'`，不满足时跳过本分支。
- [service.py:408](../../../src/workflow/service.py#L408)：`name == 'mock'`，不满足时跳过本分支。
- [service.py:410](../../../src/workflow/service.py#L410)：`name != 'openai-compatible'`，不满足时跳过本分支。
- [service.py:412](../../../src/workflow/service.py#L412)：`not self.settings.vlm_api_key`，不满足时跳过本分支。
- [service.py:414](../../../src/workflow/service.py#L414)：`not self.settings.vlm_model`，不满足时跳过本分支。

**调用与被调用**：
- `DisabledVLMProvider`（[service.py:407](../../../src/workflow/service.py#L407)）：来自 `src.providers.DisabledVLMProvider`；具体实现可能由依赖注入或运行时分派决定。
- `MockVLMProvider`（[service.py:409](../../../src/workflow/service.py#L409)）：来自 `src.providers.MockVLMProvider`；具体实现可能由依赖注入或运行时分派决定。
- `ProviderConfigurationError`（调用点 [service.py:411](../../../src/workflow/service.py#L411)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- `self._validate_endpoint`（调用点 [service.py:416](../../../src/workflow/service.py#L416)）→ [PrismKEService._validate_endpoint](service.md)，静态可定位。
- `OpenAICompatibleVLMProvider`（[service.py:417](../../../src/workflow/service.py#L417)）：来自 `src.providers.OpenAICompatibleVLMProvider`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[PrismKEService.create_run](service.md)、[PrismKEService._execute_run](service.md)、[PrismKEService._validated_run_providers](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderConfigurationError(f<字符串常量>)`、`ProviderConfigurationError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.embedding_provider ⭐⭐

**位置与等级**：[service.py:425](../../../src/workflow/service.py#L425)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def embedding_provider(self) -> EmbeddingProvider`。

**作用**：处理 `embedding_provider` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`EmbeddingProvider`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self._embedding_provider is not None`；按条件分流，else 分支不存在。
2. 更新 `name`，值来自 `self.settings.embedding_provider`。
3. 检查 `name == 'disabled'`；按条件分流，else 分支存在。
4. 更新 `self._embedding_provider`，值来自 `provider`。
5. 返回 `provider`。

**关键条件与保护**：
- [service.py:426](../../../src/workflow/service.py#L426)：`self._embedding_provider is not None`，不满足时跳过本分支。
- [service.py:429](../../../src/workflow/service.py#L429)：`name == 'disabled'`，不满足时有 else 分支。
- [service.py:431](../../../src/workflow/service.py#L431)：`name == 'mock'`，不满足时有 else 分支。
- [service.py:433](../../../src/workflow/service.py#L433)：`name == 'bge-m3'`，不满足时有 else 分支。

**调用与被调用**：
- `DisabledEmbeddingProvider`（[service.py:430](../../../src/workflow/service.py#L430)）：来自 `src.providers.DisabledEmbeddingProvider`；具体实现可能由依赖注入或运行时分派决定。
- `MockEmbeddingProvider`（[service.py:432](../../../src/workflow/service.py#L432)）：来自 `src.providers.MockEmbeddingProvider`；具体实现可能由依赖注入或运行时分派决定。
- `BGEM3EmbeddingProvider`（[service.py:434](../../../src/workflow/service.py#L434)）：来自 `src.providers.BGEM3EmbeddingProvider`；具体实现可能由依赖注入或运行时分派决定。
- `ProviderConfigurationError`（调用点 [service.py:446](../../../src/workflow/service.py#L446)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- 静态可定位的调用方：[PrismKEService.case_retriever](service.md)、[PrismKEService.entity_governance](service.md)、[PrismKEService.search_entities](service.md)、[PrismKEService._workflow](service.md)、[PrismKEService.create_run](service.md)、[PrismKEService.review_tail_workflow](service.md)、[PrismKEService._validated_run_providers](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self._embedding_provider`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderConfigurationError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.reflection_provider ⭐⭐⭐⭐

**位置与等级**：[service.py:450](../../../src/workflow/service.py#L450)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def reflection_provider(self, name: str) -> ReflectionProvider`。

**作用**：处理 `reflection_provider` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`name`（str）。
- 输出类型：`ReflectionProvider`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `name == 'disabled'`；按条件分流，else 分支不存在。
2. 检查 `name == 'mock'`；按条件分流，else 分支不存在。
3. 检查 `name != 'openai-compatible'`；按条件分流，else 分支不存在。
4. 检查 `not self.settings.llm_api_key`；按条件分流，else 分支不存在。
5. 检查 `not self.settings.llm_model`；按条件分流，else 分支不存在。
6. 调用 `self._validate_endpoint`，结果未直接赋值。
7. 返回 `OpenAICompatibleReflectionProvider(base_url=self.settings.llm_base_url, api_key=self.settings.llm_api_ke…`。

**关键条件与保护**：
- [service.py:451](../../../src/workflow/service.py#L451)：`name == 'disabled'`，不满足时跳过本分支。
- [service.py:453](../../../src/workflow/service.py#L453)：`name == 'mock'`，不满足时跳过本分支。
- [service.py:455](../../../src/workflow/service.py#L455)：`name != 'openai-compatible'`，不满足时跳过本分支。
- [service.py:457](../../../src/workflow/service.py#L457)：`not self.settings.llm_api_key`，不满足时跳过本分支。
- [service.py:461](../../../src/workflow/service.py#L461)：`not self.settings.llm_model`，不满足时跳过本分支。

**调用与被调用**：
- `DisabledReflectionProvider`（[service.py:452](../../../src/workflow/service.py#L452)）：来自 `src.providers.DisabledReflectionProvider`；具体实现可能由依赖注入或运行时分派决定。
- `MockReflectionProvider`（[service.py:454](../../../src/workflow/service.py#L454)）：来自 `src.providers.MockReflectionProvider`；具体实现可能由依赖注入或运行时分派决定。
- `ProviderConfigurationError`（调用点 [service.py:456](../../../src/workflow/service.py#L456)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- `self._validate_endpoint`（调用点 [service.py:465](../../../src/workflow/service.py#L465)）→ [PrismKEService._validate_endpoint](service.md)，静态可定位。
- `OpenAICompatibleReflectionProvider`（[service.py:466](../../../src/workflow/service.py#L466)）：来自 `src.providers.OpenAICompatibleReflectionProvider`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[PrismKEService._workflow](service.md)、[PrismKEService.create_run](service.md)、[PrismKEService._validate_reflection_policy](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderConfigurationError(f<字符串常量>)`、`ProviderConfigurationError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.semantic_advisor ⭐⭐

**位置与等级**：[service.py:473](../../../src/workflow/service.py#L473)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def semantic_advisor(self, name: str) -> SemanticAdvisor`。

**作用**：处理 `semantic_advisor` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`name`（str）。
- 输出类型：`SemanticAdvisor`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `name == 'disabled'`；按条件分流，else 分支不存在。
2. 检查 `name == 'mock'`；按条件分流，else 分支不存在。
3. 检查 `name != 'openai-compatible'`；按条件分流，else 分支不存在。
4. 检查 `not self.settings.llm_api_key`；按条件分流，else 分支不存在。
5. 检查 `not self.settings.llm_model`；按条件分流，else 分支不存在。
6. 调用 `self._validate_endpoint`，结果未直接赋值。
7. 返回 `OpenAICompatibleSemanticAdvisor(base_url=self.settings.llm_base_url, api_key=self.settings.llm_api_key, …`。

**关键条件与保护**：
- [service.py:474](../../../src/workflow/service.py#L474)：`name == 'disabled'`，不满足时跳过本分支。
- [service.py:476](../../../src/workflow/service.py#L476)：`name == 'mock'`，不满足时跳过本分支。
- [service.py:478](../../../src/workflow/service.py#L478)：`name != 'openai-compatible'`，不满足时跳过本分支。
- [service.py:480](../../../src/workflow/service.py#L480)：`not self.settings.llm_api_key`，不满足时跳过本分支。
- [service.py:482](../../../src/workflow/service.py#L482)：`not self.settings.llm_model`，不满足时跳过本分支。

**调用与被调用**：
- `DisabledSemanticAdvisor`（调用点 [service.py:475](../../../src/workflow/service.py#L475)）→ [DisabledSemanticAdvisor](../providers/semantic.md)，静态可定位。
- `MockSemanticAdvisor`（调用点 [service.py:477](../../../src/workflow/service.py#L477)）→ [MockSemanticAdvisor](../providers/semantic.md)，静态可定位。
- `ProviderConfigurationError`（调用点 [service.py:479](../../../src/workflow/service.py#L479)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- `self._validate_endpoint`（调用点 [service.py:484](../../../src/workflow/service.py#L484)）→ [PrismKEService._validate_endpoint](service.md)，静态可定位。
- `OpenAICompatibleSemanticAdvisor`（调用点 [service.py:485](../../../src/workflow/service.py#L485)）→ [OpenAICompatibleSemanticAdvisor](../providers/semantic.md)，静态可定位。
- 静态可定位的调用方：[PrismKEService._workflow](service.md)、[PrismKEService.create_run](service.md)、[PrismKEService._validate_agent_policy](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderConfigurationError(f<字符串常量>)`、`ProviderConfigurationError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.case_retriever ⭐⭐

**位置与等级**：[service.py:492](../../../src/workflow/service.py#L492)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def case_retriever(self) -> CaseRetriever`。

**作用**：处理 `case_retriever` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`CaseRetriever`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `provider`，值来自 `self.embedding_provider()`。
2. 检查 `provider.fingerprint() == 'embedding:disabled'`；按条件分流，else 分支不存在。
3. 返回 `CaseRetriever(self.case_repository, provider)`。

**关键条件与保护**：
- [service.py:494](../../../src/workflow/service.py#L494)：`provider.fingerprint() == 'embedding:disabled'`，不满足时跳过本分支。

**调用与被调用**：
- `self.embedding_provider`（调用点 [service.py:493](../../../src/workflow/service.py#L493)）→ [PrismKEService.embedding_provider](service.md)，静态可定位。
- `provider.fingerprint`（[service.py:494](../../../src/workflow/service.py#L494)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ProviderConfigurationError`（调用点 [service.py:495](../../../src/workflow/service.py#L495)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- `CaseRetriever`（调用点 [service.py:496](../../../src/workflow/service.py#L496)）→ [CaseRetriever](cases.md)，静态可定位。
- 静态可定位的调用方：[PrismKEService.rebuild_case_index](service.md)、[PrismKEService._workflow](service.md)、[PrismKEService.create_run](service.md)、[PrismKEService._validate_reflection_policy](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderConfigurationError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.list_cases ⭐⭐

**位置与等级**：[service.py:498](../../../src/workflow/service.py#L498)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def list_cases(self, *, case_type: str | None=None, task_type: str | None=None, language: str | None=None, active_only: bool=True, limit: int=200) -> list[dict[str, Any]]`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`case_type`（str | None；默认 `None`）；`task_type`（str | None；默认 `None`）；`language`（str | None；默认 `None`）；`active_only`（bool；默认 `True`）；`limit`（int；默认 `200`；查询或展示的最大条数）。
- 输出类型：`list[dict[str, Any]]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `records`，值来自 `self.case_repository.list(case_type=case_type, task_type=task_type, language=language, active_only=…`。
2. 返回 `[{**record.model_dump(mode='json'), 'active': self.case_repository.is_active(record.id)} for record in r…`。

**调用与被调用**：
- `self.case_repository.list`（[service.py:507](../../../src/workflow/service.py#L507)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `record.model_dump`（[service.py:516](../../../src/workflow/service.py#L516)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.case_repository.is_active`（[service.py:517](../../../src/workflow/service.py#L517)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.get_case ⭐⭐

**位置与等级**：[service.py:522](../../../src/workflow/service.py#L522)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def get_case(self, case_id: str) -> dict[str, Any]`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`case_id`（str）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `record`，值来自 `self.case_repository.get(case_id)`。
2. 返回 `{**record.model_dump(mode='json'), 'active': self.case_repository.is_active(case_id), 'status_events': […`。

**调用与被调用**：
- `self.case_repository.get`（[service.py:523](../../../src/workflow/service.py#L523)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `record.model_dump`（[service.py:525](../../../src/workflow/service.py#L525)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.case_repository.is_active`（[service.py:526](../../../src/workflow/service.py#L526)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item.model_dump`（[service.py:528](../../../src/workflow/service.py#L528)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.case_repository.status_events`（[service.py:528](../../../src/workflow/service.py#L528)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[PrismKEService.disable_case](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.disable_case ⭐⭐

**位置与等级**：[service.py:532](../../../src/workflow/service.py#L532)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def disable_case(self, case_id: str, *, operator: str, reason: str, request_id: str) -> dict[str, Any]`。

**作用**：处理 `disable_case` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`case_id`（str）；`operator`（str）；`reason`（str；人工操作或审核的理由）；`request_id`（str；幂等请求标识，避免重复动作）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not operator.strip() or not reason.strip() or (not request_id.strip())`；按条件分流，else 分支不存在。
2. 调用 `self.case_repository.get`，结果未直接赋值。
3. 更新 `event`，值来自 `CaseStatusEvent(id=stable_id('case-status', case_id, request_id), case_id=case_id, action='disable'…`。
4. 调用 `self.case_repository.disable`，结果未直接赋值。
5. 调用 `self.audit.record`，结果未直接赋值。
6. 返回 `self.get_case(case_id)`。

**关键条件与保护**：
- [service.py:537](../../../src/workflow/service.py#L537)：`not operator.strip() or not reason.strip() or (not request_id.strip())`，不满足时跳过本分支。

**调用与被调用**：
- `operator.strip`（[service.py:537](../../../src/workflow/service.py#L537)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `reason.strip`（[service.py:537](../../../src/workflow/service.py#L537)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `request_id.strip`（[service.py:537](../../../src/workflow/service.py#L537)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[service.py:538](../../../src/workflow/service.py#L538)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.case_repository.get`（[service.py:539](../../../src/workflow/service.py#L539)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CaseStatusEvent`（[service.py:540](../../../src/workflow/service.py#L540)）：来自 `src.domain.CaseStatusEvent`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [service.py:541](../../../src/workflow/service.py#L541)）→ [stable_id](../core/ids.md)，静态可定位。
- `self.case_repository.disable`（[service.py:547](../../../src/workflow/service.py#L547)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.audit.record`（[service.py:548](../../../src/workflow/service.py#L548)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `event.model_dump`（[service.py:548](../../../src/workflow/service.py#L548)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.get_case`（调用点 [service.py:549](../../../src/workflow/service.py#L549)）→ [PrismKEService.get_case](service.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.rebuild_case_index ⭐⭐

**位置与等级**：[service.py:551](../../../src/workflow/service.py#L551)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def rebuild_case_index(self, *, dry_run: bool=False) -> dict[str, Any]`。

**作用**：处理 `rebuild_case_index` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`dry_run`（bool；默认 `False`）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self.case_retriever().rebuild(dry_run=dry_run)`。

**调用与被调用**：
- `self.case_retriever().rebuild`（[service.py:552](../../../src/workflow/service.py#L552)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.case_retriever`（调用点 [service.py:552](../../../src/workflow/service.py#L552)）→ [PrismKEService.case_retriever](service.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.replay_case_projections ⭐⭐

**位置与等级**：[service.py:554](../../../src/workflow/service.py#L554)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def replay_case_projections(self) -> int`。

**作用**：处理 `replay_case_projections` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`int`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `count`，值来自 `0`。
2. 遍历 `self.runs.list(limit=10000)`，逐项处理 `run`。
3. 返回 `count`。

**关键条件与保护**：
- [service.py:557](../../../src/workflow/service.py#L557)：`run.pipeline_version != PIPELINE_VERSION`，不满足时跳过本分支。
- [service.py:560](../../../src/workflow/service.py#L560)：`self.case_repository.projected(event.id)`，不满足时跳过本分支。

**调用与被调用**：
- `self.runs.list`（[service.py:556](../../../src/workflow/service.py#L556)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.reviews.repository.events`（[service.py:559](../../../src/workflow/service.py#L559)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.case_repository.projected`（[service.py:560](../../../src/workflow/service.py#L560)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.reviews.repository.event_state`（[service.py:562](../../../src/workflow/service.py#L562)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `WorkflowState.model_validate`（[service.py:563](../../../src/workflow/service.py#L563)）：来自 `src.domain.WorkflowState`；具体实现可能由依赖注入或运行时分派决定。
- `self.cases.project_review_event`（[service.py:564](../../../src/workflow/service.py#L564)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.entity_governance ⭐⭐

**位置与等级**：[service.py:568](../../../src/workflow/service.py#L568)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def entity_governance(self) -> EntityGovernanceService`。

**作用**：处理 `entity_governance` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`EntityGovernanceService`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `EntityGovernanceService(self.graph_store, self.entity_governance_repository, self.embedding_provider())`。

**调用与被调用**：
- `EntityGovernanceService`（[service.py:569](../../../src/workflow/service.py#L569)）：来自 `src.governance.EntityGovernanceService`；具体实现可能由依赖注入或运行时分派决定。
- `self.embedding_provider`（调用点 [service.py:572](../../../src/workflow/service.py#L572)）→ [PrismKEService.embedding_provider](service.md)，静态可定位。
- 静态可定位的调用方：[PrismKEService.propose_entity_merge](service.md)、[PrismKEService.propose_entity_split](service.md)、[PrismKEService.review_entity_operation](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.search_entities ⭐⭐

**位置与等级**：[service.py:575](../../../src/workflow/service.py#L575)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def search_entities(self, query: str, entity_type: str, limit: int=10) -> list[EntityCandidate]`。

**作用**：处理 `search_entities` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`query`（str）；`entity_type`（str）；`limit`（int；默认 `10`；查询或展示的最大条数）。
- 输出类型：`list[EntityCandidate]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `provider`，值来自 `self.embedding_provider()`。
2. 检查 `provider.fingerprint() == 'embedding:disabled'`；按条件分流，else 分支不存在。
3. 更新 `vector`，值来自 `(await provider.encode([f<字符串常量>]))[0]`。
4. 更新 `matches`，值来自 `await self.graph_store.search_entities(vector, entity_type, limit, provider.fingerprint())`。
5. 返回 `[EntityCandidate(entity_id=entity.id, retrieval_score=score, name_score=0.0, context_score=max(0.0, min(…`。

**关键条件与保护**：
- [service.py:579](../../../src/workflow/service.py#L579)：`provider.fingerprint() == 'embedding:disabled'`，不满足时跳过本分支。

**调用与被调用**：
- `self.embedding_provider`（调用点 [service.py:578](../../../src/workflow/service.py#L578)）→ [PrismKEService.embedding_provider](service.md)，静态可定位。
- `provider.fingerprint`（[service.py:579](../../../src/workflow/service.py#L579)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `query.casefold().strip`（[service.py:580](../../../src/workflow/service.py#L580)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `query.casefold`（[service.py:580](../../../src/workflow/service.py#L580)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityCandidate`（[service.py:582](../../../src/workflow/service.py#L582)）：来自 `src.domain.EntityCandidate`；具体实现可能由依赖注入或运行时分派决定。
- `self.graph_store.list_entities`（[service.py:590](../../../src/workflow/service.py#L590)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item.name.casefold`（[service.py:593](../../../src/workflow/service.py#L593)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `a.casefold`（[service.py:593](../../../src/workflow/service.py#L593)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `provider.encode`（[service.py:595](../../../src/workflow/service.py#L595)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.search_entities`（[service.py:596](../../../src/workflow/service.py#L596)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[service.py:604](../../../src/workflow/service.py#L604)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[service.py:604](../../../src/workflow/service.py#L604)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.list_entity_reviews ⭐⭐⭐⭐

**位置与等级**：[service.py:611](../../../src/workflow/service.py#L611)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def list_entity_reviews(self, status: str | None=None) -> list[EntityReviewTask]`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`status`（str | None；默认 `None`）。
- 输出类型：`list[EntityReviewTask]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `workflow_tasks`，值来自 `[task for state in self.runs.list(limit=1000) for task in state.entity_review_tasks if status is No…`。
2. 更新 `governance_tasks`，值来自 `self.entity_governance_repository.list_tasks(status)`。
3. 返回 `sorted([*workflow_tasks, *governance_tasks], key=lambda item: item.created_at, reverse=True)`。

**调用与被调用**：
- `self.runs.list`（[service.py:614](../../../src/workflow/service.py#L614)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.entity_governance_repository.list_tasks`（[service.py:618](../../../src/workflow/service.py#L618)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[service.py:619](../../../src/workflow/service.py#L619)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.propose_entity_merge ⭐⭐

**位置与等级**：[service.py:625](../../../src/workflow/service.py#L625)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def propose_entity_merge(self, source_entity_ids: list[str], target_entity_id: str, reasons: list[str]) -> EntityReviewTask`。

**作用**：处理 `propose_entity_merge` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`source_entity_ids`（list[str]）；`target_entity_id`（str）；`reasons`（list[str]）。
- 输出类型：`EntityReviewTask`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self.entity_governance().propose_merge(source_entity_ids, target_entity_id, reasons)`。

**调用与被调用**：
- `self.entity_governance().propose_merge`（[service.py:628](../../../src/workflow/service.py#L628)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.entity_governance`（调用点 [service.py:628](../../../src/workflow/service.py#L628)）→ [PrismKEService.entity_governance](service.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.propose_entity_split ⭐⭐

**位置与等级**：[service.py:632](../../../src/workflow/service.py#L632)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def propose_entity_split(self, source_entity_id: str, target_entities: list[CanonicalEntity], claim_assignments: dict[str, str], reasons: list[str]) -> EntityReviewTask`。

**作用**：处理 `propose_entity_split` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`source_entity_id`（str）；`target_entities`（list[CanonicalEntity]）；`claim_assignments`（dict[str, str]）；`reasons`（list[str]）。
- 输出类型：`EntityReviewTask`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self.entity_governance().propose_split(source_entity_id, target_entities, claim_assignments, reaso…`。

**调用与被调用**：
- `self.entity_governance().propose_split`（[service.py:639](../../../src/workflow/service.py#L639)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.entity_governance`（调用点 [service.py:639](../../../src/workflow/service.py#L639)）→ [PrismKEService.entity_governance](service.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.review_entity_operation ⭐⭐⭐⭐

**位置与等级**：[service.py:643](../../../src/workflow/service.py#L643)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def review_entity_operation(self, task_id: str, approve: bool, reviewer: str | None=None) -> GraphRevision | None`。

**作用**：处理 `review_entity_operation` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`task_id`（str；待处理审核任务标识）；`approve`（bool）；`reviewer`（str | None；默认 `None`；审核操作者，形成审计归属）。
- 输出类型：`GraphRevision | None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not (reviewer or '').strip()`；按条件分流，else 分支不存在。
2. 更新 `result`，值来自 `await self.entity_governance().resolve_operation(task_id, approve, reviewer)`。
3. 调用 `self.audit.record`，结果未直接赋值。
4. 返回 `result`。

**关键条件与保护**：
- [service.py:646](../../../src/workflow/service.py#L646)：`not (reviewer or '').strip()`，不满足时跳过本分支。

**调用与被调用**：
- `(reviewer or '').strip`（[service.py:646](../../../src/workflow/service.py#L646)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[service.py:647](../../../src/workflow/service.py#L647)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.entity_governance().resolve_operation`（[service.py:648](../../../src/workflow/service.py#L648)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.entity_governance`（调用点 [service.py:648](../../../src/workflow/service.py#L648)）→ [PrismKEService.entity_governance](service.md)，静态可定位。
- `self.audit.record`（[service.py:649](../../../src/workflow/service.py#L649)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.entity_history ⭐⭐

**位置与等级**：[service.py:660](../../../src/workflow/service.py#L660)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def entity_history(self, entity_id: str) -> list[GraphRevision]`。

**作用**：处理 `entity_history` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`entity_id`（str）。
- 输出类型：`list[GraphRevision]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `revisions`，值来自 `await self.graph_store.list_revisions(limit=10000)`。
2. 返回 `[item for item in revisions if entity_id in item.entity_ids or any((change.resource_type == 'entity' and…`。

**调用与被调用**：
- `self.graph_store.list_revisions`（[service.py:661](../../../src/workflow/service.py#L661)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[service.py:666](../../../src/workflow/service.py#L666)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService._workflow ⭐⭐

**位置与等级**：[service.py:672](../../../src/workflow/service.py#L672)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _workflow(self, provider: LLMProvider, ocr_provider: OCRProvider, vlm_provider: VLMProvider, allow_remote_assets: bool=False, state: WorkflowState | None=None) -> PrismKEWorkflow`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`provider`（LLMProvider）；`ocr_provider`（OCRProvider）；`vlm_provider`（VLMProvider）；`allow_remote_assets`（bool；默认 `False`）；`state`（WorkflowState | None；默认 `None`；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`PrismKEWorkflow`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `reflection_service`，值来自 `None`。
2. 检查 `state is not None and state.reflection_enabled`；按条件分流，else 分支不存在。
3. 返回 `PrismKEWorkflow(provider, ocr_provider, vlm_provider, self.graph_store, self.evidence_store, self.settin…`。

**关键条件与保护**：
- [service.py:681](../../../src/workflow/service.py#L681)：`state is not None and state.reflection_enabled`，不满足时跳过本分支。

**调用与被调用**：
- `self.case_retriever`（调用点 [service.py:682](../../../src/workflow/service.py#L682)）→ [PrismKEService.case_retriever](service.md)，静态可定位。
- `BoundedReflectionService`（调用点 [service.py:683](../../../src/workflow/service.py#L683)）→ [BoundedReflectionService](reflection.md)，静态可定位。
- `self.reflection_provider`（调用点 [service.py:684](../../../src/workflow/service.py#L684)）→ [PrismKEService.reflection_provider](service.md)，静态可定位。
- `PrismKEWorkflow`（调用点 [service.py:688](../../../src/workflow/service.py#L688)）→ [PrismKEWorkflow](graph.md)，静态可定位。
- `ParserRegistry`（[service.py:696](../../../src/workflow/service.py#L696)）：来自 `src.parsing.ParserRegistry`；具体实现可能由依赖注入或运行时分派决定。
- `self.embedding_provider`（调用点 [service.py:700](../../../src/workflow/service.py#L700)）→ [PrismKEService.embedding_provider](service.md)，静态可定位。
- `self.semantic_advisor`（调用点 [service.py:706](../../../src/workflow/service.py#L706)）→ [PrismKEService.semantic_advisor](service.md)，静态可定位。
- 静态可定位的调用方：[PrismKEService._execute_run](service.md)、[PrismKEService.review_workflow](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.run ⭐⭐⭐⭐

**位置与等级**：[service.py:711](../../../src/workflow/service.py#L711)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def run(self, input_path: Path, schema_path: Path, provider_name: str, ocr_provider_name: str='disabled', vlm_provider_name: str='disabled', allow_remote_assets: bool=False, case_mode: Literal['none', 'good', 'good_bad']='none', reflection_enabled: bool=False, reflection_provider_name: str='disabled', reflection_max_attempts: int | None=None, reflection_token_budget: int | None=None, reflection_time_budget_seconds: int | None=None, semantic_advisor_name: str='disabled', agent_token_budget: int | None=None) -> WorkflowState`。

**作用**：创建并执行一次运行；具体同步/异步以及副作用以实现步骤为准。

**输入与输出**：
- 输入：`input_path`（Path）；`schema_path`（Path）；`provider_name`（str）；`ocr_provider_name`（str；默认 `'disabled'`）；`vlm_provider_name`（str；默认 `'disabled'`）；`allow_remote_assets`（bool；默认 `False`）；`case_mode`（Literal['none', 'good', 'good_bad']；默认 `'none'`）；`reflection_enabled`（bool；默认 `False`）；`reflection_provider_name`（str；默认 `'disabled'`）；`reflection_max_attempts`（int | None；默认 `None`）；`reflection_token_budget`（int | None；默认 `None`）；`reflection_time_budget_seconds`（int | None；默认 `None`）；`semantic_advisor_name`（str；默认 `'disabled'`）；`agent_token_budget`（int | None；默认 `None`）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `(state, created)`，值来自 `self.create_run(input_path, schema_path, provider_name, ocr_provider_name, vlm_provider_name, allow…`。
2. 检查 `not created`；按条件分流，else 分支不存在。
3. 返回 `await self.execute_run(state.run_id)`。

**关键条件与保护**：
- [service.py:744](../../../src/workflow/service.py#L744)：`not created`，不满足时跳过本分支。

**调用与被调用**：
- `self.create_run`（调用点 [service.py:728](../../../src/workflow/service.py#L728)）→ [PrismKEService.create_run](service.md)，静态可定位。
- `self.execute_run`（调用点 [service.py:746](../../../src/workflow/service.py#L746)）→ [PrismKEService.execute_run](service.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.create_run ⭐⭐⭐⭐

**位置与等级**：[service.py:748](../../../src/workflow/service.py#L748)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def create_run(self, input_path: Path, schema_path: Path, provider_name: str, ocr_provider_name: str='disabled', vlm_provider_name: str='disabled', allow_remote_assets: bool=False, case_mode: Literal['none', 'good', 'good_bad']='none', reflection_enabled: bool=False, reflection_provider_name: str='disabled', reflection_max_attempts: int | None=None, reflection_token_budget: int | None=None, reflection_time_budget_seconds: int | None=None, semantic_advisor_name: str='disabled', agent_token_budget: int | None=None) -> tuple[WorkflowState, bool]`。

**作用**：Validate a request and persist its initial state without executing it.

**输入与输出**：
- 输入：`input_path`（Path）；`schema_path`（Path）；`provider_name`（str）；`ocr_provider_name`（str；默认 `'disabled'`）；`vlm_provider_name`（str；默认 `'disabled'`）；`allow_remote_assets`（bool；默认 `False`）；`case_mode`（Literal['none', 'good', 'good_bad']；默认 `'none'`）；`reflection_enabled`（bool；默认 `False`）；`reflection_provider_name`（str；默认 `'disabled'`）；`reflection_max_attempts`（int | None；默认 `None`）；`reflection_token_budget`（int | None；默认 `None`）；`reflection_time_budget_seconds`（int | None；默认 `None`）；`semantic_advisor_name`（str；默认 `'disabled'`）；`agent_token_budget`（int | None；默认 `None`）。
- 输出类型：`tuple[WorkflowState, bool]`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.executions.ensure_accepting`，结果未直接赋值。
2. 检查 `self.review_metadata`；按条件分流，else 分支不存在。
3. 更新 `input_path`，值来自 `input_path.resolve()`。
4. 更新 `schema_path`，值来自 `schema_path.resolve()`。
5. 更新 `provider`，值来自 `self.provider(provider_name)`。
6. 更新 `ocr_provider`，值来自 `self.ocr_provider(ocr_provider_name)`。
7. 更新 `vlm_provider`，值来自 `self.vlm_provider(vlm_provider_name)`。
8. 更新 `embedding_provider`，值来自 `self.embedding_provider()`。
9. 检查 `case_mode not in {'none', 'good', 'good_bad'}`；按条件分流，else 分支不存在。
10. 检查 `case_mode != 'none' and embedding_provider.fingerprint() == 'embedding:disabled'`；按条件分流，else 分支不存在。
11. 更新 `max_attempts`，值来自 `self.settings.reflection_max_attempts if reflection_max_attempts is None else reflection_max_attemp…`。
12. 更新 `token_budget`，值来自 `self.settings.reflection_token_budget if reflection_token_budget is None else reflection_token_budg…`。
13. 更新 `time_budget`，值来自 `self.settings.reflection_time_budget_seconds if reflection_time_budget_seconds is None else reflect…`。
14. 检查 `not 0 <= max_attempts <= 2`；按条件分流，else 分支不存在。
15. 检查 `token_budget <= 0 or time_budget <= 0`；按条件分流，else 分支不存在。
16. 更新 `reflection`，值来自 `self.reflection_provider(reflection_provider_name if reflection_enabled else 'disabled')`。
17. 检查 `reflection_enabled and reflection.fingerprint() == 'reflection:disabled'`；按条件分流，else 分支不存在。
18. 更新 `advisor`，值来自 `self.semantic_advisor(semantic_advisor_name)`。
19. 更新 `advice_budget`，值来自 `self.settings.agent_token_budget if agent_token_budget is None else agent_token_budget`。
20. 检查 `advice_budget <= 0`；按条件分流，else 分支不存在。
21. 更新 `retriever`，值来自 `self.case_retriever() if case_mode != 'none' else None`。
22. 更新 `case_snapshot_ids`，值来自 `retriever.snapshot_ids() if retriever else []`。
23. 更新 `case_snapshot`，值来自 `retriever.fingerprint_for(case_snapshot_ids) if retriever else 'cases:none'`。
24. 更新 `schema`，值来自 `load_schema(schema_path)`。
后续还有 5 个语句级步骤，见源码对应行；这里优先保留主要控制流。

**关键条件与保护**：
- [service.py:767](../../../src/workflow/service.py#L767)：`self.review_metadata`，不满足时跳过本分支。
- [service.py:775](../../../src/workflow/service.py#L775)：`case_mode not in {'none', 'good', 'good_bad'}`，不满足时跳过本分支。
- [service.py:777](../../../src/workflow/service.py#L777)：`case_mode != 'none' and embedding_provider.fingerprint() == 'embedding:disabled'`，不满足时跳过本分支。
- [service.py:794](../../../src/workflow/service.py#L794)：`not 0 <= max_attempts <= 2`，不满足时跳过本分支。
- [service.py:796](../../../src/workflow/service.py#L796)：`token_budget <= 0 or time_budget <= 0`，不满足时跳过本分支。
- [service.py:801](../../../src/workflow/service.py#L801)：`reflection_enabled and reflection.fingerprint() == 'reflection:disabled'`，不满足时跳过本分支。
- [service.py:809](../../../src/workflow/service.py#L809)：`advice_budget <= 0`，不满足时跳过本分支。
- [service.py:848](../../../src/workflow/service.py#L848)：`self.runs.exists(run_id)`，不满足时跳过本分支。
- [service.py:884](../../../src/workflow/service.py#L884)：`self.runs.exists(run_id)`，不满足时跳过本分支。

**调用与被调用**：
- `self.executions.ensure_accepting`（[service.py:766](../../../src/workflow/service.py#L766)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[service.py:768](../../../src/workflow/service.py#L768)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `input_path.resolve`（[service.py:769](../../../src/workflow/service.py#L769)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `schema_path.resolve`（[service.py:770](../../../src/workflow/service.py#L770)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.provider`（调用点 [service.py:771](../../../src/workflow/service.py#L771)）→ [PrismKEService.provider](service.md)，静态可定位。
- `self.ocr_provider`（调用点 [service.py:772](../../../src/workflow/service.py#L772)）→ [PrismKEService.ocr_provider](service.md)，静态可定位。
- `self.vlm_provider`（调用点 [service.py:773](../../../src/workflow/service.py#L773)）→ [PrismKEService.vlm_provider](service.md)，静态可定位。
- `self.embedding_provider`（调用点 [service.py:774](../../../src/workflow/service.py#L774)）→ [PrismKEService.embedding_provider](service.md)，静态可定位。
- `embedding_provider.fingerprint`（[service.py:777](../../../src/workflow/service.py#L777)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ProviderConfigurationError`（调用点 [service.py:778](../../../src/workflow/service.py#L778)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- `self.reflection_provider`（调用点 [service.py:798](../../../src/workflow/service.py#L798)）→ [PrismKEService.reflection_provider](service.md)，静态可定位。
- `reflection.fingerprint`（[service.py:801](../../../src/workflow/service.py#L801)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.semantic_advisor`（调用点 [service.py:805](../../../src/workflow/service.py#L805)）→ [PrismKEService.semantic_advisor](service.md)，静态可定位。
- `self.case_retriever`（调用点 [service.py:811](../../../src/workflow/service.py#L811)）→ [PrismKEService.case_retriever](service.md)，静态可定位。
- `retriever.snapshot_ids`（[service.py:812](../../../src/workflow/service.py#L812)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `retriever.fingerprint_for`（[service.py:813](../../../src/workflow/service.py#L813)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `load_schema`（[service.py:814](../../../src/workflow/service.py#L814)）：来自 `src.domain.load_schema`；具体实现可能由依赖注入或运行时分派决定。
- `canonical_hash`（调用点 [service.py:815](../../../src/workflow/service.py#L815)）→ [canonical_hash](../core/ids.md)，静态可定位。
- `schema.model_dump`（[service.py:815](../../../src/workflow/service.py#L815)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `stable_id`（调用点 [service.py:816](../../../src/workflow/service.py#L816)）→ [stable_id](../core/ids.md)，静态可定位。
- `file_sha256`（调用点 [service.py:818](../../../src/workflow/service.py#L818)）→ [file_sha256](../core/ids.md)，静态可定位。
- `provider.fingerprint`（[service.py:821](../../../src/workflow/service.py#L821)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ocr_provider.fingerprint`（[service.py:822](../../../src/workflow/service.py#L822)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `vlm_provider.fingerprint`（[service.py:823](../../../src/workflow/service.py#L823)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `advisor.fingerprint`（[service.py:828](../../../src/workflow/service.py#L828)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.runs.exists`（[service.py:848](../../../src/workflow/service.py#L848)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.runs.load`（[service.py:849](../../../src/workflow/service.py#L849)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `WorkflowState`（[service.py:850](../../../src/workflow/service.py#L850)）：来自 `src.domain.WorkflowState`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[service.py:852](../../../src/workflow/service.py#L852)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.runs.creation_lock`（[service.py:883](../../../src/workflow/service.py#L883)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 此处列出前 30 个不同调用表达式，另有 2 个，需按源码继续追踪。
- 静态可定位的调用方：[PrismKEService.run](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`、`ProviderConfigurationError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.execute_run ⭐⭐⭐⭐

**位置与等级**：[service.py:890](../../../src/workflow/service.py#L890)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def execute_run(self, run_id: str) -> WorkflowState`。

**作用**：处理 `execute_run` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self.executions.run_wait(run_id, 'execute')`。

**调用与被调用**：
- `self.executions.run_wait`（[service.py:891](../../../src/workflow/service.py#L891)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[PrismKEService.run](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService._execute_run ⭐⭐

**位置与等级**：[service.py:893](../../../src/workflow/service.py#L893)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _execute_run(self, run_id: str) -> WorkflowState`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self.review_metadata`；按条件分流，else 分支不存在。
2. 更新 `state`，值来自 `self.runs.load(run_id)`。
3. 调用 `self._validate_entity_policy`，结果未直接赋值。
4. 更新 `provider`，值来自 `self.provider(state.provider_name)`。
5. 更新 `ocr_provider`，值来自 `self.ocr_provider(state.ocr_provider_name)`。
6. 更新 `vlm_provider`，值来自 `self.vlm_provider(state.vlm_provider_name)`。
7. 调用 `self._validate_reflection_policy`，结果未直接赋值。
8. 调用 `self._validate_agent_policy`，结果未直接赋值。
9. 返回 `await self._workflow(provider, ocr_provider, vlm_provider, state.allow_remote_assets, state).invoke(stat…`。

**关键条件与保护**：
- [service.py:894](../../../src/workflow/service.py#L894)：`self.review_metadata`，不满足时跳过本分支。

**调用与被调用**：
- `ValueError`（[service.py:895](../../../src/workflow/service.py#L895)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.runs.load`（[service.py:896](../../../src/workflow/service.py#L896)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._validate_entity_policy`（调用点 [service.py:897](../../../src/workflow/service.py#L897)）→ [PrismKEService._validate_entity_policy](service.md)，静态可定位。
- `self.provider`（调用点 [service.py:898](../../../src/workflow/service.py#L898)）→ [PrismKEService.provider](service.md)，静态可定位。
- `self.ocr_provider`（调用点 [service.py:899](../../../src/workflow/service.py#L899)）→ [PrismKEService.ocr_provider](service.md)，静态可定位。
- `self.vlm_provider`（调用点 [service.py:900](../../../src/workflow/service.py#L900)）→ [PrismKEService.vlm_provider](service.md)，静态可定位。
- `self._validate_reflection_policy`（调用点 [service.py:901](../../../src/workflow/service.py#L901)）→ [PrismKEService._validate_reflection_policy](service.md)，静态可定位。
- `self._validate_agent_policy`（调用点 [service.py:902](../../../src/workflow/service.py#L902)）→ [PrismKEService._validate_agent_policy](service.md)，静态可定位。
- `self._workflow(provider, ocr_provider, vlm_provider, state.allow_remote_assets, state).in…`（[service.py:903](../../../src/workflow/service.py#L903)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._workflow`（调用点 [service.py:903](../../../src/workflow/service.py#L903)）→ [PrismKEService._workflow](service.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.show_run ⭐⭐⭐⭐

**位置与等级**：[service.py:911](../../../src/workflow/service.py#L911)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def show_run(self, run_id: str) -> WorkflowState`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.runs.load(run_id)`。

**调用与被调用**：
- `self.runs.load`（[service.py:912](../../../src/workflow/service.py#L912)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[PrismKEService.validate_run](service.md)、[PrismKEService.exclude_validation_issue](service.md)、[PrismKEService.entity_review_detail](service.md)、[PrismKEService.claim_review_detail](service.md)、[PrismKEService.review_progress](service.md)、[PrismKEService.review](service.md)、[PrismKEService._confirm_review_commit](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.entity_review_detail ⭐⭐⭐⭐

**位置与等级**：[service.py:914](../../../src/workflow/service.py#L914)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def entity_review_detail(self, run_id: str, task_id: str) -> dict[str, Any]`。

**作用**：处理 `entity_review_detail` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`task_id`（str；待处理审核任务标识）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state`，值来自 `self.show_run(run_id)`。
2. 更新 `detail`，值来自 `entity_task_base(state, task_id)`。
3. 更新 `entities`，值来自 `{item.id: item for item in state.entities}`。
4. 更新 `candidates`，值来自 `[]`。
5. 更新 `task`，值来自 `next((item for item in state.entity_review_tasks if item.id == task_id))`。
6. 遍历 `task.candidates`，逐项处理 `score`。
7. 更新 `detail['candidates']`，值来自 `candidates`。
8. 更新 `detail['margin']`，值来自 `next((item.margin for item in state.entity_resolution_decisions if item.mention_id == task.mention_…`。
9. 返回 `detail`。

**调用与被调用**：
- `self.show_run`（调用点 [service.py:917](../../../src/workflow/service.py#L917)）→ [PrismKEService.show_run](service.md)，静态可定位。
- `entity_task_base`（调用点 [service.py:918](../../../src/workflow/service.py#L918)）→ [entity_task_base](review_details.md)，静态可定位。
- `next`（[service.py:921](../../../src/workflow/service.py#L921)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `entities.get`（[service.py:923](../../../src/workflow/service.py#L923)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.get_entity`（[service.py:923](../../../src/workflow/service.py#L923)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `candidates.append`（[service.py:926](../../../src/workflow/service.py#L926)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `score.model_dump`（[service.py:928](../../../src/workflow/service.py#L928)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `entity.model_dump`（[service.py:929](../../../src/workflow/service.py#L929)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`detail['candidates']`、`detail['margin']`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.claim_review_detail ⭐⭐⭐⭐

**位置与等级**：[service.py:943](../../../src/workflow/service.py#L943)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def claim_review_detail(self, run_id: str, task_id: str) -> dict[str, Any]`。

**作用**：处理 `claim_review_detail` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`task_id`（str；待处理审核任务标识）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 (KeyError, StopIteration)；另检查 finally/else 的清理和传播。

**关键条件与保护**：
- [service.py:957](../../../src/workflow/service.py#L957)：`event is None`，不满足时跳过本分支。

**调用与被调用**：
- `claim_task_detail`（调用点 [service.py:947](../../../src/workflow/service.py#L947)）→ [claim_task_detail](review_details.md)，静态可定位。
- `self.show_run`（调用点 [service.py:947](../../../src/workflow/service.py#L947)）→ [PrismKEService.show_run](service.md)，静态可定位。
- `next`（[service.py:949](../../../src/workflow/service.py#L949)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `reversed`（[service.py:952](../../../src/workflow/service.py#L952)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.reviews.repository.events`（[service.py:952](../../../src/workflow/service.py#L952)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `KeyError`（[service.py:958](../../../src/workflow/service.py#L958)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `WorkflowState.model_validate`（[service.py:959](../../../src/workflow/service.py#L959)）：来自 `src.domain.WorkflowState`；具体实现可能由依赖注入或运行时分派决定。
- `self.reviews.repository.event_state`（[service.py:959](../../../src/workflow/service.py#L959)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`detail['historical_only']`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`KeyError(<字符串常量>)`。
- 本地捕获：`(KeyError, StopIteration)`。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.review_progress ⭐⭐⭐⭐

**位置与等级**：[service.py:964](../../../src/workflow/service.py#L964)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def review_progress(self, run_id: str) -> dict[str, Any]`。

**作用**：处理 `review_progress` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state`，值来自 `self.show_run(run_id)`。
2. 更新 `entity_pending`，值来自 `sum((item.status == 'pending' for item in state.entity_review_tasks))`。
3. 更新 `claim_pending`，值来自 `sum((item.status == 'pending' for item in state.review_tasks))`。
4. 更新 `retry_commit`，值来自 `state.status == 'failed' and state.failed_node == 'commit_graph'`。
5. 更新 `sync_pending`，值来自 `bool(self.reviews.repository.pending(run_id))`。
6. 更新 `execution`，值来自 `self.executions.view(run_id)`。
7. 返回 `{'run_id': run_id, 'status': state.status, 'node': state.current_node, 'execution': execution, 'entity_p…`。

**调用与被调用**：
- `self.show_run`（调用点 [service.py:965](../../../src/workflow/service.py#L965)）→ [PrismKEService.show_run](service.md)，静态可定位。
- `sum`（[service.py:966](../../../src/workflow/service.py#L966)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `bool`（[service.py:969](../../../src/workflow/service.py#L969)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.reviews.repository.pending`（[service.py:969](../../../src/workflow/service.py#L969)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.executions.view`（[service.py:970](../../../src/workflow/service.py#L970)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[service.py:1000](../../../src/workflow/service.py#L1000)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `c.model_dump`（[service.py:1006](../../../src/workflow/service.py#L1006)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.review_workflow ⭐⭐⭐⭐

**位置与等级**：[service.py:1014](../../../src/workflow/service.py#L1014)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def review_workflow(self, state: WorkflowState) -> PrismKEWorkflow`。

**作用**：处理 `review_workflow` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`PrismKEWorkflow`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `state.pipeline_version == PIPELINE_VERSION and state.current_node in {'resolve_entities', 'normalize_cla…`；按条件分流，else 分支不存在。
2. 检查 `self.review_metadata`；按条件分流，else 分支不存在。
3. 检查 `not state.review_workspace`；按条件分流，else 分支不存在。
4. 调用 `validate_workspace_run`，结果未直接赋值。
5. 调用 `self._validate_entity_policy`，结果未直接赋值。
6. 返回 `PrismKEWorkflow(MockLLMProvider(), DisabledOCRProvider(), DisabledVLMProvider(), self.graph_store, self.…`。

**关键条件与保护**：
- [service.py:1015](../../../src/workflow/service.py#L1015)：`state.pipeline_version == PIPELINE_VERSION and state.current_node in {'resolve_entities', 'normalize_claims', 'det…`，不满足时跳过本分支。
- [service.py:1027](../../../src/workflow/service.py#L1027)：`self.review_metadata`，不满足时跳过本分支。
- [service.py:1029](../../../src/workflow/service.py#L1029)：`not state.review_workspace`，不满足时跳过本分支。

**调用与被调用**：
- `self.review_tail_workflow`（调用点 [service.py:1023](../../../src/workflow/service.py#L1023)）→ [PrismKEService.review_tail_workflow](service.md)，静态可定位。
- `validate_workspace_run`（调用点 [service.py:1028](../../../src/workflow/service.py#L1028)）→ [validate_workspace_run](review_workspace.md)，静态可定位。
- `self._validated_run_providers`（调用点 [service.py:1030](../../../src/workflow/service.py#L1030)）→ [PrismKEService._validated_run_providers](service.md)，静态可定位。
- `self._validate_reflection_policy`（调用点 [service.py:1031](../../../src/workflow/service.py#L1031)）→ [PrismKEService._validate_reflection_policy](service.md)，静态可定位。
- `self._workflow`（调用点 [service.py:1032](../../../src/workflow/service.py#L1032)）→ [PrismKEService._workflow](service.md)，静态可定位。
- `self._validate_entity_policy`（调用点 [service.py:1034](../../../src/workflow/service.py#L1034)）→ [PrismKEService._validate_entity_policy](service.md)，静态可定位。
- `PrismKEWorkflow`（调用点 [service.py:1035](../../../src/workflow/service.py#L1035)）→ [PrismKEWorkflow](graph.md)，静态可定位。
- `MockLLMProvider`（[service.py:1036](../../../src/workflow/service.py#L1036)）：来自 `src.providers.MockLLMProvider`；具体实现可能由依赖注入或运行时分派决定。
- `DisabledOCRProvider`（[service.py:1037](../../../src/workflow/service.py#L1037)）：来自 `src.providers.DisabledOCRProvider`；具体实现可能由依赖注入或运行时分派决定。
- `DisabledVLMProvider`（[service.py:1038](../../../src/workflow/service.py#L1038)）：来自 `src.providers.DisabledVLMProvider`；具体实现可能由依赖注入或运行时分派决定。
- `DisabledEmbeddingProvider`（[service.py:1043](../../../src/workflow/service.py#L1043)）：来自 `src.providers.DisabledEmbeddingProvider`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[PrismKEService.exclude_validation_issue](service.md)、[PrismKEService._resume](service.md)、[PrismKEService._confirm_review_commit](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.review_tail_workflow ⭐⭐⭐⭐

**位置与等级**：[service.py:1047](../../../src/workflow/service.py#L1047)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def review_tail_workflow(self, state: WorkflowState, *, use_embeddings: bool=False) -> PrismKEWorkflow`。

**作用**：处理 `review_tail_workflow` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）；`use_embeddings`（bool；默认 `False`）。
- 输出类型：`PrismKEWorkflow`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self.reviews.compatible`，结果未直接赋值。
2. 检查 `state.review_workspace`；按条件分流，else 分支不存在。
3. 更新 `embedding`，值来自 `DisabledEmbeddingProvider()`。
4. 检查 `use_embeddings`；按条件分流，else 分支不存在。
5. 返回 `PrismKEWorkflow(MockLLMProvider(), DisabledOCRProvider(), DisabledVLMProvider(), self.graph_store, self.…`。

**关键条件与保护**：
- [service.py:1051](../../../src/workflow/service.py#L1051)：`state.review_workspace`，不满足时跳过本分支。
- [service.py:1054](../../../src/workflow/service.py#L1054)：`use_embeddings`，不满足时跳过本分支。
- [service.py:1056](../../../src/workflow/service.py#L1056)：`embedding.fingerprint() != state.embedding_provider_fingerprint`，不满足时跳过本分支。

**调用与被调用**：
- `self.reviews.compatible`（[service.py:1050](../../../src/workflow/service.py#L1050)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `validate_workspace_run`（调用点 [service.py:1052](../../../src/workflow/service.py#L1052)）→ [validate_workspace_run](review_workspace.md)，静态可定位。
- `DisabledEmbeddingProvider`（[service.py:1053](../../../src/workflow/service.py#L1053)）：来自 `src.providers.DisabledEmbeddingProvider`；具体实现可能由依赖注入或运行时分派决定。
- `self.embedding_provider`（调用点 [service.py:1055](../../../src/workflow/service.py#L1055)）→ [PrismKEService.embedding_provider](service.md)，静态可定位。
- `embedding.fingerprint`（[service.py:1056](../../../src/workflow/service.py#L1056)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ProviderConfigurationError`（调用点 [service.py:1057](../../../src/workflow/service.py#L1057)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- `PrismKEWorkflow`（调用点 [service.py:1060](../../../src/workflow/service.py#L1060)）→ [PrismKEWorkflow](graph.md)，静态可定位。
- `MockLLMProvider`（[service.py:1061](../../../src/workflow/service.py#L1061)）：来自 `src.providers.MockLLMProvider`；具体实现可能由依赖注入或运行时分派决定。
- `DisabledOCRProvider`（[service.py:1062](../../../src/workflow/service.py#L1062)）：来自 `src.providers.DisabledOCRProvider`；具体实现可能由依赖注入或运行时分派决定。
- `DisabledVLMProvider`（[service.py:1063](../../../src/workflow/service.py#L1063)）：来自 `src.providers.DisabledVLMProvider`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[PrismKEService.review_workflow](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderConfigurationError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService._validated_run_providers ⭐⭐

**位置与等级**：[service.py:1072](../../../src/workflow/service.py#L1072)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _validated_run_providers(self, state: WorkflowState) -> tuple[LLMProvider, OCRProvider, VLMProvider]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`tuple[LLMProvider, OCRProvider, VLMProvider]`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `self._validate_entity_policy`，结果未直接赋值。
2. 更新 `provider`，值来自 `self.provider(state.provider_name)`。
3. 更新 `ocr_provider`，值来自 `self.ocr_provider(state.ocr_provider_name)`。
4. 更新 `vlm_provider`，值来自 `self.vlm_provider(state.vlm_provider_name)`。
5. 更新 `embedding_provider`，值来自 `self.embedding_provider()`。
6. 检查 `state.provider_fingerprint == 'legacy'`；按条件分流，else 分支不存在。
7. 检查 `state.provider_fingerprint != provider.fingerprint()`；按条件分流，else 分支不存在。
8. 检查 `state.ocr_provider_fingerprint != ocr_provider.fingerprint()`；按条件分流，else 分支不存在。
9. 检查 `state.vlm_provider_fingerprint != vlm_provider.fingerprint()`；按条件分流，else 分支不存在。
10. 检查 `state.embedding_provider_fingerprint != embedding_provider.fingerprint()`；按条件分流，else 分支不存在。
11. 调用 `self._validate_reflection_policy`，结果未直接赋值。
12. 调用 `self._validate_agent_policy`，结果未直接赋值。
13. 返回 `(provider, ocr_provider, vlm_provider)`。

**关键条件与保护**：
- [service.py:1080](../../../src/workflow/service.py#L1080)：`state.provider_fingerprint == 'legacy'`，不满足时跳过本分支。
- [service.py:1084](../../../src/workflow/service.py#L1084)：`state.provider_fingerprint != provider.fingerprint()`，不满足时跳过本分支。
- [service.py:1086](../../../src/workflow/service.py#L1086)：`state.ocr_provider_fingerprint != ocr_provider.fingerprint()`，不满足时跳过本分支。
- [service.py:1090](../../../src/workflow/service.py#L1090)：`state.vlm_provider_fingerprint != vlm_provider.fingerprint()`，不满足时跳过本分支。
- [service.py:1094](../../../src/workflow/service.py#L1094)：`state.embedding_provider_fingerprint != embedding_provider.fingerprint()`，不满足时跳过本分支。

**调用与被调用**：
- `self._validate_entity_policy`（调用点 [service.py:1075](../../../src/workflow/service.py#L1075)）→ [PrismKEService._validate_entity_policy](service.md)，静态可定位。
- `self.provider`（调用点 [service.py:1076](../../../src/workflow/service.py#L1076)）→ [PrismKEService.provider](service.md)，静态可定位。
- `self.ocr_provider`（调用点 [service.py:1077](../../../src/workflow/service.py#L1077)）→ [PrismKEService.ocr_provider](service.md)，静态可定位。
- `self.vlm_provider`（调用点 [service.py:1078](../../../src/workflow/service.py#L1078)）→ [PrismKEService.vlm_provider](service.md)，静态可定位。
- `self.embedding_provider`（调用点 [service.py:1079](../../../src/workflow/service.py#L1079)）→ [PrismKEService.embedding_provider](service.md)，静态可定位。
- `LegacyCheckpointError`（调用点 [service.py:1081](../../../src/workflow/service.py#L1081)）→ [LegacyCheckpointError](../core/errors.md)，静态可定位。
- `provider.fingerprint`（[service.py:1084](../../../src/workflow/service.py#L1084)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ProviderConfigurationError`（调用点 [service.py:1085](../../../src/workflow/service.py#L1085)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- `ocr_provider.fingerprint`（[service.py:1086](../../../src/workflow/service.py#L1086)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `vlm_provider.fingerprint`（[service.py:1090](../../../src/workflow/service.py#L1090)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `embedding_provider.fingerprint`（[service.py:1094](../../../src/workflow/service.py#L1094)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._validate_reflection_policy`（调用点 [service.py:1098](../../../src/workflow/service.py#L1098)）→ [PrismKEService._validate_reflection_policy](service.md)，静态可定位。
- `self._validate_agent_policy`（调用点 [service.py:1099](../../../src/workflow/service.py#L1099)）→ [PrismKEService._validate_agent_policy](service.md)，静态可定位。
- 静态可定位的调用方：[PrismKEService.review_workflow](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`LegacyCheckpointError(<字符串常量>)`、`ProviderConfigurationError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService._validate_agent_policy ⭐⭐

**位置与等级**：[service.py:1102](../../../src/workflow/service.py#L1102)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _validate_agent_policy(self, state: WorkflowState) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `state.agent_policy_version != AGENT_POLICY_VERSION`；按条件分流，else 分支不存在。
2. 更新 `advisor`，值来自 `self.semantic_advisor(state.semantic_advisor_name)`。
3. 检查 `advisor.fingerprint() != state.semantic_advisor_fingerprint`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [service.py:1103](../../../src/workflow/service.py#L1103)：`state.agent_policy_version != AGENT_POLICY_VERSION`，不满足时跳过本分支。
- [service.py:1108](../../../src/workflow/service.py#L1108)：`advisor.fingerprint() != state.semantic_advisor_fingerprint`，不满足时跳过本分支。

**调用与被调用**：
- `LegacyCheckpointError`（调用点 [service.py:1104](../../../src/workflow/service.py#L1104)）→ [LegacyCheckpointError](../core/errors.md)，静态可定位。
- `self.semantic_advisor`（调用点 [service.py:1107](../../../src/workflow/service.py#L1107)）→ [PrismKEService.semantic_advisor](service.md)，静态可定位。
- `advisor.fingerprint`（[service.py:1108](../../../src/workflow/service.py#L1108)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ProviderConfigurationError`（调用点 [service.py:1109](../../../src/workflow/service.py#L1109)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- 静态可定位的调用方：[PrismKEService._execute_run](service.md)、[PrismKEService._validated_run_providers](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`LegacyCheckpointError(<字符串常量>)`、`ProviderConfigurationError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService._validate_reflection_policy ⭐⭐

**位置与等级**：[service.py:1113](../../../src/workflow/service.py#L1113)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _validate_reflection_policy(self, state: WorkflowState) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `state.case_retrieval_policy_version != CASE_RETRIEVAL_VERSION`；按条件分流，else 分支不存在。
2. 检查 `state.reflection_policy_version != REFLECTION_POLICY_VERSION`；按条件分流，else 分支不存在。
3. 更新 `reflection`，值来自 `self.reflection_provider(state.reflection_provider_name)`。
4. 检查 `reflection.fingerprint() != state.reflection_provider_fingerprint`；按条件分流，else 分支不存在。
5. 检查 `state.case_mode != 'none'`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [service.py:1114](../../../src/workflow/service.py#L1114)：`state.case_retrieval_policy_version != CASE_RETRIEVAL_VERSION`，不满足时跳过本分支。
- [service.py:1118](../../../src/workflow/service.py#L1118)：`state.reflection_policy_version != REFLECTION_POLICY_VERSION`，不满足时跳过本分支。
- [service.py:1123](../../../src/workflow/service.py#L1123)：`reflection.fingerprint() != state.reflection_provider_fingerprint`，不满足时跳过本分支。
- [service.py:1127](../../../src/workflow/service.py#L1127)：`state.case_mode != 'none'`，不满足时跳过本分支。
- [service.py:1129](../../../src/workflow/service.py#L1129)：`expected != state.case_snapshot_fingerprint`，不满足时跳过本分支。

**调用与被调用**：
- `LegacyCheckpointError`（调用点 [service.py:1115](../../../src/workflow/service.py#L1115)）→ [LegacyCheckpointError](../core/errors.md)，静态可定位。
- `self.reflection_provider`（调用点 [service.py:1122](../../../src/workflow/service.py#L1122)）→ [PrismKEService.reflection_provider](service.md)，静态可定位。
- `reflection.fingerprint`（[service.py:1123](../../../src/workflow/service.py#L1123)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ProviderConfigurationError`（调用点 [service.py:1124](../../../src/workflow/service.py#L1124)）→ [ProviderConfigurationError](../core/errors.md)，静态可定位。
- `self.case_retriever().fingerprint_for`（[service.py:1128](../../../src/workflow/service.py#L1128)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.case_retriever`（调用点 [service.py:1128](../../../src/workflow/service.py#L1128)）→ [PrismKEService.case_retriever](service.md)，静态可定位。
- 静态可定位的调用方：[PrismKEService._execute_run](service.md)、[PrismKEService.review_workflow](service.md)、[PrismKEService._validated_run_providers](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`LegacyCheckpointError(<字符串常量>)`、`ProviderConfigurationError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService._validate_entity_policy ⭐⭐

**位置与等级**：[service.py:1133](../../../src/workflow/service.py#L1133)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _validate_entity_policy(state: WorkflowState) -> None`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`state`（WorkflowState；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `state.entity_resolution_policy_version != ENTITY_RESOLUTION_POLICY_VERSION`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [service.py:1134](../../../src/workflow/service.py#L1134)：`state.entity_resolution_policy_version != ENTITY_RESOLUTION_POLICY_VERSION`，不满足时跳过本分支。

**调用与被调用**：
- `LegacyCheckpointError`（调用点 [service.py:1135](../../../src/workflow/service.py#L1135)）→ [LegacyCheckpointError](../core/errors.md)，静态可定位。
- 静态可定位的调用方：[PrismKEService._execute_run](service.md)、[PrismKEService.review_workflow](service.md)、[PrismKEService._validated_run_providers](service.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`LegacyCheckpointError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.review ⭐⭐⭐⭐

**位置与等级**：[service.py:1139](../../../src/workflow/service.py#L1139)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def review(self, run_id: str, claim_id: str, decision: ReviewDecision, reviewer: str | None=None, comment: str | None=None, expected_version: int | None=None, request_id: str | None=None) -> WorkflowState`。

**作用**：处理 `review` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`claim_id`（str）；`decision`（ReviewDecision）；`reviewer`（str | None；默认 `None`；审核操作者，形成审计归属）；`comment`（str | None；默认 `None`）；`expected_version`（int | None；默认 `None`；乐观并发版本；过期提交应拒绝）；`request_id`（str | None；默认 `None`；幂等请求标识，避免重复动作）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.runs.mutation_lock(run_id)`，由上下文管理器控制资源释放或事务范围。

**关键条件与保护**：
- [service.py:1152](../../../src/workflow/service.py#L1152)：`task is None`，不满足时跳过本分支。

**调用与被调用**：
- `self.runs.mutation_lock`（[service.py:1149](../../../src/workflow/service.py#L1149)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.show_run`（调用点 [service.py:1150](../../../src/workflow/service.py#L1150)）→ [PrismKEService.show_run](service.md)，静态可定位。
- `next`（[service.py:1151](../../../src/workflow/service.py#L1151)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `KeyError`（[service.py:1153](../../../src/workflow/service.py#L1153)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.reviews.decide`（[service.py:1154](../../../src/workflow/service.py#L1154)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`KeyError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.review_entity ⭐⭐⭐⭐

**位置与等级**：[service.py:1166](../../../src/workflow/service.py#L1166)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def review_entity(self, run_id: str, task_id: str, decision: Literal['link', 'create', 'reject', 'defer'], selected_entity_id: str | None=None, reviewer: str | None=None, comment: str | None=None, expected_version: int | None=None, request_id: str | None=None) -> WorkflowState`。

**作用**：处理 `review_entity` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`task_id`（str；待处理审核任务标识）；`decision`（Literal['link', 'create', 'reject', 'defer']）；`selected_entity_id`（str | None；默认 `None`）；`reviewer`（str | None；默认 `None`；审核操作者，形成审计归属）；`comment`（str | None；默认 `None`）；`expected_version`（int | None；默认 `None`；乐观并发版本；过期提交应拒绝）；`request_id`（str | None；默认 `None`；幂等请求标识，避免重复动作）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 进入上下文 `self.runs.mutation_lock(run_id)`，由上下文管理器控制资源释放或事务范围。

**调用与被调用**：
- `self.runs.mutation_lock`（[service.py:1177](../../../src/workflow/service.py#L1177)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.reviews.decide`（[service.py:1178](../../../src/workflow/service.py#L1178)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.resume ⭐⭐⭐⭐

**位置与等级**：[service.py:1190](../../../src/workflow/service.py#L1190)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def resume(self, run_id: str) -> WorkflowState`。

**作用**：从已有运行/检查点继续；恢复前须核对策略、版本及安全阻断。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self.executions.run_wait(run_id, 'resume')`。

**调用与被调用**：
- `self.executions.run_wait`（[service.py:1191](../../../src/workflow/service.py#L1191)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService._resume ⭐⭐

**位置与等级**：[service.py:1193](../../../src/workflow/service.py#L1193)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _resume(self, run_id: str) -> WorkflowState`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 等待 `self.reviews.recover(run_id)` 完成。
2. 更新 `state`，值来自 `self.runs.load(run_id)`。
3. 检查 `state.pipeline_version != PIPELINE_VERSION`；按条件分流，else 分支不存在。
4. 检查 `state.validation.blocking_count or any((task.status == 'pending' for task in state.entity_review_tasks))…`；按条件分流，else 分支不存在。
5. 更新 `workflow`，值来自 `self.review_workflow(state)`。
6. 更新 `state.status`，值来自 `'running'`。
7. 更新 `result`，值来自 `await workflow.resume(run_id)`。
8. 检查 `result is None`；按条件分流，else 分支不存在。
9. 返回 `result`。

**关键条件与保护**：
- [service.py:1196](../../../src/workflow/service.py#L1196)：`state.pipeline_version != PIPELINE_VERSION`，不满足时跳过本分支。
- [service.py:1200](../../../src/workflow/service.py#L1200)：`state.validation.blocking_count or any((task.status == 'pending' for task in state.entity_review_tasks)) or any((t…`，不满足时跳过本分支。
- [service.py:1209](../../../src/workflow/service.py#L1209)：`result is None`，不满足时跳过本分支。

**调用与被调用**：
- `self.reviews.recover`（[service.py:1194](../../../src/workflow/service.py#L1194)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.runs.load`（[service.py:1195](../../../src/workflow/service.py#L1195)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `LegacyCheckpointError`（调用点 [service.py:1197](../../../src/workflow/service.py#L1197)）→ [LegacyCheckpointError](../core/errors.md)，静态可定位。
- `any`（[service.py:1202](../../../src/workflow/service.py#L1202)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[service.py:1205](../../../src/workflow/service.py#L1205)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.review_workflow`（调用点 [service.py:1206](../../../src/workflow/service.py#L1206)）→ [PrismKEService.review_workflow](service.md)，静态可定位。
- `workflow.resume`（[service.py:1208](../../../src/workflow/service.py#L1208)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`state.status`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`LegacyCheckpointError(f<字符串常量>)`、`ValueError(<字符串常量>)`、`LegacyCheckpointError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService.confirm_review_commit ⭐⭐⭐⭐

**位置与等级**：[service.py:1215](../../../src/workflow/service.py#L1215)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def confirm_review_commit(self, run_id: str, reviewer: str) -> WorkflowState`。

**作用**：处理 `confirm_review_commit` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`reviewer`（str；审核操作者，形成审计归属）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await self.executions.run_wait(run_id, 'confirm', reviewer)`。

**调用与被调用**：
- `self.executions.run_wait`（[service.py:1216](../../../src/workflow/service.py#L1216)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---

# PrismKEService._confirm_review_commit ⭐⭐

**位置与等级**：[service.py:1218](../../../src/workflow/service.py#L1218)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _confirm_review_commit(self, run_id: str, reviewer: str) -> WorkflowState`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`reviewer`（str；审核操作者，形成审计归属）。
- 输出类型：`WorkflowState`；具体返回路径见流程步骤。

**处理流程**：
1. 等待 `self.reviews.recover(run_id)` 完成。
2. 更新 `state`，值来自 `self.show_run(run_id)`。
3. 检查 `not reviewer.strip()`；按条件分流，else 分支不存在。
4. 更新 `retry_commit`，值来自 `state.status == 'failed' and state.failed_node == 'commit_graph'`。
5. 检查 `not (state.review_workspace or state.pending_correction_id) or (state.current_node != 'prepare_graph_com…`；按条件分流，else 分支不存在。
6. 检查 `state.validation.blocking_count or any((task.status == 'pending' for task in state.entity_review_tasks))…`；按条件分流，else 分支不存在。
7. 检查 `state.graph_commit is None or (state.submission_confirmed and (not retry_commit))`；按条件分流，else 分支不存在。
8. 检查 `state.pending_correction_id`；按条件分流，else 分支不存在。
9. 更新 `result`，值来自 `await self.review_workflow(state).confirm_submission(state)`。
10. 调用 `self.audit.record`，结果未直接赋值。
11. 返回 `result`。

**关键条件与保护**：
- [service.py:1221](../../../src/workflow/service.py#L1221)：`not reviewer.strip()`，不满足时跳过本分支。
- [service.py:1224](../../../src/workflow/service.py#L1224)：`not (state.review_workspace or state.pending_correction_id) or (state.current_node != 'prepare_graph_commit' and (…`，不满足时跳过本分支。
- [service.py:1228](../../../src/workflow/service.py#L1228)：`state.validation.blocking_count or any((task.status == 'pending' for task in state.entity_review_tasks)) or any((t…`，不满足时跳过本分支。
- [service.py:1234](../../../src/workflow/service.py#L1234)：`state.graph_commit is None or (state.submission_confirmed and (not retry_commit))`，不满足时跳过本分支。
- [service.py:1236](../../../src/workflow/service.py#L1236)：`state.pending_correction_id`，不满足时跳过本分支。

**调用与被调用**：
- `self.reviews.recover`（[service.py:1219](../../../src/workflow/service.py#L1219)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.show_run`（调用点 [service.py:1220](../../../src/workflow/service.py#L1220)）→ [PrismKEService.show_run](service.md)，静态可定位。
- `reviewer.strip`（[service.py:1221](../../../src/workflow/service.py#L1221)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[service.py:1222](../../../src/workflow/service.py#L1222)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[service.py:1230](../../../src/workflow/service.py#L1230)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.corrections.confirm`（[service.py:1237](../../../src/workflow/service.py#L1237)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.review_workflow(state).confirm_submission`（[service.py:1238](../../../src/workflow/service.py#L1238)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.review_workflow`（调用点 [service.py:1238](../../../src/workflow/service.py#L1238)）→ [PrismKEService.review_workflow](service.md)，静态可定位。
- `self.audit.record`（[service.py:1239](../../../src/workflow/service.py#L1239)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。
- 恢复/幂等性：仅在代码有检查点、事务、请求编号或显式去重时才成立；此函数不能单凭名称视为可安全重试。


---
