源码：[entity_resolution.py:1](../../../src/governance/entity_resolution.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：19

**模块职责**：Deterministic and semantic entity linking with conservative governance.
**在系统中的位置**：实体解析、事实规范化、冲突、风险、审核及实体操作的确定性规则。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)、[src.persistence.base](../persistence/base.md)、[src.providers.base](../providers/base.md)；外部/标准库：`__future__`、`dataclasses`、`difflib`、`math`、`re`。
**主要调用方（静态导入）**：[evaluation/entity_linking.py](../evaluation/entity_linking.md)、[governance/__init__.py](__init__.md)、[governance/entity_index.py](entity_index.md)、[governance/entity_operations.py](entity_operations.md)、[workflow/service.py](../workflow/service.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# _cosine ⭐⭐

**位置与等级**：[entity_resolution.py:27](../../../src/governance/entity_resolution.py#L27)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _cosine(left: list[float], right: list[float]) -> float`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`left`（list[float]）；`right`（list[float]）。
- 输出类型：`float`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `left_norm`，值来自 `math.sqrt(sum((value * value for value in left))) or 1.0`。
2. 更新 `right_norm`，值来自 `math.sqrt(sum((value * value for value in right))) or 1.0`。
3. 返回 `max(-1.0, min(1.0, sum((a * b for a, b in zip(left, right, strict=True))) / (left_norm * right_norm)))`。

**调用与被调用**：
- `math.sqrt`（[entity_resolution.py:28](../../../src/governance/entity_resolution.py#L28)）：来自 `math`；具体实现可能由依赖注入或运行时分派决定。
- `sum`（[entity_resolution.py:28](../../../src/governance/entity_resolution.py#L28)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[entity_resolution.py:30](../../../src/governance/entity_resolution.py#L30)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[entity_resolution.py:32](../../../src/governance/entity_resolution.py#L32)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `zip`（[entity_resolution.py:32](../../../src/governance/entity_resolution.py#L32)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[SemanticEntityResolver._semantic_name_scores](entity_resolution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _cross_script ⭐⭐

**位置与等级**：[entity_resolution.py:36](../../../src/governance/entity_resolution.py#L36)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _cross_script(left: str, right: str) -> bool`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`left`（str）；`right`（str）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `{script(left), script(right)} == {'han', 'latin'}`。

**调用与被调用**：
- `script`（[entity_resolution.py:42](../../../src/governance/entity_resolution.py#L42)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[SemanticEntityResolver._candidate](entity_resolution.md)、[SemanticEntityResolver.resolve](entity_resolution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _cross_script.script ⭐⭐

**位置与等级**：[entity_resolution.py:37](../../../src/governance/entity_resolution.py#L37)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def script(value: str) -> str`。

**作用**：处理 `script` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`value`（str）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `re.search(<字符串常量>, value)`；按条件分流，else 分支不存在。
2. 返回 `'latin' if re.search(<字符串常量>, value) else 'other'`。

**关键条件与保护**：
- [entity_resolution.py:38](../../../src/governance/entity_resolution.py#L38)：`re.search(<字符串常量>, value)`，不满足时跳过本分支。

**调用与被调用**：
- `re.search`（[entity_resolution.py:38](../../../src/governance/entity_resolution.py#L38)）：来自 `re`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ResolutionBundle ⭐⭐⭐⭐

**位置与等级**：[entity_resolution.py:46](../../../src/governance/entity_resolution.py#L46)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。
**约束/装饰器**：`dataclass(frozen=True)`。

**字段与类级约束**：
- `entities`：`list[CanonicalEntity]`。
- `mention_to_entity`：`dict[str, str]`。
- `review_reasons`：`dict[str, list[str]]`。
- `decisions`：`list[EntityResolutionDecision] | None`；默认 `None`。
- `review_tasks`：`list[EntityReviewTask] | None`；默认 `None`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EntityResolver ⭐⭐⭐⭐

**位置与等级**：[entity_resolution.py:54](../../../src/governance/entity_resolution.py#L54)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`EntityResolver.__init__`、`EntityResolver._index`、`EntityResolver.resolve`


---

# EntityResolver.__init__ ⭐⭐⭐⭐

**位置与等级**：[entity_resolution.py:55](../../../src/governance/entity_resolution.py#L55)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def __init__(self, schema: SchemaIndex, existing: list[CanonicalEntity]) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`schema`（SchemaIndex；当前任务的 Schema 或索引，约束实体与关系）；`existing`（list[CanonicalEntity]）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.schema`，值来自 `schema`。
2. 更新 `self.entities`，值来自 `{item.id: item for item in existing}`。
3. 更新 `self.lookup`，值来自 `{}`。
4. 遍历 `existing`，逐项处理 `entity`。
5. 遍历 `schema.schema.entity_catalog`，逐项处理 `item`。

**调用与被调用**：
- `self._index`（调用点 [entity_resolution.py:60](../../../src/governance/entity_resolution.py#L60)）→ [EntityResolver._index](entity_resolution.md)，静态可定位。
- `CanonicalEntity`（[entity_resolution.py:62](../../../src/governance/entity_resolution.py#L62)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `self.entities.setdefault`（[entity_resolution.py:65](../../../src/governance/entity_resolution.py#L65)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.schema`、`self.entities`、`self.lookup`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# EntityResolver._index ⭐⭐

**位置与等级**：[entity_resolution.py:68](../../../src/governance/entity_resolution.py#L68)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _index(self, entity: CanonicalEntity) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`entity`（CanonicalEntity）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 遍历 `[entity.name, *entity.aliases]`，逐项处理 `name`。

**调用与被调用**：
- `normalize_label`（[entity_resolution.py:70](../../../src/governance/entity_resolution.py#L70)）：来自 `src.domain.normalize_label`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[EntityResolver.__init__](entity_resolution.md)、[EntityResolver.resolve](entity_resolution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.lookup[normalize_label(name), entity.entity_type]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# EntityResolver.resolve ⭐⭐⭐⭐

**位置与等级**：[entity_resolution.py:72](../../../src/governance/entity_resolution.py#L72)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def resolve(self, mentions: list[EntityMention]) -> ResolutionBundle`。

**作用**：根据类型、名称、语义候选和上下文形成实体解析结果及审核路由。

**输入与输出**：
- 输入：`mentions`（list[EntityMention]）。
- 输出类型：`ResolutionBundle`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `mapping`，值来自 `{}`。
2. 更新 `review_reasons`，值来自 `{}`。
3. 遍历 `mentions`，逐项处理 `mention`。
4. 返回 `ResolutionBundle(entities=list(self.entities.values()), mention_to_entity=mapping, review_reasons=review…`。

**关键条件与保护**：
- [entity_resolution.py:77](../../../src/governance/entity_resolution.py#L77)：`entity_type is None`，不满足时跳过本分支。
- [entity_resolution.py:78](../../../src/governance/entity_resolution.py#L78)：`self.schema.schema.strict`，不满足时跳过本分支。
- [entity_resolution.py:84](../../../src/governance/entity_resolution.py#L84)：`entity is None`，不满足时跳过本分支。

**调用与被调用**：
- `self.schema.entity_type`（[entity_resolution.py:76](../../../src/governance/entity_resolution.py#L76)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `SchemaValidationError`（调用点 [entity_resolution.py:79](../../../src/governance/entity_resolution.py#L79)）→ [SchemaValidationError](../core/errors.md)，静态可定位。
- `normalize_label`（[entity_resolution.py:82](../../../src/governance/entity_resolution.py#L82)）：来自 `src.domain.normalize_label`；具体实现可能由依赖注入或运行时分派决定。
- `self.lookup.get`（[entity_resolution.py:83](../../../src/governance/entity_resolution.py#L83)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CanonicalEntity`（[entity_resolution.py:85](../../../src/governance/entity_resolution.py#L85)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [entity_resolution.py:86](../../../src/governance/entity_resolution.py#L86)）→ [stable_id](../core/ids.md)，静态可定位。
- `mention.name.strip`（[entity_resolution.py:87](../../../src/governance/entity_resolution.py#L87)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._index`（调用点 [entity_resolution.py:91](../../../src/governance/entity_resolution.py#L91)）→ [EntityResolver._index](entity_resolution.md)，静态可定位。
- `ResolutionBundle`（调用点 [entity_resolution.py:93](../../../src/governance/entity_resolution.py#L93)）→ [ResolutionBundle](entity_resolution.md)，静态可定位。
- `list`（[entity_resolution.py:94](../../../src/governance/entity_resolution.py#L94)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.entities.values`（[entity_resolution.py:94](../../../src/governance/entity_resolution.py#L94)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`review_reasons[mention.id]`、`self.entities[entity.id]`、`mapping[mention.id]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`SchemaValidationError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# entity_embedding_text ⭐⭐

**位置与等级**：[entity_resolution.py:100](../../../src/governance/entity_resolution.py#L100)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def entity_embedding_text(entity: CanonicalEntity) -> str`。

**作用**：处理 `entity_embedding_text` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`entity`（CanonicalEntity）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `attributes`，值来自 `<字符串常量>.join((f<字符串常量> for key, value in sorted(entity.attributes.items())))`。
2. 返回 `<字符串常量>.join((item for item in (f<字符串常量>, f<字符串常量>, <字符串常量> if entity.aliases else '', f<字符串常量>, f<字符串常量…`。

**调用与被调用**：
- `<字符串常量>.join`（[entity_resolution.py:101](../../../src/governance/entity_resolution.py#L101)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[entity_resolution.py:101](../../../src/governance/entity_resolution.py#L101)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `entity.attributes.items`（[entity_resolution.py:101](../../../src/governance/entity_resolution.py#L101)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[rebuild_entity_index](entity_index.md)、[EntityGovernanceService._embedding](entity_operations.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# mention_embedding_text ⭐⭐

**位置与等级**：[entity_resolution.py:115](../../../src/governance/entity_resolution.py#L115)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def mention_embedding_text(mention: EntityMention, entity_type: str) -> str`。

**作用**：处理 `mention_embedding_text` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`mention`（EntityMention）；`entity_type`（str）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `<字符串常量>.join((item for item in (f<字符串常量>, f<字符串常量>, f<字符串常量> if mention.context.strip() else '') if item…`。

**调用与被调用**：
- `<字符串常量>.join`（[entity_resolution.py:116](../../../src/governance/entity_resolution.py#L116)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `mention.name.strip`（[entity_resolution.py:119](../../../src/governance/entity_resolution.py#L119)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `mention.context.strip`（[entity_resolution.py:121](../../../src/governance/entity_resolution.py#L121)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[SemanticEntityResolver.resolve](entity_resolution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# SemanticEntityResolver ⭐⭐⭐⭐

**位置与等级**：[entity_resolution.py:127](../../../src/governance/entity_resolution.py#L127)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。
**源码说明**：Resolve mentions using exact aliases followed by dense semantic retrieval.

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`SemanticEntityResolver.__init__`、`SemanticEntityResolver._name_score`、`SemanticEntityResolver._nil_entity`、`SemanticEntityResolver._candidate`、`SemanticEntityResolver._semantic_name_scores`、`SemanticEntityResolver._context_scores`、`SemanticEntityResolver._apply_neighborhood_score`、`SemanticEntityResolver.resolve`


---

# SemanticEntityResolver.__init__ ⭐⭐⭐⭐

**位置与等级**：[entity_resolution.py:130](../../../src/governance/entity_resolution.py#L130)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def __init__(self, schema: SchemaIndex, graph_store: GraphStore, embedding_provider: EmbeddingProvider, *, run_id: str, top_k: int=10, auto_link_threshold: float=0.88, review_threshold: float=0.65, min_margin: float=0.08) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`schema`（SchemaIndex；当前任务的 Schema 或索引，约束实体与关系）；`graph_store`（GraphStore；图持久化接口，具体实现由配置注入）；`embedding_provider`（EmbeddingProvider）；`run_id`（str；目标运行的稳定标识）；`top_k`（int；默认 `10`；候选召回数量上限）；`auto_link_threshold`（float；默认 `0.88`）；`review_threshold`（float；默认 `0.65`）；`min_margin`（float；默认 `0.08`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.schema`，值来自 `schema`。
2. 更新 `self.graph_store`，值来自 `graph_store`。
3. 更新 `self.embedding_provider`，值来自 `embedding_provider`。
4. 更新 `self.run_id`，值来自 `run_id`。
5. 更新 `self.top_k`，值来自 `top_k`。
6. 更新 `self.auto_link_threshold`，值来自 `auto_link_threshold`。
7. 更新 `self.review_threshold`，值来自 `review_threshold`。
8. 更新 `self.min_margin`，值来自 `min_margin`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.schema`、`self.graph_store`、`self.embedding_provider`、`self.run_id`、`self.top_k`、`self.auto_link_threshold`、`self.review_threshold`、`self.min_margin`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# SemanticEntityResolver._name_score ⭐⭐

**位置与等级**：[entity_resolution.py:152](../../../src/governance/entity_resolution.py#L152)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _name_score(mention: EntityMention, entity: CanonicalEntity) -> float`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`mention`（EntityMention）；`entity`（CanonicalEntity）。
- 输出类型：`float`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `needle`，值来自 `normalize_label(mention.name)`。
2. 更新 `values`，值来自 `[normalize_label(entity.name), *(normalize_label(a) for a in entity.aliases)]`。
3. 返回 `max((SequenceMatcher(None, needle, value).ratio() for value in values))`。

**调用与被调用**：
- `normalize_label`（[entity_resolution.py:153](../../../src/governance/entity_resolution.py#L153)）：来自 `src.domain.normalize_label`；具体实现可能由依赖注入或运行时分派决定。
- `max`（[entity_resolution.py:155](../../../src/governance/entity_resolution.py#L155)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `SequenceMatcher(None, needle, value).ratio`（[entity_resolution.py:155](../../../src/governance/entity_resolution.py#L155)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `SequenceMatcher`（[entity_resolution.py:155](../../../src/governance/entity_resolution.py#L155)）：来自 `difflib.SequenceMatcher`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# SemanticEntityResolver._nil_entity ⭐⭐

**位置与等级**：[entity_resolution.py:158](../../../src/governance/entity_resolution.py#L158)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _nil_entity(mention: EntityMention, entity_type: str) -> CanonicalEntity`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`mention`（EntityMention）；`entity_type`（str）。
- 输出类型：`CanonicalEntity`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `normalized`，值来自 `normalize_label(mention.name)`。
2. 返回 `CanonicalEntity(id=stable_id('entity', entity_type, normalized), name=mention.name.strip(), entity_type=…`。

**调用与被调用**：
- `normalize_label`（[entity_resolution.py:159](../../../src/governance/entity_resolution.py#L159)）：来自 `src.domain.normalize_label`；具体实现可能由依赖注入或运行时分派决定。
- `CanonicalEntity`（[entity_resolution.py:160](../../../src/governance/entity_resolution.py#L160)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `stable_id`（调用点 [entity_resolution.py:161](../../../src/governance/entity_resolution.py#L161)）→ [stable_id](../core/ids.md)，静态可定位。
- `mention.name.strip`（[entity_resolution.py:162](../../../src/governance/entity_resolution.py#L162)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `mention.context.strip`（[entity_resolution.py:164](../../../src/governance/entity_resolution.py#L164)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[entity_resolution.py:165](../../../src/governance/entity_resolution.py#L165)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[entity_resolution.py:165](../../../src/governance/entity_resolution.py#L165)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[SemanticEntityResolver.resolve](entity_resolution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# SemanticEntityResolver._candidate ⭐⭐

**位置与等级**：[entity_resolution.py:169](../../../src/governance/entity_resolution.py#L169)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _candidate(mention: EntityMention, entity: CanonicalEntity, retrieval_score: float, context_score: float | None=None, semantic_name_score: float | None=None) -> EntityCandidate`。

**装饰器/路由**：`staticmethod`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`mention`（EntityMention）；`entity`（CanonicalEntity）；`retrieval_score`（float）；`context_score`（float | None；默认 `None`）；`semantic_name_score`（float | None；默认 `None`）。
- 输出类型：`EntityCandidate`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `retrieval`，值来自 `max(0.0, min(1.0, (retrieval_score + 1.0) / 2.0))`。
2. 更新 `name`，值来自 `SemanticEntityResolver._name_score(mention, entity)`。
3. 更新 `context`，值来自 `retrieval if context_score is None else context_score`。
4. 更新 `neighborhood`，值来自 `0.0`。
5. 更新 `cross_script`，值来自 `any((_cross_script(mention.name, value) for value in [entity.name, *entity.aliases]))`。
6. 更新 `effective_name`，值来自 `name`。
7. 检查 `cross_script and semantic_name_score is not None`；按条件分流，else 分支不存在。
8. 更新 `final`，值来自 `0.4 * retrieval + 0.3 * effective_name + 0.2 * context + 0.1 * neighborhood`。
9. 返回 `EntityCandidate(entity_id=entity.id, retrieval_score=retrieval_score, name_score=name, semantic_name_sco…`。

**关键条件与保护**：
- [entity_resolution.py:184](../../../src/governance/entity_resolution.py#L184)：`cross_script and semantic_name_score is not None`，不满足时跳过本分支。

**调用与被调用**：
- `max`（[entity_resolution.py:176](../../../src/governance/entity_resolution.py#L176)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[entity_resolution.py:176](../../../src/governance/entity_resolution.py#L176)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `SemanticEntityResolver._name_score`（[entity_resolution.py:177](../../../src/governance/entity_resolution.py#L177)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[entity_resolution.py:180](../../../src/governance/entity_resolution.py#L180)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_cross_script`（调用点 [entity_resolution.py:181](../../../src/governance/entity_resolution.py#L181)）→ [_cross_script](entity_resolution.md)，静态可定位。
- `EntityCandidate`（[entity_resolution.py:187](../../../src/governance/entity_resolution.py#L187)）：来自 `src.domain.EntityCandidate`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[SemanticEntityResolver.resolve](entity_resolution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# SemanticEntityResolver._semantic_name_scores ⭐⭐

**位置与等级**：[entity_resolution.py:205](../../../src/governance/entity_resolution.py#L205)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _semantic_name_scores(self, mention: EntityMention, entities: list[CanonicalEntity]) -> dict[str, float]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`mention`（EntityMention）；`entities`（list[CanonicalEntity]）。
- 输出类型：`dict[str, float]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `names`，值来自 `[(entity.id, name) for entity in entities for name in [entity.name, *entity.aliases]]`。
2. 检查 `not names`；按条件分流，else 分支不存在。
3. 更新 `vectors`，值来自 `await self.embedding_provider.encode([mention.name, *(name for _, name in names)])`。
4. 更新 `scores`，值来自 `{}`。
5. 遍历 `zip(names, vectors[1:], strict=True)`，逐项处理 `((entity_id, _), vector)`。
6. 返回 `scores`。

**关键条件与保护**：
- [entity_resolution.py:211](../../../src/governance/entity_resolution.py#L211)：`not names`，不满足时跳过本分支。

**调用与被调用**：
- `self.embedding_provider.encode`（[entity_resolution.py:213](../../../src/governance/entity_resolution.py#L213)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `zip`（[entity_resolution.py:215](../../../src/governance/entity_resolution.py#L215)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[entity_resolution.py:216](../../../src/governance/entity_resolution.py#L216)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `scores.get`（[entity_resolution.py:216](../../../src/governance/entity_resolution.py#L216)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_cosine`（调用点 [entity_resolution.py:216](../../../src/governance/entity_resolution.py#L216)）→ [_cosine](entity_resolution.md)，静态可定位。
- 静态可定位的调用方：[SemanticEntityResolver.resolve](entity_resolution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`scores[entity_id]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# SemanticEntityResolver._context_scores ⭐⭐

**位置与等级**：[entity_resolution.py:219](../../../src/governance/entity_resolution.py#L219)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _context_scores(self, mention: EntityMention, entities: list[CanonicalEntity]) -> dict[str, float]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`mention`（EntityMention）；`entities`（list[CanonicalEntity]）。
- 输出类型：`dict[str, float]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `with_context`，值来自 `[item for item in entities if item.context_summary]`。
2. 检查 `not mention.context.strip() or not with_context`；按条件分流，else 分支不存在。
3. 更新 `vectors`，值来自 `await self.embedding_provider.encode([mention.context, *(item.context_summary or '' for item in wit…`。
4. 更新 `query`，值来自 `vectors[0]`。
5. 更新 `query_norm`，值来自 `math.sqrt(sum((value * value for value in query))) or 1.0`。
6. 更新 `scores`，值来自 `{}`。
7. 遍历 `zip(with_context, vectors[1:], strict=True)`，逐项处理 `(entity, vector)`。
8. 返回 `scores`。

**关键条件与保护**：
- [entity_resolution.py:223](../../../src/governance/entity_resolution.py#L223)：`not mention.context.strip() or not with_context`，不满足时跳过本分支。

**调用与被调用**：
- `mention.context.strip`（[entity_resolution.py:223](../../../src/governance/entity_resolution.py#L223)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.embedding_provider.encode`（[entity_resolution.py:225](../../../src/governance/entity_resolution.py#L225)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `math.sqrt`（[entity_resolution.py:229](../../../src/governance/entity_resolution.py#L229)）：来自 `math`；具体实现可能由依赖注入或运行时分派决定。
- `sum`（[entity_resolution.py:229](../../../src/governance/entity_resolution.py#L229)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `zip`（[entity_resolution.py:231](../../../src/governance/entity_resolution.py#L231)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[entity_resolution.py:236](../../../src/governance/entity_resolution.py#L236)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[entity_resolution.py:236](../../../src/governance/entity_resolution.py#L236)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[SemanticEntityResolver.resolve](entity_resolution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`scores[entity.id]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# SemanticEntityResolver._apply_neighborhood_score ⭐⭐

**位置与等级**：[entity_resolution.py:239](../../../src/governance/entity_resolution.py#L239)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _apply_neighborhood_score(self, mention: EntityMention, candidate: EntityCandidate) -> EntityCandidate`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`mention`（EntityMention）；`candidate`（EntityCandidate；尚未成为正式 Claim 的候选）。
- 输出类型：`EntityCandidate`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 (KeyError, ValueError)；另检查 finally/else 的清理和传播。
2. 更新 `context`，值来自 `normalize_label(mention.context)`。
3. 检查 `not context`；按条件分流，else 分支不存在。
4. 更新 `matched`，值来自 `any((normalize_label(name) in context for entity in neighborhood.entities if entity.id != candidate…`。
5. 检查 `not matched`；按条件分流，else 分支不存在。
6. 返回 `candidate.model_copy(update={'neighborhood_score': 1.0, 'final_score': min(1.0, candidate.final_score + …`。

**关键条件与保护**：
- [entity_resolution.py:247](../../../src/governance/entity_resolution.py#L247)：`not context`，不满足时跳过本分支。
- [entity_resolution.py:256](../../../src/governance/entity_resolution.py#L256)：`not matched`，不满足时跳过本分支。

**调用与被调用**：
- `self.graph_store.get_neighborhood`（[entity_resolution.py:243](../../../src/governance/entity_resolution.py#L243)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `normalize_label`（[entity_resolution.py:246](../../../src/governance/entity_resolution.py#L246)）：来自 `src.domain.normalize_label`；具体实现可能由依赖注入或运行时分派决定。
- `any`（[entity_resolution.py:249](../../../src/governance/entity_resolution.py#L249)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[entity_resolution.py:254](../../../src/governance/entity_resolution.py#L254)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `candidate.model_copy`（[entity_resolution.py:258](../../../src/governance/entity_resolution.py#L258)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[entity_resolution.py:261](../../../src/governance/entity_resolution.py#L261)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[SemanticEntityResolver.resolve](entity_resolution.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`(KeyError, ValueError)`。


---

# SemanticEntityResolver.resolve ⭐⭐⭐⭐

**位置与等级**：[entity_resolution.py:266](../../../src/governance/entity_resolution.py#L266)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def resolve(self, mentions: list[EntityMention]) -> ResolutionBundle`。

**作用**：根据类型、名称、语义候选和上下文形成实体解析结果及审核路由。

**输入与输出**：
- 输入：`mentions`（list[EntityMention]）。
- 输出类型：`ResolutionBundle`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `existing`，值来自 `{item.id: item for item in await self.graph_store.list_entities()}`。
2. 更新 `entities`，值来自 `dict(existing)`。
3. 更新 `exact`，值来自 `{}`。
4. 更新 `names_any_type`，值来自 `{}`。
5. 遍历 `existing.values()`，逐项处理 `entity`。
6. 遍历 `self.schema.schema.entity_catalog`，逐项处理 `item`。
7. 更新 `mapping`，值来自 `{}`。
8. 更新 `review_reasons`，值来自 `{}`。
9. 更新 `decisions`，值来自 `[]`。
10. 更新 `review_tasks`，值来自 `[]`。
11. 更新 `provider_enabled`，值来自 `self.embedding_provider.fingerprint() != 'embedding:disabled'`。
12. 遍历 `mentions`，逐项处理 `mention`。
13. 返回 `ResolutionBundle(entities=list(entities.values()), mention_to_entity=mapping, review_reasons=review_reas…`。

**关键条件与保护**：
- [entity_resolution.py:272](../../../src/governance/entity_resolution.py#L272)：`not entity.active`，不满足时跳过本分支。
- [entity_resolution.py:277](../../../src/governance/entity_resolution.py#L277)：`all((existing.id != entity.id for existing in values))`，不满足时跳过本分支。
- [entity_resolution.py:291](../../../src/governance/entity_resolution.py#L291)：`all((existing.id != entity.id for existing in values))`，不满足时跳过本分支。
- [entity_resolution.py:304](../../../src/governance/entity_resolution.py#L304)：`entity_type is None`，不满足时跳过本分支。
- [entity_resolution.py:305](../../../src/governance/entity_resolution.py#L305)：`self.schema.schema.strict`，不满足时跳过本分支。
- [entity_resolution.py:311](../../../src/governance/entity_resolution.py#L311)：`len(exact_matches) == 1 and provider_enabled and exact_matches[0].context_summary and mention.context.strip()`，不满足时跳过本分支。
- [entity_resolution.py:319](../../../src/governance/entity_resolution.py#L319)：`scores.get(exact_matches[0].id, 1.0) < 0.65`，不满足时跳过本分支。
- [entity_resolution.py:323](../../../src/governance/entity_resolution.py#L323)：`len(exact_matches) == 1 and (not reasons)`，不满足时跳过本分支。
- [entity_resolution.py:347](../../../src/governance/entity_resolution.py#L347)：`provider_enabled and (not cross_type)`，不满足时有 else 分支。
- [entity_resolution.py:360](../../../src/governance/entity_resolution.py#L360)：`previous is None or score > previous[1]`，不满足时跳过本分支。
- [entity_resolution.py:399](../../../src/governance/entity_resolution.py#L399)：`len(exact_matches) > 1`，不满足时跳过本分支。
- [entity_resolution.py:413](../../../src/governance/entity_resolution.py#L413)：`nil_entity.id in existing or exact_matches`，不满足时跳过本分支。
- 另有 10 个条件判断，参见源码；不要将本列表当作全部分支。

**调用与被调用**：
- `self.graph_store.list_entities`（[entity_resolution.py:267](../../../src/governance/entity_resolution.py#L267)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `dict`（[entity_resolution.py:268](../../../src/governance/entity_resolution.py#L268)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `existing.values`（[entity_resolution.py:271](../../../src/governance/entity_resolution.py#L271)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `normalize_label`（[entity_resolution.py:275](../../../src/governance/entity_resolution.py#L275)）：来自 `src.domain.normalize_label`；具体实现可能由依赖注入或运行时分派决定。
- `exact.setdefault`（[entity_resolution.py:276](../../../src/governance/entity_resolution.py#L276)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `all`（[entity_resolution.py:277](../../../src/governance/entity_resolution.py#L277)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `values.append`（[entity_resolution.py:278](../../../src/governance/entity_resolution.py#L278)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `names_any_type.setdefault(normalized, []).append`（[entity_resolution.py:279](../../../src/governance/entity_resolution.py#L279)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `names_any_type.setdefault`（[entity_resolution.py:279](../../../src/governance/entity_resolution.py#L279)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CanonicalEntity`（[entity_resolution.py:281](../../../src/governance/entity_resolution.py#L281)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `entities.setdefault`（[entity_resolution.py:287](../../../src/governance/entity_resolution.py#L287)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.embedding_provider.fingerprint`（[entity_resolution.py:299](../../../src/governance/entity_resolution.py#L299)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.schema.entity_type`（[entity_resolution.py:302](../../../src/governance/entity_resolution.py#L302)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `SchemaValidationError`（调用点 [entity_resolution.py:306](../../../src/governance/entity_resolution.py#L306)）→ [SchemaValidationError](../core/errors.md)，静态可定位。
- `reasons.append`（[entity_resolution.py:308](../../../src/governance/entity_resolution.py#L308)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `exact.get`（[entity_resolution.py:310](../../../src/governance/entity_resolution.py#L310)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[entity_resolution.py:312](../../../src/governance/entity_resolution.py#L312)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `mention.context.strip`（[entity_resolution.py:315](../../../src/governance/entity_resolution.py#L315)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self._context_scores`（调用点 [entity_resolution.py:318](../../../src/governance/entity_resolution.py#L318)）→ [SemanticEntityResolver._context_scores](entity_resolution.md)，静态可定位。
- `scores.get`（[entity_resolution.py:319](../../../src/governance/entity_resolution.py#L319)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `decisions.append`（[entity_resolution.py:325](../../../src/governance/entity_resolution.py#L325)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityResolutionDecision`（[entity_resolution.py:326](../../../src/governance/entity_resolution.py#L326)）：来自 `src.domain.EntityResolutionDecision`；具体实现可能由依赖注入或运行时分派决定。
- `names_any_type.get`（[entity_resolution.py:340](../../../src/governance/entity_resolution.py#L340)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `mention_embedding_text`（调用点 [entity_resolution.py:350](../../../src/governance/entity_resolution.py#L350)）→ [mention_embedding_text](entity_resolution.md)，静态可定位。
- `mention.name.strip`（[entity_resolution.py:351](../../../src/governance/entity_resolution.py#L351)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.embedding_provider.encode`（[entity_resolution.py:353](../../../src/governance/entity_resolution.py#L353)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `self.graph_store.search_entities`（[entity_resolution.py:356](../../../src/governance/entity_resolution.py#L356)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `merged.get`（[entity_resolution.py:359](../../../src/governance/entity_resolution.py#L359)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `list`（[entity_resolution.py:362](../../../src/governance/entity_resolution.py#L362)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `merged.values`（[entity_resolution.py:362](../../../src/governance/entity_resolution.py#L362)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 此处列出前 30 个不同调用表达式，另有 18 个，需按源码继续追踪。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`mapping[mention.id]`、`merged[entity.id]`、`review_reasons[mention.id]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`SchemaValidationError(f<字符串常量>)`。
- 本地捕获：`Exception`。


---
