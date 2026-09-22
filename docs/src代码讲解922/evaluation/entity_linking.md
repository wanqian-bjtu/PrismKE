源码：[entity_linking.py:1](../../../src/evaluation/entity_linking.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：3

**模块职责**：Reproducible evaluation for v0.4 entity linking and deduplication.
**在系统中的位置**：离线评测、预算账本、标注导出及报告；不等于生产工作流。
**直接依赖**：[src.domain](../domain/__init__.md)、[src.governance.entity_index](../governance/entity_index.md)、[src.governance.entity_resolution](../governance/entity_resolution.md)、[src.persistence.json_graph](../persistence/json_graph.md)、[src.providers.base](../providers/base.md)；外部/标准库：`__future__`、`collections`、`hashlib`、`json`、`pathlib`、`pydantic`、`subprocess`、`tempfile`、`time`、`typing`。
**主要调用方（静态导入）**：[evaluation/__init__.py](__init__.md)、[evaluation/baseline_report.py](baseline_report.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# EntityLinkingEvaluationReport ⭐⭐⭐

**位置与等级**：[entity_linking.py:34](../../../src/evaluation/entity_linking.py#L34)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：输出契约，供后续节点、API 或报告消费。基类：`BaseModel`。

**字段与类级约束**：
- `protocol`：`Literal['fixed', 'sequential']`；默认 `'fixed'`。
- `provenance`：`dict[str, Any]`；默认 `Field(default_factory=dict)`。
- `denominators`：`dict[str, int]`；默认 `Field(default_factory=dict)`。
- `modality_summary`：`dict[str, dict[str, Any]]`；默认 `Field(default_factory=dict)`。
- `auto_link_coverage`：`float`；默认 `0.0`。
- `auto_link_accuracy`：`float`；默认 `0.0`。
- `auto_resolution_coverage`：`float`；默认 `0.0`。
- `created_entities`：`int`；默认 `0`。
- `duplicate_creation_count`：`int`；默认 `0`。
- `cases`：`int`。
- `governance_cases`：`int`。
- `top_10_recall`：`float`。
- `top_1_accuracy`：`float`。
- `nil_precision`：`float`。
- `nil_recall`：`float`。
- `nil_f1`：`float`。
- `b_cubed_precision`：`float`。
- `b_cubed_recall`：`float`。
- `b_cubed_f1`：`float`。
- `review_rate`：`float`。
- `false_auto_link_rate`：`float`。
- `index_build_seconds`：`float`。
- `resolution_seconds`：`float`。
- `total_seconds`：`float`。
- `indexed_entities_per_second`：`float`。
- `mean_resolution_ms`：`float`。
- `details`：`list[dict[str, Any]]`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# _bcubed ⭐⭐

**位置与等级**：[entity_linking.py:64](../../../src/evaluation/entity_linking.py#L64)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _bcubed(actual: list[str], predicted: list[str]) -> tuple[float, float, float]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`actual`（list[str]）；`predicted`（list[str]）。
- 输出类型：`tuple[float, float, float]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `actual_groups`，值来自 `defaultdict(set)`。
2. 更新 `predicted_groups`，值来自 `defaultdict(set)`。
3. 遍历 `enumerate(zip(actual, predicted, strict=True))`，逐项处理 `(index, (actual_id, predicted_id))`。
4. 更新 `precisions`，值来自 `[]`。
5. 更新 `recalls`，值来自 `[]`。
6. 遍历 `enumerate(zip(actual, predicted, strict=True))`，逐项处理 `(index, (actual_id, predicted_id))`。
7. 更新 `precision`，值来自 `sum(precisions) / len(precisions) if precisions else 0.0`。
8. 更新 `recall`，值来自 `sum(recalls) / len(recalls) if recalls else 0.0`。
9. 更新 `f1`，值来自 `2 * precision * recall / (precision + recall) if precision + recall else 0.0`。
10. 返回 `(precision, recall, f1)`。

**调用与被调用**：
- `defaultdict`（[entity_linking.py:65](../../../src/evaluation/entity_linking.py#L65)）：来自 `collections.defaultdict`；具体实现可能由依赖注入或运行时分派决定。
- `enumerate`（[entity_linking.py:67](../../../src/evaluation/entity_linking.py#L67)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `zip`（[entity_linking.py:67](../../../src/evaluation/entity_linking.py#L67)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `actual_groups[actual_id].add`（[entity_linking.py:68](../../../src/evaluation/entity_linking.py#L68)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `predicted_groups[predicted_id].add`（[entity_linking.py:69](../../../src/evaluation/entity_linking.py#L69)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `precisions.append`（[entity_linking.py:75](../../../src/evaluation/entity_linking.py#L75)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[entity_linking.py:75](../../../src/evaluation/entity_linking.py#L75)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `recalls.append`（[entity_linking.py:76](../../../src/evaluation/entity_linking.py#L76)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sum`（[entity_linking.py:77](../../../src/evaluation/entity_linking.py#L77)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[evaluate_entity_linking_manifest](entity_linking.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# evaluate_entity_linking_manifest ⭐⭐

**位置与等级**：[entity_linking.py:83](../../../src/evaluation/entity_linking.py#L83)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def evaluate_entity_linking_manifest(manifest_path: Path, provider: EmbeddingProvider, *, top_k: int=10, auto_link_threshold: float=0.88, review_threshold: float=0.65, min_margin: float=0.08, protocol: Literal['fixed', 'sequential'] | None=None) -> EntityLinkingEvaluationReport`。

**作用**：处理 `evaluate_entity_linking_manifest` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`manifest_path`（Path）；`provider`（EmbeddingProvider）；`top_k`（int；默认 `10`；候选召回数量上限）；`auto_link_threshold`（float；默认 `0.88`）；`review_threshold`（float；默认 `0.65`）；`min_margin`（float；默认 `0.08`）；`protocol`（Literal['fixed', 'sequential'] | None；默认 `None`）。
- 输出类型：`EntityLinkingEvaluationReport`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `total_started`，值来自 `time.perf_counter()`。
2. 更新 `manifest`，值来自 `json.loads(manifest_path.read_text(encoding='utf-8'))`。
3. 更新 `entities`，值来自 `[CanonicalEntity.model_validate(item) for item in manifest['entities']]`。
4. 更新 `selected_protocol`，值来自 `protocol or manifest.get('protocol', 'fixed')`。
5. 检查 `selected_protocol not in {'fixed', 'sequential'}`；按条件分流，else 分支不存在。
6. 更新 `mentions_payload`，值来自 `manifest['mentions']`。
7. 检查 `len({item['id'] for item in mentions_payload}) != len(mentions_payload)`；按条件分流，else 分支不存在。
8. 检查 `len({item.id for item in entities}) != len(entities)`；按条件分流，else 分支不存在。
9. 更新 `types`，值来自 `sorted({item.entity_type for item in entities} | {item['entity_type'] for item in mentions_payload})`。
10. 更新 `schema`，值来自 `SchemaIndex(OutputSchema(schema_id='entity-eval-v0.4', version=str(manifest['version']), strict=Fal…`。
11. 进入上下文 `TemporaryDirectory(prefix='prismke-entity-eval-')`，由上下文管理器控制资源释放或事务范围。
12. 更新 `count`，值来自 `len(details)`。
13. 更新 `nil_precision`，值来自 `correct_nil / predicted_nil if predicted_nil else 0.0`。
14. 更新 `nil_recall`，值来自 `correct_nil / true_nil if true_nil else 0.0`。
15. 更新 `nil_f1`，值来自 `2 * nil_precision * nil_recall / (nil_precision + nil_recall) if nil_precision + nil_recall else 0.0`。
16. 更新 `(bc_precision, bc_recall, bc_f1)`，值来自 `_bcubed(actual_clusters, predicted_clusters)`。
17. 捕获 (OSError, subprocess.CalledProcessError)；另检查 finally/else 的清理和传播。
18. 更新 `modality_summary`，值来自 `{}`。
19. 遍历 `sorted({item['modality'] for item in details})`，逐项处理 `modality`。
20. 返回 `EntityLinkingEvaluationReport(protocol=selected_protocol, provenance={**manifest.get('provenance', {}), …`。

**关键条件与保护**：
- [entity_linking.py:97](../../../src/evaluation/entity_linking.py#L97)：`selected_protocol not in {'fixed', 'sequential'}`，不满足时跳过本分支。
- [entity_linking.py:100](../../../src/evaluation/entity_linking.py#L100)：`len({item['id'] for item in mentions_payload}) != len(mentions_payload)`，不满足时跳过本分支。
- [entity_linking.py:102](../../../src/evaluation/entity_linking.py#L102)：`len({item.id for item in entities}) != len(entities)`，不满足时跳过本分支。
- [entity_linking.py:179](../../../src/evaluation/entity_linking.py#L179)：`any(('unavailable' in reason for reason in decision.reasons))`，不满足时跳过本分支。
- [entity_linking.py:191](../../../src/evaluation/entity_linking.py#L191)：`targets and top_10_correct`，不满足时跳过本分支。
- [entity_linking.py:193](../../../src/evaluation/entity_linking.py#L193)：`top_1_correct`，不满足时跳过本分支。
- [entity_linking.py:244](../../../src/evaluation/entity_linking.py#L244)：`selected_protocol == 'sequential' and (not decision.requires_review)`，不满足时跳过本分支。
- [entity_linking.py:246](../../../src/evaluation/entity_linking.py#L246)：`selected is None`，不满足时跳过本分支。
- [entity_linking.py:249](../../../src/evaluation/entity_linking.py#L249)：`selected not in identities`，不满足时跳过本分支。

**调用与被调用**：
- `time.perf_counter`（[entity_linking.py:93](../../../src/evaluation/entity_linking.py#L93)）：来自 `time`；具体实现可能由依赖注入或运行时分派决定。
- `json.loads`（[entity_linking.py:94](../../../src/evaluation/entity_linking.py#L94)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `manifest_path.read_text`（[entity_linking.py:94](../../../src/evaluation/entity_linking.py#L94)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CanonicalEntity.model_validate`（[entity_linking.py:95](../../../src/evaluation/entity_linking.py#L95)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `manifest.get`（[entity_linking.py:96](../../../src/evaluation/entity_linking.py#L96)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[entity_linking.py:98](../../../src/evaluation/entity_linking.py#L98)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[entity_linking.py:100](../../../src/evaluation/entity_linking.py#L100)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[entity_linking.py:104](../../../src/evaluation/entity_linking.py#L104)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `SchemaIndex`（[entity_linking.py:107](../../../src/evaluation/entity_linking.py#L107)）：来自 `src.domain.SchemaIndex`；具体实现可能由依赖注入或运行时分派决定。
- `OutputSchema`（[entity_linking.py:108](../../../src/evaluation/entity_linking.py#L108)）：来自 `src.domain.OutputSchema`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[entity_linking.py:110](../../../src/evaluation/entity_linking.py#L110)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityTypeDef`（[entity_linking.py:112](../../../src/evaluation/entity_linking.py#L112)）：来自 `src.domain.EntityTypeDef`；具体实现可能由依赖注入或运行时分派决定。
- `TemporaryDirectory`（[entity_linking.py:116](../../../src/evaluation/entity_linking.py#L116)）：来自 `tempfile.TemporaryDirectory`；具体实现可能由依赖注入或运行时分派决定。
- `JSONGraphStore`（调用点 [entity_linking.py:117](../../../src/evaluation/entity_linking.py#L117)）→ [JSONGraphStore](../persistence/json_graph.md)，静态可定位。
- `Path`（[entity_linking.py:117](../../../src/evaluation/entity_linking.py#L117)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `store.commit`（[entity_linking.py:118](../../../src/evaluation/entity_linking.py#L118)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `GraphCommit`（[entity_linking.py:119](../../../src/evaluation/entity_linking.py#L119)）：来自 `src.domain.GraphCommit`；具体实现可能由依赖注入或运行时分派决定。
- `GraphRevision`（[entity_linking.py:121](../../../src/evaluation/entity_linking.py#L121)）：来自 `src.domain.GraphRevision`；具体实现可能由依赖注入或运行时分派决定。
- `rebuild_entity_index`（调用点 [entity_linking.py:129](../../../src/evaluation/entity_linking.py#L129)）→ [rebuild_entity_index](../governance/entity_index.md)，静态可定位。
- `set`（[entity_linking.py:147](../../../src/evaluation/entity_linking.py#L147)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `identities.values`（[entity_linking.py:147](../../../src/evaluation/entity_linking.py#L147)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `payload.get`（[entity_linking.py:152](../../../src/evaluation/entity_linking.py#L152)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `identities.items`（[entity_linking.py:154](../../../src/evaluation/entity_linking.py#L154)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `bool`（[entity_linking.py:158](../../../src/evaluation/entity_linking.py#L158)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EntityMention`（[entity_linking.py:159](../../../src/evaluation/entity_linking.py#L159)）：来自 `src.domain.EntityMention`；具体实现可能由依赖注入或运行时分派决定。
- `SemanticEntityResolver`（调用点 [entity_linking.py:167](../../../src/evaluation/entity_linking.py#L167)）→ [SemanticEntityResolver](../governance/entity_resolution.md)，静态可定位。
- `resolver.resolve`（[entity_linking.py:177](../../../src/evaluation/entity_linking.py#L177)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[entity_linking.py:179](../../../src/evaluation/entity_linking.py#L179)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `RuntimeError`（[entity_linking.py:180](../../../src/evaluation/entity_linking.py#L180)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `int`（[entity_linking.py:197](../../../src/evaluation/entity_linking.py#L197)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 此处列出前 30 个不同调用表达式，另有 17 个，需按源码继续追踪。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`identities[selected]`、`modality_summary[modality]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`、`RuntimeError(f<字符串常量>)`。
- 本地捕获：`(OSError, subprocess.CalledProcessError)`。


---
