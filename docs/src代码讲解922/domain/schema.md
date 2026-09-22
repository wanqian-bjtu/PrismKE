源码：[schema.py:1](../../../src/domain/schema.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：14

**模块职责**：Schema contracts and canonical vocabulary lookup.
**在系统中的位置**：文档、知识、Schema、运行、审核、校验、案例等结构化领域契约。
**直接依赖**：[src.core.errors](../core/errors.md)；外部/标准库：`__future__`、`json`、`pathlib`、`pydantic`、`yaml`。
**主要调用方（静态导入）**：[domain/__init__.py](__init__.md)、[domain/cases.py](cases.md)、[domain/validation.py](validation.md)、[domain/workflow.py](workflow.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# normalize_label ⭐⭐⭐⭐

**位置与等级**：[schema.py:14](../../../src/domain/schema.py#L14)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def normalize_label(value: str) -> str`。

**作用**：处理 `normalize_label` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`value`（str）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `<字符串常量>.join(value.casefold().replace('_', <字符串常量>).split())`。

**调用与被调用**：
- `<字符串常量>.join`（[schema.py:15](../../../src/domain/schema.py#L15)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `value.casefold().replace('_', <字符串常量>).split`（[schema.py:15](../../../src/domain/schema.py#L15)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `value.casefold().replace`（[schema.py:15](../../../src/domain/schema.py#L15)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `value.casefold`（[schema.py:15](../../../src/domain/schema.py#L15)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[SchemaIndex.__init__](schema.md)、[SchemaIndex.entity_type](schema.md)、[SchemaIndex.relation](schema.md)、[SchemaIndex.catalog_entity](schema.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# EntityTypeDef ⭐⭐⭐

**位置与等级**：[schema.py:18](../../../src/domain/schema.py#L18)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `aliases`：`list[str]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# RelationDef ⭐⭐⭐

**位置与等级**：[schema.py:23](../../../src/domain/schema.py#L23)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `aliases`：`list[str]`；默认 `Field(default_factory=list)`。
- `domain`：`list[str]`；默认 `Field(default_factory=list)`。
- `range`：`list[str]`；默认 `Field(default_factory=list)`。
- `functional`：`bool`；默认 `False`。
- `min_cardinality`：`int`；默认 `Field(default=0, ge=0)`。
- `max_cardinality`：`int | None`；默认 `Field(default=None, ge=1)`。
- `symmetric`：`bool`；默认 `False`。
- `inverse_relation`：`str | None`；默认 `None`。

**内部成员**：`RelationDef.normalize_cardinality`


---

# RelationDef.normalize_cardinality ⭐⭐⭐⭐

**位置与等级**：[schema.py:35](../../../src/domain/schema.py#L35)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def normalize_cardinality(self) -> RelationDef`。

**装饰器/路由**：`model_validator(mode='after')`。

**作用**：处理 `normalize_cardinality` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`RelationDef`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self.functional`；按条件分流，else 分支不存在。
2. 检查 `self.max_cardinality is not None and self.min_cardinality > self.max_cardinality`；按条件分流，else 分支不存在。
3. 检查 `self.symmetric and self.inverse_relation not in (None, self.id)`；按条件分流，else 分支不存在。
4. 返回 `self`。

**关键条件与保护**：
- [schema.py:36](../../../src/domain/schema.py#L36)：`self.functional`，不满足时跳过本分支。
- [schema.py:37](../../../src/domain/schema.py#L37)：`self.max_cardinality not in (None, 1)`，不满足时跳过本分支。
- [schema.py:40](../../../src/domain/schema.py#L40)：`self.max_cardinality is not None and self.min_cardinality > self.max_cardinality`，不满足时跳过本分支。
- [schema.py:42](../../../src/domain/schema.py#L42)：`self.symmetric and self.inverse_relation not in (None, self.id)`，不满足时跳过本分支。

**调用与被调用**：
- `ValueError`（[schema.py:38](../../../src/domain/schema.py#L38)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `model_validator`（[schema.py:34](../../../src/domain/schema.py#L34)）：来自 `pydantic.model_validator`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.max_cardinality`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# EntityCatalogItem ⭐⭐⭐

**位置与等级**：[schema.py:47](../../../src/domain/schema.py#L47)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `name`：`str`。
- `type`：`str`。
- `aliases`：`list[str]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# OutputSchema ⭐⭐⭐

**位置与等级**：[schema.py:54](../../../src/domain/schema.py#L54)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `schema_id`：`str`。
- `version`：`str`。
- `strict`：`bool`；默认 `True`。
- `entity_types`：`list[EntityTypeDef]`。
- `relations`：`list[RelationDef]`。
- `entity_catalog`：`list[EntityCatalogItem]`；默认 `Field(default_factory=list)`。

**内部成员**：`OutputSchema.validate_references`


---

# OutputSchema.validate_references ⭐⭐⭐⭐

**位置与等级**：[schema.py:63](../../../src/domain/schema.py#L63)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def validate_references(self) -> OutputSchema`。

**装饰器/路由**：`model_validator(mode='after')`。

**作用**：处理 `validate_references` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`OutputSchema`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `type_ids`，值来自 `[item.id for item in self.entity_types]`。
2. 更新 `relation_ids`，值来自 `[item.id for item in self.relations]`。
3. 检查 `len(type_ids) != len(set(type_ids))`；按条件分流，else 分支不存在。
4. 检查 `len(relation_ids) != len(set(relation_ids))`；按条件分流，else 分支不存在。
5. 更新 `known_types`，值来自 `set(type_ids)`。
6. 更新 `known_relations`，值来自 `{item.id: item for item in self.relations}`。
7. 遍历 `self.relations`，逐项处理 `relation`。
8. 遍历 `self.entity_catalog`，逐项处理 `entity`。
9. 返回 `self`。

**关键条件与保护**：
- [schema.py:66](../../../src/domain/schema.py#L66)：`len(type_ids) != len(set(type_ids))`，不满足时跳过本分支。
- [schema.py:68](../../../src/domain/schema.py#L68)：`len(relation_ids) != len(set(relation_ids))`，不满足时跳过本分支。
- [schema.py:74](../../../src/domain/schema.py#L74)：`unknown_types`，不满足时跳过本分支。
- [schema.py:78](../../../src/domain/schema.py#L78)：`relation.inverse_relation is not None`，不满足时跳过本分支。
- [schema.py:80](../../../src/domain/schema.py#L80)：`inverse is None`，不满足时跳过本分支。
- [schema.py:82](../../../src/domain/schema.py#L82)：`inverse.inverse_relation != relation.id`，不满足时跳过本分支。
- [schema.py:87](../../../src/domain/schema.py#L87)：`entity.type not in known_types`，不满足时跳过本分支。

**调用与被调用**：
- `len`（[schema.py:66](../../../src/domain/schema.py#L66)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[schema.py:66](../../../src/domain/schema.py#L66)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[schema.py:67](../../../src/domain/schema.py#L67)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[schema.py:76](../../../src/domain/schema.py#L76)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `known_relations.get`（[schema.py:79](../../../src/domain/schema.py#L79)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `model_validator`（[schema.py:62](../../../src/domain/schema.py#L62)）：来自 `pydantic.model_validator`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`、`ValueError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# load_schema ⭐⭐

**位置与等级**：[schema.py:92](../../../src/domain/schema.py#L92)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def load_schema(path: Path) -> OutputSchema`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`path`（Path）。
- 输出类型：`OutputSchema`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 (OSError, ValueError, ValidationError, yaml.YAMLError)；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `path.read_text`（[schema.py:94](../../../src/domain/schema.py#L94)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.suffix.lower`（[schema.py:95](../../../src/domain/schema.py#L95)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `json.loads`（[schema.py:95](../../../src/domain/schema.py#L95)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `yaml.safe_load`（[schema.py:95](../../../src/domain/schema.py#L95)）：来自 `yaml`；具体实现可能由依赖注入或运行时分派决定。
- `OutputSchema.model_validate`（[schema.py:96](../../../src/domain/schema.py#L96)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `SchemaValidationError`（调用点 [schema.py:98](../../../src/domain/schema.py#L98)）→ [SchemaValidationError](../core/errors.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`SchemaValidationError(f<字符串常量>)`。
- 本地捕获：`(OSError, ValueError, ValidationError, yaml.YAMLError)`。


---

# SchemaIndex ⭐⭐⭐

**位置与等级**：[schema.py:101](../../../src/domain/schema.py#L101)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`SchemaIndex.__init__`、`SchemaIndex.entity_type`、`SchemaIndex.relation`、`SchemaIndex.relation_by_id`、`SchemaIndex.catalog_entity`


---

# SchemaIndex.__init__ ⭐⭐

**位置与等级**：[schema.py:102](../../../src/domain/schema.py#L102)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def __init__(self, schema: OutputSchema) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`schema`（OutputSchema；当前任务的 Schema 或索引，约束实体与关系）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.schema`，值来自 `schema`。
2. 更新 `self._types`，值来自 `{normalize_label(name): item.id for item in schema.entity_types for name in [item.id, *item.aliases…`。
3. 更新 `self._relations`，值来自 `{normalize_label(name): item for item in schema.relations for name in [item.id, *item.aliases]}`。
4. 更新 `self._relations_by_id`，值来自 `{item.id: item for item in schema.relations}`。
5. 更新 `self._entities`，值来自 `{(normalize_label(name), item.type): item for item in schema.entity_catalog for name in [item.name,…`。

**调用与被调用**：
- `normalize_label`（调用点 [schema.py:105](../../../src/domain/schema.py#L105)）→ [normalize_label](schema.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.schema`、`self._types`、`self._relations`、`self._relations_by_id`、`self._entities`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# SchemaIndex.entity_type ⭐⭐

**位置与等级**：[schema.py:121](../../../src/domain/schema.py#L121)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def entity_type(self, value: str) -> str | None`。

**作用**：处理 `entity_type` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`value`（str）。
- 输出类型：`str | None`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self._types.get(normalize_label(value))`。

**调用与被调用**：
- `self._types.get`（[schema.py:122](../../../src/domain/schema.py#L122)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `normalize_label`（调用点 [schema.py:122](../../../src/domain/schema.py#L122)）→ [normalize_label](schema.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# SchemaIndex.relation ⭐⭐

**位置与等级**：[schema.py:124](../../../src/domain/schema.py#L124)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def relation(self, value: str) -> RelationDef | None`。

**作用**：处理 `relation` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`value`（str）。
- 输出类型：`RelationDef | None`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self._relations.get(normalize_label(value))`。

**调用与被调用**：
- `self._relations.get`（[schema.py:125](../../../src/domain/schema.py#L125)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `normalize_label`（调用点 [schema.py:125](../../../src/domain/schema.py#L125)）→ [normalize_label](schema.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# SchemaIndex.relation_by_id ⭐⭐

**位置与等级**：[schema.py:127](../../../src/domain/schema.py#L127)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def relation_by_id(self, relation_id: str) -> RelationDef | None`。

**作用**：处理 `relation_by_id` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`relation_id`（str）。
- 输出类型：`RelationDef | None`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self._relations_by_id.get(relation_id)`。

**调用与被调用**：
- `self._relations_by_id.get`（[schema.py:128](../../../src/domain/schema.py#L128)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# SchemaIndex.catalog_entity ⭐⭐

**位置与等级**：[schema.py:130](../../../src/domain/schema.py#L130)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def catalog_entity(self, name: str, entity_type: str) -> EntityCatalogItem | None`。

**作用**：处理 `catalog_entity` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`name`（str）；`entity_type`（str）。
- 输出类型：`EntityCatalogItem | None`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self._entities.get((normalize_label(name), entity_type))`。

**调用与被调用**：
- `self._entities.get`（[schema.py:131](../../../src/domain/schema.py#L131)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `normalize_label`（调用点 [schema.py:131](../../../src/domain/schema.py#L131)）→ [normalize_label](schema.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
