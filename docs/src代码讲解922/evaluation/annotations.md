源码：[annotations.py:1](../../../src/evaluation/annotations.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：5

**模块职责**：Read-only conversion of reviewed workbooks into isolated evaluation inputs.
**在系统中的位置**：离线评测、预算账本、标注导出及报告；不等于生产工作流。
**直接依赖**：[src.domain](../domain/__init__.md)；外部/标准库：`PIL`、`__future__`、`bs4`、`hashlib`、`json`、`pathlib`、`re`、`typing`。
**主要调用方（静态导入）**：[cli.py](../cli.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# _read ⭐⭐

**位置与等级**：[annotations.py:17](../../../src/evaluation/annotations.py#L17)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _read(path: Path) -> Any`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`path`（Path）。
- 输出类型：`Any`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `json.loads(path.read_text(encoding='utf-8'))`。

**调用与被调用**：
- `json.loads`（[annotations.py:18](../../../src/evaluation/annotations.py#L18)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- `path.read_text`（[annotations.py:18](../../../src/evaluation/annotations.py#L18)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[export_reviewed_annotations](annotations.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _digest ⭐⭐

**位置与等级**：[annotations.py:21](../../../src/evaluation/annotations.py#L21)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _digest(path: Path) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`path`（Path）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `hashlib.sha256(path.read_bytes()).hexdigest()`。

**调用与被调用**：
- `hashlib.sha256(path.read_bytes()).hexdigest`（[annotations.py:22](../../../src/evaluation/annotations.py#L22)）：来自 `hashlib`；具体实现可能由依赖注入或运行时分派决定。
- `hashlib.sha256`（[annotations.py:22](../../../src/evaluation/annotations.py#L22)）：来自 `hashlib`；具体实现可能由依赖注入或运行时分派决定。
- `path.read_bytes`（[annotations.py:22](../../../src/evaluation/annotations.py#L22)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[export_reviewed_annotations](annotations.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _local ⭐⭐

**位置与等级**：[annotations.py:25](../../../src/evaluation/annotations.py#L25)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _local(root: Path, name: str) -> Path`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`root`（Path）；`name`（str）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `path`，值来自 `(root / name).resolve()`。
2. 检查 `not path.is_relative_to(root.resolve())`；按条件分流，else 分支不存在。
3. 返回 `path`。

**关键条件与保护**：
- [annotations.py:27](../../../src/evaluation/annotations.py#L27)：`not path.is_relative_to(root.resolve())`，不满足时跳过本分支。

**调用与被调用**：
- `(root / name).resolve`（[annotations.py:26](../../../src/evaluation/annotations.py#L26)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.is_relative_to`（[annotations.py:27](../../../src/evaluation/annotations.py#L27)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `root.resolve`（[annotations.py:27](../../../src/evaluation/annotations.py#L27)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[annotations.py:28](../../../src/evaluation/annotations.py#L28)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[export_reviewed_annotations](annotations.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(f<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _verify_original_block ⭐⭐

**位置与等级**：[annotations.py:32](../../../src/evaluation/annotations.py#L32)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _verify_original_block(path: Path, block: dict[str, Any]) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`path`（Path）；`block`（dict[str, Any]）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `path.suffix == '.pdf'`；按条件分流，else 分支存在。

**关键条件与保护**：
- [annotations.py:33](../../../src/evaluation/annotations.py#L33)：`path.suffix == '.pdf'`，不满足时有 else 分支。
- [annotations.py:39](../../../src/evaluation/annotations.py#L39)：`original[4] != block['text'] or list(original[:4]) != block['bbox']`，不满足时跳过本分支。
- [annotations.py:41](../../../src/evaluation/annotations.py#L41)：`path.suffix == '.md'`，不满足时有 else 分支。
- [annotations.py:43](../../../src/evaluation/annotations.py#L43)：`line != block['text']`，不满足时跳过本分支。
- [annotations.py:45](../../../src/evaluation/annotations.py#L45)：`path.suffix == '.html'`，不满足时有 else 分支。
- [annotations.py:49](../../../src/evaluation/annotations.py#L49)：`paragraph.get_text().strip() != block['text']`，不满足时跳过本分支。
- [annotations.py:51](../../../src/evaluation/annotations.py#L51)：`block['text'] not in path.read_text(encoding='utf-8')`，不满足时跳过本分支。

**调用与被调用**：
- `pymupdf.open`（[annotations.py:36](../../../src/evaluation/annotations.py#L36)）：来自 `pymupdf`；具体实现可能由依赖注入或运行时分派决定。
- `int`（[annotations.py:37](../../../src/evaluation/annotations.py#L37)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `block['id'].rsplit`（[annotations.py:37](../../../src/evaluation/annotations.py#L37)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `pdf[block['page'] - 1].get_text`（[annotations.py:38](../../../src/evaluation/annotations.py#L38)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `list`（[annotations.py:39](../../../src/evaluation/annotations.py#L39)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `ValueError`（[annotations.py:40](../../../src/evaluation/annotations.py#L40)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.read_text(encoding='utf-8-sig').splitlines`（[annotations.py:42](../../../src/evaluation/annotations.py#L42)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.read_text`（[annotations.py:42](../../../src/evaluation/annotations.py#L42)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `BeautifulSoup`（[annotations.py:46](../../../src/evaluation/annotations.py#L46)）：来自 `bs4.BeautifulSoup`；具体实现可能由依赖注入或运行时分派决定。
- `path.read_bytes`（[annotations.py:46](../../../src/evaluation/annotations.py#L46)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `tree.select_one`（[annotations.py:47](../../../src/evaluation/annotations.py#L47)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `article.find_all`（[annotations.py:48](../../../src/evaluation/annotations.py#L48)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `paragraph.get_text().strip`（[annotations.py:49](../../../src/evaluation/annotations.py#L49)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `paragraph.get_text`（[annotations.py:49](../../../src/evaluation/annotations.py#L49)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[export_reviewed_annotations](annotations.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# export_reviewed_annotations ⭐⭐⭐⭐

**位置与等级**：[annotations.py:55](../../../src/evaluation/annotations.py#L55)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def export_reviewed_annotations(workbook: Path, package: Path, output: Path) -> dict[str, Any]`。

**作用**：Validate the originals first; never overwrite the workbook or source answers.

**输入与输出**：
- 输入：`workbook`（Path）；`package`（Path）；`output`（Path）。
- 输出类型：`dict[str, Any]`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 ImportError；另检查 finally/else 的清理和传播。
2. 检查 `output.resolve() == package.resolve() or output.resolve() in workbook.resolve().parents`；按条件分流，else 分支不存在。
3. 更新 `answers`，值来自 `_read(package / 'annotations/answer_key.json')`。
4. 更新 `initial`，值来自 `_read(package / 'annotations/initial_kb.json')`。
5. 更新 `sources`，值来自 `_read(package / 'sources.json')`。
6. 更新 `source_paths`，值来自 `{source['document_id']: _local(package, source['original_file']) for source in sources}`。
7. 更新 `catalog`，值来自 `{item['id']: item for item in answers['entities']}`。
8. 更新 `original_mentions`，值来自 `{item['mention_id']: item for item in answers['mentions']}`。
9. 检查 `len(original_mentions) != len(answers['mentions'])`；按条件分流，else 分支不存在。
10. 更新 `entities`，值来自 `[CanonicalEntity.model_validate(item) for item in initial['entities']]`。
11. 检查 `len({entity.id for entity in entities}) != len(entities)`；按条件分流，else 分支不存在。
12. 遍历 `sources`，逐项处理 `source`。
13. 更新 `block_cache`，值来自 `{}`。
14. 更新 `errors`，值来自 `[]`。
15. 更新 `confirmed`，值来自 `[]`。
16. 更新 `excluded`，值来自 `[]`。
17. 更新 `seen`，值来自 `set()`。
18. 更新 `input_digest`，值来自 `_digest(workbook)`。
19. 更新 `book`，值来自 `load_workbook(workbook, read_only=True, data_only=False)`。
20. 捕获 无显式捕获；另检查 finally/else 的清理和传播。
21. 检查 `_digest(workbook) != input_digest`；按条件分流，else 分支不存在。
22. 检查 `errors`；按条件分流，else 分支不存在。
23. 检查 `not confirmed`；按条件分流，else 分支不存在。
24. 更新 `manifest`，值来自 `{'version': 'real-entity-baseline-1', 'protocol': 'fixed', 'entities': initial['entities'], 'mentio…`。
后续还有 7 个语句级步骤，见源码对应行；这里优先保留主要控制流。

**关键条件与保护**：
- [annotations.py:61](../../../src/evaluation/annotations.py#L61)：`output.resolve() == package.resolve() or output.resolve() in workbook.resolve().parents`，不满足时跳过本分支。
- [annotations.py:71](../../../src/evaluation/annotations.py#L71)：`len(original_mentions) != len(answers['mentions'])`，不满足时跳过本分支。
- [annotations.py:74](../../../src/evaluation/annotations.py#L74)：`len({entity.id for entity in entities}) != len(entities)`，不满足时跳过本分支。
- [annotations.py:78](../../../src/evaluation/annotations.py#L78)：`_digest(path) != source['sha256']`，不满足时跳过本分支。
- [annotations.py:82](../../../src/evaluation/annotations.py#L82)：`_digest(path) != asset['sha256']`，不满足时跳过本分支。
- [annotations.py:104](../../../src/evaluation/annotations.py#L104)：`any((name not in headers for name in required))`，不满足时跳过本分支。
- [annotations.py:107](../../../src/evaluation/annotations.py#L107)：`not any((value is not None for value in cells))`，不满足时跳过本分支。
- [annotations.py:112](../../../src/evaluation/annotations.py#L112)：`mention_id in seen or mention_id not in original_mentions`，不满足时跳过本分支。
- [annotations.py:116](../../../src/evaluation/annotations.py#L116)：`row[<字符串常量>] == <字符串常量> or row[<字符串常量>] == <字符串常量>`，不满足时跳过本分支。
- [annotations.py:119](../../../src/evaluation/annotations.py#L119)：`row[<字符串常量>] not in {<字符串常量>, <字符串常量>}`，不满足时跳过本分支。
- [annotations.py:123](../../../src/evaluation/annotations.py#L123)：`surface != re.sub(<字符串常量>, <字符串常量>, original['surface']).strip()`，不满足时跳过本分支。
- [annotations.py:125](../../../src/evaluation/annotations.py#L125)：`row[<字符串常量>] != original['document_id']`，不满足时跳过本分支。
- 另有 17 个条件判断，参见源码；不要将本列表当作全部分支。

**调用与被调用**：
- `ValueError`（[annotations.py:60](../../../src/evaluation/annotations.py#L60)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `output.resolve`（[annotations.py:61](../../../src/evaluation/annotations.py#L61)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `package.resolve`（[annotations.py:61](../../../src/evaluation/annotations.py#L61)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `workbook.resolve`（[annotations.py:61](../../../src/evaluation/annotations.py#L61)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_read`（调用点 [annotations.py:63](../../../src/evaluation/annotations.py#L63)）→ [_read](annotations.md)，静态可定位。
- `_local`（调用点 [annotations.py:67](../../../src/evaluation/annotations.py#L67)）→ [_local](annotations.md)，静态可定位。
- `len`（[annotations.py:71](../../../src/evaluation/annotations.py#L71)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `CanonicalEntity.model_validate`（[annotations.py:73](../../../src/evaluation/annotations.py#L73)）：来自 `src.domain.CanonicalEntity`；具体实现可能由依赖注入或运行时分派决定。
- `_digest`（调用点 [annotations.py:78](../../../src/evaluation/annotations.py#L78)）→ [_digest](annotations.md)，静态可定位。
- `set`（[annotations.py:88](../../../src/evaluation/annotations.py#L88)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `load_workbook`（[annotations.py:90](../../../src/evaluation/annotations.py#L90)）：来自 `openpyxl.load_workbook`；具体实现可能由依赖注入或运行时分派决定。
- `next`（[annotations.py:93](../../../src/evaluation/annotations.py#L93)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sheet.iter_rows`（[annotations.py:93](../../../src/evaluation/annotations.py#L93)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[annotations.py:104](../../../src/evaluation/annotations.py#L104)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `enumerate`（[annotations.py:106](../../../src/evaluation/annotations.py#L106)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `dict`（[annotations.py:109](../../../src/evaluation/annotations.py#L109)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `zip`（[annotations.py:109](../../../src/evaluation/annotations.py#L109)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[annotations.py:110](../../../src/evaluation/annotations.py#L110)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `seen.add`（[annotations.py:114](../../../src/evaluation/annotations.py#L114)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `excluded.append`（[annotations.py:117](../../../src/evaluation/annotations.py#L117)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `re.sub(<字符串常量>, <字符串常量>, str(row[<字符串常量>])).strip`（[annotations.py:122](../../../src/evaluation/annotations.py#L122)）：来自 `re`；具体实现可能由依赖注入或运行时分派决定。
- `re.sub`（[annotations.py:122](../../../src/evaluation/annotations.py#L122)）：来自 `re`；具体实现可能由依赖注入或运行时分派决定。
- `re.sub(<字符串常量>, <字符串常量>, original['surface']).strip`（[annotations.py:123](../../../src/evaluation/annotations.py#L123)）：来自 `re`；具体实现可能由依赖注入或运行时分派决定。
- `_verify_original_block`（调用点 [annotations.py:147](../../../src/evaluation/annotations.py#L147)）→ [_verify_original_block](annotations.md)，静态可定位。
- `Image.open`（[annotations.py:159](../../../src/evaluation/annotations.py#L159)）：来自 `PIL.Image`；具体实现可能由依赖注入或运行时分派决定。
- `confirmed.append`（[annotations.py:167](../../../src/evaluation/annotations.py#L167)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `row.get`（[annotations.py:181](../../../src/evaluation/annotations.py#L181)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `errors.append`（[annotations.py:186](../../../src/evaluation/annotations.py#L186)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `original_mentions.keys`（[annotations.py:187](../../../src/evaluation/annotations.py#L187)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[annotations.py:189](../../../src/evaluation/annotations.py#L189)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 此处列出前 30 个不同调用表达式，另有 10 个，需按源码继续追踪。
- 静态可定位的调用方：[export_entity_annotations](../cli.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：`block_cache[doc]`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`、`ValueError(f<字符串常量>document_id<字符串常量>)`、`ValueError(f<字符串常量>document_id<字符串常量>file<字符串常量>)`、`ValueError(f<字符串常量>)`、`ValueError(<字符串常量>.join(errors))`。
- 本地捕获：`ImportError`、`(ValueError, KeyError, TypeError)`。


---
