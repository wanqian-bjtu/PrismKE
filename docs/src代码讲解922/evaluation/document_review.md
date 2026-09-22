源码：[document_review.py:1](../../../src/evaluation/document_review.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：6

**模块职责**：Evidence-aware review tables for partially annotated real documents, not full-text F1.
**在系统中的位置**：离线评测、预算账本、标注导出及报告；不等于生产工作流。
**直接依赖**：[src.domain](../domain/__init__.md)、[src.parsing.visual_assets](../parsing/visual_assets.md)；外部/标准库：`__future__`、`collections`、`csv`、`json`、`math`、`pathlib`、`typing`、`urllib`。
**主要调用方（静态导入）**：未见静态直接导入；可能由包入口、框架注册或动态加载。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# document_coverage ⭐⭐

**位置与等级**：[document_review.py:17](../../../src/evaluation/document_review.py#L17)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def document_coverage(state: dict[str, Any]) -> dict[str, Any]`。

**作用**：Report structural coverage, not extraction accuracy or evidence truth.

**输入与输出**：
- 输入：`state`（dict[str, Any]；跨节点 WorkflowState；调用方须保持证据与状态一致）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `raw`，值来自 `state.get('document')`。
2. 检查 `not raw`；按条件分流，else 分支不存在。
3. 更新 `document`，值来自 `DocumentIR.model_validate(raw)`。
4. 更新 `selected`，值来自 `{asset.id for asset in select_analysis_assets(document)}`。
5. 更新 `called`，值来自 `{call['operation_id'] for call in state.get('provider_calls', []) if call.get('provider') == 'vlm' …`。
6. 更新 `missing`，值来自 `selected - called`。
7. 更新 `invalid`，值来自 `[]`。
8. 更新 `boxes`，值来自 `0`。
9. 遍历 `document.evidence`，逐项处理 `ref`。
10. 更新 `warnings`，值来自 `state.get('warnings', [])`。
11. 更新 `failures`，值来自 `[w for w in warnings if w.startswith(('ocr_failed:', 'vlm_failed:'))]`。
12. 返回 `{'document_available': True, 'source_hash': document.source_hash, 'pages': len(document.pages), 'text_bl…`。

**关键条件与保护**：
- [document_review.py:20](../../../src/evaluation/document_review.py#L20)：`not raw`，不满足时跳过本分支。
- [document_review.py:33](../../../src/evaluation/document_review.py#L33)：`ref.bbox is None`，不满足时跳过本分支。
- [document_review.py:41](../../../src/evaluation/document_review.py#L41)：`not valid or not (0 <= b.x0 <= b.x1 <= (width or 0) and 0 <= b.y0 <= b.y1 <= (height or 0))`，不满足时跳过本分支。

**调用与被调用**：
- `state.get`（[document_review.py:19](../../../src/evaluation/document_review.py#L19)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `DocumentIR.model_validate`（[document_review.py:22](../../../src/evaluation/document_review.py#L22)）：来自 `src.domain.DocumentIR`；具体实现可能由依赖注入或运行时分派决定。
- `select_analysis_assets`（调用点 [document_review.py:23](../../../src/evaluation/document_review.py#L23)）→ [select_analysis_assets](../parsing/visual_assets.md)，静态可定位。
- `call.get`（[document_review.py:27](../../../src/evaluation/document_review.py#L27)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `all`（[document_review.py:40](../../../src/evaluation/document_review.py#L40)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `math.isfinite`（[document_review.py:40](../../../src/evaluation/document_review.py#L40)）：来自 `math`；具体实现可能由依赖注入或运行时分派决定。
- `invalid.append`（[document_review.py:44](../../../src/evaluation/document_review.py#L44)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `w.startswith`（[document_review.py:46](../../../src/evaluation/document_review.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[document_review.py:50](../../../src/evaluation/document_review.py#L50)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `dict`（[document_review.py:51](../../../src/evaluation/document_review.py#L51)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Counter`（[document_review.py:51](../../../src/evaluation/document_review.py#L51)）：来自 `collections.Counter`；具体实现可能由依赖注入或运行时分派决定。
- `sorted`（[document_review.py:55](../../../src/evaluation/document_review.py#L55)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[import_review_run](../workflow/review_workspace.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _normalized ⭐⭐

**位置与等级**：[document_review.py:70](../../../src/evaluation/document_review.py#L70)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _normalized(text: str) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`text`（str）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `<字符串常量>.join(text.split()).casefold()`。

**调用与被调用**：
- `<字符串常量>.join(text.split()).casefold`（[document_review.py:71](../../../src/evaluation/document_review.py#L71)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `<字符串常量>.join`（[document_review.py:71](../../../src/evaluation/document_review.py#L71)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `text.split`（[document_review.py:71](../../../src/evaluation/document_review.py#L71)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[evidence_match](document_review.md)、[review_document_state](document_review.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _joined ⭐⭐

**位置与等级**：[document_review.py:74](../../../src/evaluation/document_review.py#L74)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _joined(mentions: list[dict[str, Any]], key: str) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`mentions`（list[dict[str, Any]]）；`key`（str）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `<字符串常量>.join(sorted({str(item[key]) for item in mentions if item.get(key) is not None}))`。

**调用与被调用**：
- `<字符串常量>.join`（[document_review.py:75](../../../src/evaluation/document_review.py#L75)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[document_review.py:75](../../../src/evaluation/document_review.py#L75)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[document_review.py:75](../../../src/evaluation/document_review.py#L75)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item.get`（[document_review.py:75](../../../src/evaluation/document_review.py#L75)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[export_document_review](document_review.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# evidence_match ⭐⭐

**位置与等级**：[document_review.py:78](../../../src/evaluation/document_review.py#L78)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def evidence_match(gold: dict[str, Any], actual: dict[str, Any], context: str) -> str`。

**作用**：处理 `evidence_match` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`gold`（dict[str, Any]）；`actual`（dict[str, Any]）；`context`（str）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `position`，值来自 `gold.get('evidence') or {}`。
2. 检查 `position.get('coordinate_system') == 'pdf_points'`；按条件分流，else 分支不存在。
3. 更新 `expected_context`，值来自 `_normalized(gold.get('context', ''))`。
4. 检查 `gold.get('modality', 'text') == 'text' and len(expected_context) >= 20 and (expected_context in _normali…`；按条件分流，else 分支不存在。
5. 返回 `'not_verified'`。

**关键条件与保护**：
- [document_review.py:80](../../../src/evaluation/document_review.py#L80)：`position.get('coordinate_system') == 'pdf_points'`，不满足时跳过本分支。
- [document_review.py:81](../../../src/evaluation/document_review.py#L81)：`actual.get('coordinate_space') != 'pdf_points'`，不满足时跳过本分支。
- [document_review.py:83](../../../src/evaluation/document_review.py#L83)：`actual.get('page_number') != position.get('page')`，不满足时跳过本分支。
- [document_review.py:87](../../../src/evaluation/document_review.py#L87)：`expected and bbox`，不满足时跳过本分支。
- [document_review.py:93](../../../src/evaluation/document_review.py#L93)：`gold.get('modality', 'text') == 'text' and len(expected_context) >= 20 and (expected_context in _normalized(contex…`，不满足时跳过本分支。

**调用与被调用**：
- `gold.get`（[document_review.py:79](../../../src/evaluation/document_review.py#L79)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `position.get`（[document_review.py:80](../../../src/evaluation/document_review.py#L80)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `actual.get`（[document_review.py:81](../../../src/evaluation/document_review.py#L81)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `min`（[document_review.py:88](../../../src/evaluation/document_review.py#L88)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `max`（[document_review.py:88](../../../src/evaluation/document_review.py#L88)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_normalized`（调用点 [document_review.py:92](../../../src/evaluation/document_review.py#L92)）→ [_normalized](document_review.md)，静态可定位。
- `len`（[document_review.py:95](../../../src/evaluation/document_review.py#L95)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[review_document_state](document_review.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# review_document_state ⭐⭐⭐⭐

**位置与等级**：[document_review.py:102](../../../src/evaluation/document_review.py#L102)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def review_document_state(state: dict[str, Any], annotations: list[dict[str, Any]]) -> list[dict[str, Any]]`。

**作用**：处理 `review_document_state` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`state`（dict[str, Any]；跨节点 WorkflowState；调用方须保持证据与状态一致）；`annotations`（list[dict[str, Any]]）。
- 输出类型：`list[dict[str, Any]]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `document`，值来自 `state.get('document') or {}`。
2. 更新 `refs`，值来自 `{ref['id']: ref for ref in document.get('evidence', [])}`。
3. 更新 `blocks`，值来自 `{block['evidence_id']: block['text'] for block in document.get('text_blocks', [])}`。
4. 更新 `decisions`，值来自 `{row['mention_id']: row for row in state.get('entity_resolution_decisions', [])}`。
5. 更新 `mentions`，值来自 `{}`。
6. 遍历 `state.get('candidates', [])`，逐项处理 `claim`。
7. 更新 `rows`，值来自 `[]`。
8. 遍历 `annotations`，逐项处理 `gold`。
9. 返回 `rows`。

**关键条件与保护**：
- [document_review.py:113](../../../src/evaluation/document_review.py#L113)：`isinstance(mention, dict) and 'name' in mention`，不满足时跳过本分支。
- [document_review.py:119](../../../src/evaluation/document_review.py#L119)：`_normalized(mention['name']) != _normalized(gold['name'])`，不满足时跳过本分支。

**调用与被调用**：
- `state.get`（[document_review.py:105](../../../src/evaluation/document_review.py#L105)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `document.get`（[document_review.py:106](../../../src/evaluation/document_review.py#L106)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `claim.get`（[document_review.py:112](../../../src/evaluation/document_review.py#L112)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `isinstance`（[document_review.py:113](../../../src/evaluation/document_review.py#L113)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `mentions.values`（[document_review.py:118](../../../src/evaluation/document_review.py#L118)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_normalized`（调用点 [document_review.py:119](../../../src/evaluation/document_review.py#L119)）→ [_normalized](document_review.md)，静态可定位。
- `evidence_match`（调用点 [document_review.py:124](../../../src/evaluation/document_review.py#L124)）→ [evidence_match](document_review.md)，静态可定位。
- `refs.get`（[document_review.py:124](../../../src/evaluation/document_review.py#L124)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `blocks.get`（[document_review.py:124](../../../src/evaluation/document_review.py#L124)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `mention.get`（[document_review.py:126](../../../src/evaluation/document_review.py#L126)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `decisions.get`（[document_review.py:128](../../../src/evaluation/document_review.py#L128)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `observed.append`（[document_review.py:129](../../../src/evaluation/document_review.py#L129)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `decision.get`（[document_review.py:135](../../../src/evaluation/document_review.py#L135)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `rows.append`（[document_review.py:142](../../../src/evaluation/document_review.py#L142)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `gold.get`（[document_review.py:149](../../../src/evaluation/document_review.py#L149)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `bool`（[document_review.py:152](../../../src/evaluation/document_review.py#L152)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[export_document_review](document_review.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`mentions[mention['id']]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# export_document_review ⭐⭐⭐⭐

**位置与等级**：[document_review.py:160](../../../src/evaluation/document_review.py#L160)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def export_document_review(reports: list[Path], annotations_path: Path, output: Path, *, prefer_latest: bool=False) -> list[dict[str, Any]]`。

**作用**：处理 `export_document_review` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`reports`（list[Path]）；`annotations_path`（Path）；`output`（Path）；`prefer_latest`（bool；默认 `False`）。
- 输出类型：`list[dict[str, Any]]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `annotations`，值来自 `json.loads(annotations_path.read_text(encoding='utf-8'))['mentions']`。
2. 检查 `len({row['id'] for row in annotations}) != len(annotations)`；按条件分流，else 分支不存在。
3. 更新 `rows`，值来自 `[]`。
4. 更新 `seen_documents`，值来自 `set()`。
5. 遍历 `reversed(reports) if prefer_latest else reports`，逐项处理 `report_path`。
6. 更新 `missing`，值来自 `[row for row in annotations if row['document_id'] not in seen_documents]`。
7. 调用 `rows.extend`，结果未直接赋值。
8. 调用 `output.mkdir`，结果未直接赋值。
9. 调用 `(output / 'annotated-mention-review.json').write_text`，结果未直接赋值。
10. 进入上下文 `(output / 'annotated-mention-review.csv').open('w', encoding='ut…`，由上下文管理器控制资源释放或事务范围。
11. 返回 `rows`。

**关键条件与保护**：
- [document_review.py:164](../../../src/evaluation/document_review.py#L164)：`len({row['id'] for row in annotations}) != len(annotations)`，不满足时跳过本分支。
- [document_review.py:171](../../../src/evaluation/document_review.py#L171)：`case['id'] in seen_documents`，不满足时跳过本分支。
- [document_review.py:172](../../../src/evaluation/document_review.py#L172)：`prefer_latest`，不满足时跳过本分支。
- [document_review.py:177](../../../src/evaluation/document_review.py#L177)：`'run_id' not in case`，不满足时跳过本分支。

**调用与被调用**：
- `json.loads`（[document_review.py:163](../../../src/evaluation/document_review.py#L163)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `annotations_path.read_text`（[document_review.py:163](../../../src/evaluation/document_review.py#L163)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[document_review.py:164](../../../src/evaluation/document_review.py#L164)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[document_review.py:165](../../../src/evaluation/document_review.py#L165)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[document_review.py:167](../../../src/evaluation/document_review.py#L167)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `reversed`（[document_review.py:168](../../../src/evaluation/document_review.py#L168)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `report_path.read_text`（[document_review.py:169](../../../src/evaluation/document_review.py#L169)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `seen_documents.add`（[document_review.py:175](../../../src/evaluation/document_review.py#L175)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `rows.extend`（[document_review.py:178](../../../src/evaluation/document_review.py#L178)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `review_document_state`（调用点 [document_review.py:178](../../../src/evaluation/document_review.py#L178)）→ [review_document_state](document_review.md)，静态可定位。
- `case.get`（[document_review.py:178](../../../src/evaluation/document_review.py#L178)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `quote`（[document_review.py:180](../../../src/evaluation/document_review.py#L180)）：来自 `urllib.parse.quote`；具体实现可能由依赖注入或运行时分派决定。
- `path.read_text`（[document_review.py:181](../../../src/evaluation/document_review.py#L181)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `output.mkdir`（[document_review.py:185](../../../src/evaluation/document_review.py#L185)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `(output / 'annotated-mention-review.json').write_text`（[document_review.py:186](../../../src/evaluation/document_review.py#L186)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `json.dumps`（[document_review.py:187](../../../src/evaluation/document_review.py#L187)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `(output / 'annotated-mention-review.csv').open`（[document_review.py:189](../../../src/evaluation/document_review.py#L189)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `csv.DictWriter`（[document_review.py:207](../../../src/evaluation/document_review.py#L207)）：来自 `csv`；具体实现可能由依赖注入或运行时分派决定。
- `writer.writeheader`（[document_review.py:208](../../../src/evaluation/document_review.py#L208)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `writer.writerow`（[document_review.py:220](../../../src/evaluation/document_review.py#L220)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `<字符串常量>.join`（[document_review.py:229](../../../src/evaluation/document_review.py#L229)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[document_review.py:229](../../../src/evaluation/document_review.py#L229)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_joined`（调用点 [document_review.py:230](../../../src/evaluation/document_review.py#L230)）→ [_joined](document_review.md)，静态可定位。
- `any`（[document_review.py:232](../../../src/evaluation/document_review.py#L232)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
