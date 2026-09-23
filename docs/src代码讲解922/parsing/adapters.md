源码：[adapters.py:1](../../../src/parsing/adapters.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：31

**模块职责**：Built-in document parsers with multimodal asset provenance.
**在系统中的位置**：输入文档适配、格式注册与视觉资产提取，向后续抽取提供 DocumentIR。
**直接依赖**：[src.core.ids](../core/ids.md)、[src.domain](../domain/__init__.md)；外部/标准库：`PIL`、`__future__`、`base64`、`bs4`、`docx`、`hashlib`、`httpx`、`mimetypes`、`pathlib`、`pymupdf`、`re`、`urllib`。
**主要调用方（静态导入）**：[parsing/registry.py](registry.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# detect_media_type ⭐⭐⭐

**位置与等级**：[adapters.py:43](../../../src/parsing/adapters.py#L43)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def detect_media_type(path: Path, explicit: str | None=None) -> str`。

**作用**：处理 `detect_media_type` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`path`（Path）；`explicit`（str | None；默认 `None`）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `explicit`；按条件分流，else 分支不存在。
2. 更新 `suffix_map`，值来自 `{'.md': 'text/markdown', '.markdown': 'text/markdown', '.pdf': 'application/pdf', '.html': 'text/ht…`。
3. 返回 `suffix_map.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or ''`。

**关键条件与保护**：
- [adapters.py:44](../../../src/parsing/adapters.py#L44)：`explicit`，不满足时跳过本分支。

**调用与被调用**：
- `suffix_map.get`（[adapters.py:54](../../../src/parsing/adapters.py#L54)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.suffix.lower`（[adapters.py:54](../../../src/parsing/adapters.py#L54)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `mimetypes.guess_type`（[adapters.py:54](../../../src/parsing/adapters.py#L54)）：来自 `mimetypes`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[_resolve_image](adapters.md)、[TextParser.parse](adapters.md)、[ImageParser.parse](adapters.md)、[ParserRegistry.parse](registry.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# AssetWriter ⭐⭐⭐

**位置与等级**：[adapters.py:57](../../../src/parsing/adapters.py#L57)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`AssetWriter.__init__`、`AssetWriter.write`


---

# AssetWriter.__init__ ⭐⭐⭐

**位置与等级**：[adapters.py:58](../../../src/parsing/adapters.py#L58)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def __init__(self, directory: Path | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`directory`（Path | None；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.directory`，值来自 `directory or Path('runtime/assets')`。
2. 调用 `self.directory.mkdir`，结果未直接赋值。

**调用与被调用**：
- `Path`（[adapters.py:59](../../../src/parsing/adapters.py#L59)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `self.directory.mkdir`（[adapters.py:60](../../../src/parsing/adapters.py#L60)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.directory`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# AssetWriter.write ⭐⭐⭐

**位置与等级**：[adapters.py:62](../../../src/parsing/adapters.py#L62)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def write(self, content: bytes, suffix: str) -> tuple[Path, str]`。

**作用**：处理 `write` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`content`（bytes）；`suffix`（str）。
- 输出类型：`tuple[Path, str]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `digest`，值来自 `sha256(content).hexdigest()`。
2. 更新 `path`，值来自 `self.directory / digest[:2] / f<字符串常量>`。
3. 调用 `path.parent.mkdir`，结果未直接赋值。
4. 检查 `not path.exists()`；按条件分流，else 分支不存在。
5. 返回 `(path.resolve(), digest)`。

**关键条件与保护**：
- [adapters.py:66](../../../src/parsing/adapters.py#L66)：`not path.exists()`，不满足时跳过本分支。

**调用与被调用**：
- `sha256(content).hexdigest`（[adapters.py:63](../../../src/parsing/adapters.py#L63)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sha256`（[adapters.py:63](../../../src/parsing/adapters.py#L63)）：来自 `hashlib.sha256`；具体实现可能由依赖注入或运行时分派决定。
- `path.parent.mkdir`（[adapters.py:65](../../../src/parsing/adapters.py#L65)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.exists`（[adapters.py:66](../../../src/parsing/adapters.py#L66)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.write_bytes`（[adapters.py:67](../../../src/parsing/adapters.py#L67)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.resolve`（[adapters.py:68](../../../src/parsing/adapters.py#L68)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _text_block ⭐⭐

**位置与等级**：[adapters.py:71](../../../src/parsing/adapters.py#L71)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _text_block(document_id: str, source_hash: str, text: str, ordinal: int, *, page_number: int | None=None, bbox: BBox | None=None, char_start: int | None=None, char_end: int | None=None) -> tuple[TextBlock, EvidenceRef]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`document_id`（str）；`source_hash`（str）；`text`（str）；`ordinal`（int）；`page_number`（int | None；默认 `None`）；`bbox`（BBox | None；默认 `None`）；`char_start`（int | None；默认 `None`）；`char_end`（int | None；默认 `None`）。
- 输出类型：`tuple[TextBlock, EvidenceRef]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `evidence_id`，值来自 `stable_id('ev', document_id, 'text', page_number, ordinal, text)`。
2. 更新 `block`，值来自 `TextBlock(id=stable_id('block', document_id, page_number, ordinal, text), text=text, page_number=pa…`。
3. 更新 `evidence`，值来自 `EvidenceRef(id=evidence_id, kind=EvidenceKind.PDF_BBOX if bbox else EvidenceKind.TEXT_SPAN, documen…`。
4. 返回 `(block, evidence)`。

**调用与被调用**：
- `stable_id`（调用点 [adapters.py:82](../../../src/parsing/adapters.py#L82)）→ [stable_id](../core/ids.md)，静态可定位。
- `TextBlock`（[adapters.py:83](../../../src/parsing/adapters.py#L83)）：来自 `src.domain.TextBlock`；具体实现可能由依赖注入或运行时分派决定。
- `EvidenceRef`（[adapters.py:92](../../../src/parsing/adapters.py#L92)）：来自 `src.domain.EvidenceRef`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[TextParser.parse](adapters.md)、[MarkdownParser.parse](adapters.md)、[HTMLParser.parse](adapters.md)、[DOCXParser.parse](adapters.md)、[PDFParser.parse](adapters.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _asset ⭐⭐

**位置与等级**：[adapters.py:108](../../../src/parsing/adapters.py#L108)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _asset(writer: AssetWriter, document_id: str, content: bytes, media_type: str, origin: str, source_ref: str, context: str='', page_number: int | None=None, requires_ocr: bool=False) -> tuple[MediaAsset | None, EvidenceRef | None, str | None]`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`writer`（AssetWriter）；`document_id`（str）；`content`（bytes）；`media_type`（str）；`origin`（str）；`source_ref`（str）；`context`（str；默认 `''`）；`page_number`（int | None；默认 `None`）；`requires_ocr`（bool；默认 `False`）。
- 输出类型：`tuple[MediaAsset | None, EvidenceRef | None, str | None]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `suffix`，值来自 `mimetypes.guess_extension(media_type) or '.bin'`。
2. 更新 `(path, digest)`，值来自 `writer.write(content, suffix)`。
3. 捕获 (OSError, ValueError)；另检查 finally/else 的清理和传播。
4. 检查 `min(width, height) < MIN_ASSET_EDGE`；按条件分流，else 分支不存在。
5. 更新 `asset_id`，值来自 `stable_id('media', document_id, origin, source_ref, digest)`。
6. 更新 `evidence_id`，值来自 `stable_id('ev', document_id, asset_id, 'asset')`。
7. 更新 `asset`，值来自 `MediaAsset(id=asset_id, path=str(path), media_type=media_type, width=width, height=height, page_num…`。
8. 更新 `evidence`，值来自 `EvidenceRef(id=evidence_id, kind=EvidenceKind.IMAGE, document_id=document_id, source_hash=digest, m…`。
9. 返回 `(asset, evidence, None)`。

**关键条件与保护**：
- [adapters.py:126](../../../src/parsing/adapters.py#L126)：`min(width, height) < MIN_ASSET_EDGE`，不满足时跳过本分支。

**调用与被调用**：
- `mimetypes.guess_extension`（[adapters.py:119](../../../src/parsing/adapters.py#L119)）：来自 `mimetypes`；具体实现可能由依赖注入或运行时分派决定。
- `writer.write`（[adapters.py:120](../../../src/parsing/adapters.py#L120)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Image.open`（[adapters.py:122](../../../src/parsing/adapters.py#L122)）：来自 `PIL.Image`；具体实现可能由依赖注入或运行时分派决定。
- `min`（[adapters.py:126](../../../src/parsing/adapters.py#L126)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `stable_id`（调用点 [adapters.py:128](../../../src/parsing/adapters.py#L128)）→ [stable_id](../core/ids.md)，静态可定位。
- `MediaAsset`（[adapters.py:130](../../../src/parsing/adapters.py#L130)）：来自 `src.domain.MediaAsset`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[adapters.py:132](../../../src/parsing/adapters.py#L132)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `EvidenceRef`（[adapters.py:144](../../../src/parsing/adapters.py#L144)）：来自 `src.domain.EvidenceRef`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[MarkdownParser.parse](adapters.md)、[HTMLParser.parse](adapters.md)、[DOCXParser.parse](adapters.md)、[PDFParser.parse](adapters.md)、[ImageParser.parse](adapters.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`(OSError, ValueError)`。


---

# _resolve_image ⭐⭐

**位置与等级**：[adapters.py:160](../../../src/parsing/adapters.py#L160)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _resolve_image(source: str, base: Path, allow_remote: bool=False) -> tuple[bytes, str, str] | None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`source`（str）；`base`（Path）；`allow_remote`（bool；默认 `False`）。
- 输出类型：`tuple[bytes, str, str] | None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `source.startswith('data:')`；按条件分流，else 分支不存在。
2. 更新 `parsed`，值来自 `urlparse(source)`。
3. 检查 `parsed.scheme in {'http', 'https'}`；按条件分流，else 分支不存在。
4. 更新 `candidate`，值来自 `(base / unquote(parsed.path)).resolve()`。
5. 捕获 ValueError；另检查 finally/else 的清理和传播。
6. 检查 `not candidate.is_file()`；按条件分流，else 分支不存在。
7. 返回 `(candidate.read_bytes(), detect_media_type(candidate), str(candidate))`。

**关键条件与保护**：
- [adapters.py:163](../../../src/parsing/adapters.py#L163)：`source.startswith('data:')`，不满足时跳过本分支。
- [adapters.py:168](../../../src/parsing/adapters.py#L168)：`parsed.scheme in {'http', 'https'}`，不满足时跳过本分支。
- [adapters.py:169](../../../src/parsing/adapters.py#L169)：`not allow_remote`，不满足时跳过本分支。
- [adapters.py:181](../../../src/parsing/adapters.py#L181)：`not candidate.is_file()`，不满足时跳过本分支。

**调用与被调用**：
- `source.startswith`（[adapters.py:163](../../../src/parsing/adapters.py#L163)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `source.split`（[adapters.py:164](../../../src/parsing/adapters.py#L164)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `header[5:].split`（[adapters.py:165](../../../src/parsing/adapters.py#L165)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `base64.b64decode`（[adapters.py:166](../../../src/parsing/adapters.py#L166)）：来自 `base64`；具体实现可能由依赖注入或运行时分派决定。
- `urlparse`（[adapters.py:167](../../../src/parsing/adapters.py#L167)）：来自 `urllib.parse.urlparse`；具体实现可能由依赖注入或运行时分派决定。
- `httpx.AsyncClient`（[adapters.py:171](../../../src/parsing/adapters.py#L171)）：来自 `httpx`；具体实现可能由依赖注入或运行时分派决定。
- `client.get`（[adapters.py:172](../../../src/parsing/adapters.py#L172)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `response.raise_for_status`（[adapters.py:173](../../../src/parsing/adapters.py#L173)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `response.headers.get('content-type', 'image/png').split`（[adapters.py:174](../../../src/parsing/adapters.py#L174)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `response.headers.get`（[adapters.py:174](../../../src/parsing/adapters.py#L174)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `(base / unquote(parsed.path)).resolve`（[adapters.py:176](../../../src/parsing/adapters.py#L176)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `unquote`（[adapters.py:176](../../../src/parsing/adapters.py#L176)）：来自 `urllib.parse.unquote`；具体实现可能由依赖注入或运行时分派决定。
- `candidate.relative_to`（[adapters.py:178](../../../src/parsing/adapters.py#L178)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `base.resolve`（[adapters.py:178](../../../src/parsing/adapters.py#L178)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `candidate.is_file`（[adapters.py:181](../../../src/parsing/adapters.py#L181)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `candidate.read_bytes`（[adapters.py:183](../../../src/parsing/adapters.py#L183)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `detect_media_type`（调用点 [adapters.py:183](../../../src/parsing/adapters.py#L183)）→ [detect_media_type](adapters.md)，静态可定位。
- `str`（[adapters.py:183](../../../src/parsing/adapters.py#L183)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[MarkdownParser.parse](adapters.md)、[HTMLParser.parse](adapters.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`ValueError`。


---

# _html_image_context ⭐⭐

**位置与等级**：[adapters.py:186](../../../src/parsing/adapters.py#L186)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _html_image_context(image: Tag) -> str`。

**作用**：Keep image context local and label it as auxiliary evidence.

**输入与输出**：
- 输入：`image`（Tag）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `parts`，值来自 `[]`。
2. 遍历 `('alt', 'title')`，逐项处理 `attribute`。
3. 更新 `figure`，值来自 `image.find_parent('figure')`。
4. 检查 `isinstance(figure, Tag)`；按条件分流，else 分支不存在。
5. 更新 `container`，值来自 `figure if isinstance(figure, Tag) else image`。
6. 遍历 `(container.find_previous_sibling(), container.find_next_sibling())`，逐项处理 `sibling`。
7. 更新 `unique`，值来自 `[]`。
8. 更新 `seen`，值来自 `set()`。
9. 遍历 `parts`，逐项处理 `(label, value)`。
10. 返回 `<字符串常量>.join(unique)[:MAX_HTML_CONTEXT_CHARS]`。

**关键条件与保护**：
- [adapters.py:192](../../../src/parsing/adapters.py#L192)：`value`，不满足时跳过本分支。
- [adapters.py:196](../../../src/parsing/adapters.py#L196)：`isinstance(figure, Tag)`，不满足时跳过本分支。
- [adapters.py:198](../../../src/parsing/adapters.py#L198)：`isinstance(caption, Tag)`，不满足时跳过本分支。
- [adapters.py:200](../../../src/parsing/adapters.py#L200)：`text`，不满足时跳过本分支。
- [adapters.py:205](../../../src/parsing/adapters.py#L205)：`not isinstance(sibling, Tag) or sibling.name not in {'p', 'li', 'h1', 'h2', 'h3', 'figcaption'}`，不满足时跳过本分支。
- [adapters.py:215](../../../src/parsing/adapters.py#L215)：`text`，不满足时跳过本分支。
- [adapters.py:222](../../../src/parsing/adapters.py#L222)：`normalized in seen`，不满足时跳过本分支。

**调用与被调用**：
- `<字符串常量>.join`（[adapters.py:191](../../../src/parsing/adapters.py#L191)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str(image.get(attribute, '')).split`（[adapters.py:191](../../../src/parsing/adapters.py#L191)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[adapters.py:191](../../../src/parsing/adapters.py#L191)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `image.get`（[adapters.py:191](../../../src/parsing/adapters.py#L191)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `parts.append`（[adapters.py:193](../../../src/parsing/adapters.py#L193)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `image.find_parent`（[adapters.py:195](../../../src/parsing/adapters.py#L195)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `isinstance`（[adapters.py:196](../../../src/parsing/adapters.py#L196)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `figure.find`（[adapters.py:197](../../../src/parsing/adapters.py#L197)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `caption.get_text(<字符串常量>, strip=True).split`（[adapters.py:199](../../../src/parsing/adapters.py#L199)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `caption.get_text`（[adapters.py:199](../../../src/parsing/adapters.py#L199)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `container.find_previous_sibling`（[adapters.py:204](../../../src/parsing/adapters.py#L204)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `container.find_next_sibling`（[adapters.py:204](../../../src/parsing/adapters.py#L204)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sibling.get_text(<字符串常量>, strip=True).split`（[adapters.py:214](../../../src/parsing/adapters.py#L214)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sibling.get_text`（[adapters.py:214](../../../src/parsing/adapters.py#L214)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[adapters.py:219](../../../src/parsing/adapters.py#L219)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `value.casefold`（[adapters.py:221](../../../src/parsing/adapters.py#L221)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `seen.add`（[adapters.py:224](../../../src/parsing/adapters.py#L224)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `unique.append`（[adapters.py:225](../../../src/parsing/adapters.py#L225)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[MarkdownParser.parse](adapters.md)、[HTMLParser.parse](adapters.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# TextParser ⭐⭐⭐

**位置与等级**：[adapters.py:229](../../../src/parsing/adapters.py#L229)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`TextParser.supports`、`TextParser.parse`


---

# TextParser.supports ⭐⭐⭐

**位置与等级**：[adapters.py:230](../../../src/parsing/adapters.py#L230)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def supports(self, media_type: str) -> bool`。

**作用**：处理 `supports` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`media_type`（str）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `media_type in TEXT_TYPES`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# TextParser.parse ⭐⭐⭐

**位置与等级**：[adapters.py:233](../../../src/parsing/adapters.py#L233)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def parse(self, source: SourceDocument) -> DocumentIR`。

**作用**：处理 `parse` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`source`（SourceDocument）。
- 输出类型：`DocumentIR`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `path`，值来自 `source.path.resolve()`。
2. 更新 `(content, source_hash)`，值来自 `(path.read_text(encoding='utf-8'), file_sha256(path))`。
3. 更新 `document_id`，值来自 `stable_id('doc', source_hash)`。
4. 更新 `blocks`，值来自 `[]`。
5. 更新 `evidence`，值来自 `[]`。
6. 更新 `cursor`，值来自 `0`。
7. 遍历 `enumerate(content.splitlines(keepends=True))`，逐项处理 `(ordinal, raw_line)`。
8. 返回 `DocumentIR(id=document_id, source_path=str(path), source_hash=source_hash, media_type=detect_media_type(…`。

**关键条件与保护**：
- [adapters.py:242](../../../src/parsing/adapters.py#L242)：`paragraph.strip()`，不满足时跳过本分支。

**调用与被调用**：
- `source.path.resolve`（[adapters.py:234](../../../src/parsing/adapters.py#L234)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.read_text`（[adapters.py:235](../../../src/parsing/adapters.py#L235)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `file_sha256`（调用点 [adapters.py:235](../../../src/parsing/adapters.py#L235)）→ [file_sha256](../core/ids.md)，静态可定位。
- `stable_id`（调用点 [adapters.py:236](../../../src/parsing/adapters.py#L236)）→ [stable_id](../core/ids.md)，静态可定位。
- `enumerate`（[adapters.py:240](../../../src/parsing/adapters.py#L240)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `content.splitlines`（[adapters.py:240](../../../src/parsing/adapters.py#L240)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `raw_line.rstrip`（[adapters.py:241](../../../src/parsing/adapters.py#L241)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `paragraph.strip`（[adapters.py:242](../../../src/parsing/adapters.py#L242)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_text_block`（调用点 [adapters.py:243](../../../src/parsing/adapters.py#L243)）→ [_text_block](adapters.md)，静态可定位。
- `len`（[adapters.py:249](../../../src/parsing/adapters.py#L249)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `blocks.append`（[adapters.py:251](../../../src/parsing/adapters.py#L251)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence.append`（[adapters.py:252](../../../src/parsing/adapters.py#L252)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `DocumentIR`（[adapters.py:254](../../../src/parsing/adapters.py#L254)）：来自 `src.domain.DocumentIR`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[adapters.py:256](../../../src/parsing/adapters.py#L256)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `detect_media_type`（调用点 [adapters.py:258](../../../src/parsing/adapters.py#L258)）→ [detect_media_type](adapters.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MarkdownParser ⭐⭐⭐

**位置与等级**：[adapters.py:264](../../../src/parsing/adapters.py#L264)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`MarkdownParser.__init__`、`MarkdownParser.supports`、`MarkdownParser.parse`


---

# MarkdownParser.__init__ ⭐⭐⭐

**位置与等级**：[adapters.py:265](../../../src/parsing/adapters.py#L265)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def __init__(self, asset_dir: Path | None=None, allow_remote: bool=False) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`asset_dir`（Path | None；默认 `None`）；`allow_remote`（bool；默认 `False`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.writer`，值来自 `AssetWriter(asset_dir)`。
2. 更新 `self.allow_remote`，值来自 `allow_remote`。

**调用与被调用**：
- `AssetWriter`（调用点 [adapters.py:266](../../../src/parsing/adapters.py#L266)）→ [AssetWriter](adapters.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.writer`、`self.allow_remote`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MarkdownParser.supports ⭐⭐⭐

**位置与等级**：[adapters.py:269](../../../src/parsing/adapters.py#L269)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def supports(self, media_type: str) -> bool`。

**作用**：处理 `supports` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`media_type`（str）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `media_type in MARKDOWN_TYPES`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# MarkdownParser.parse ⭐⭐⭐

**位置与等级**：[adapters.py:272](../../../src/parsing/adapters.py#L272)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def parse(self, source: SourceDocument) -> DocumentIR`。

**作用**：处理 `parse` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`source`（SourceDocument）。
- 输出类型：`DocumentIR`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `path`，值来自 `source.path.resolve()`。
2. 更新 `(content, source_hash)`，值来自 `(path.read_text(encoding='utf-8'), file_sha256(path))`。
3. 更新 `document_id`，值来自 `stable_id('doc', source_hash)`。
4. 更新 `blocks`，值来自 `[]`。
5. 更新 `assets`，值来自 `[]`。
6. 更新 `evidence`，值来自 `[]`。
7. 更新 `warnings`，值来自 `[]`。
8. 更新 `cursor`，值来自 `0`。
9. 遍历 `enumerate(content.splitlines(keepends=True))`，逐项处理 `(ordinal, raw_line)`。
10. 遍历 `enumerate(BeautifulSoup(content, 'html.parser').find_all('img'))`，逐项处理 `(ordinal, image)`。
11. 返回 `DocumentIR(id=document_id, source_path=str(path), source_hash=source_hash, media_type='text/markdown', t…`。

**关键条件与保护**：
- [adapters.py:284](../../../src/parsing/adapters.py#L284)：`clean`，不满足时跳过本分支。
- [adapters.py:299](../../../src/parsing/adapters.py#L299)：`resolved is None`，不满足时跳过本分支。
- [adapters.py:317](../../../src/parsing/adapters.py#L317)：`warning`，不满足时跳过本分支。
- [adapters.py:319](../../../src/parsing/adapters.py#L319)：`asset and asset_ref`，不满足时跳过本分支。
- [adapters.py:326](../../../src/parsing/adapters.py#L326)：`resolved is None`，不满足时跳过本分支。
- [adapters.py:344](../../../src/parsing/adapters.py#L344)：`warning`，不满足时跳过本分支。
- [adapters.py:346](../../../src/parsing/adapters.py#L346)：`asset and asset_ref`，不满足时跳过本分支。

**调用与被调用**：
- `source.path.resolve`（[adapters.py:273](../../../src/parsing/adapters.py#L273)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `path.read_text`（[adapters.py:274](../../../src/parsing/adapters.py#L274)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `file_sha256`（调用点 [adapters.py:274](../../../src/parsing/adapters.py#L274)）→ [file_sha256](../core/ids.md)，静态可定位。
- `stable_id`（调用点 [adapters.py:275](../../../src/parsing/adapters.py#L275)）→ [stable_id](../core/ids.md)，静态可定位。
- `enumerate`（[adapters.py:281](../../../src/parsing/adapters.py#L281)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `content.splitlines`（[adapters.py:281](../../../src/parsing/adapters.py#L281)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `raw_line.rstrip`（[adapters.py:282](../../../src/parsing/adapters.py#L282)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `MARKDOWN_IMAGE.sub('', line).strip`（[adapters.py:283](../../../src/parsing/adapters.py#L283)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `MARKDOWN_IMAGE.sub`（[adapters.py:283](../../../src/parsing/adapters.py#L283)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `line.find`（[adapters.py:285](../../../src/parsing/adapters.py#L285)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_text_block`（调用点 [adapters.py:286](../../../src/parsing/adapters.py#L286)）→ [_text_block](adapters.md)，静态可定位。
- `len`（[adapters.py:292](../../../src/parsing/adapters.py#L292)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `blocks.append`（[adapters.py:294](../../../src/parsing/adapters.py#L294)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence.append`（[adapters.py:295](../../../src/parsing/adapters.py#L295)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `MARKDOWN_IMAGE.finditer`（[adapters.py:296](../../../src/parsing/adapters.py#L296)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `match.group`（[adapters.py:297](../../../src/parsing/adapters.py#L297)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_resolve_image`（调用点 [adapters.py:298](../../../src/parsing/adapters.py#L298)）→ [_resolve_image](adapters.md)，静态可定位。
- `src.startswith`（[adapters.py:302](../../../src/parsing/adapters.py#L302)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `warnings.append`（[adapters.py:305](../../../src/parsing/adapters.py#L305)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_asset`（调用点 [adapters.py:308](../../../src/parsing/adapters.py#L308)）→ [_asset](adapters.md)，静态可定位。
- `assets.append`（[adapters.py:320](../../../src/parsing/adapters.py#L320)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `BeautifulSoup(content, 'html.parser').find_all`（[adapters.py:323](../../../src/parsing/adapters.py#L323)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `BeautifulSoup`（[adapters.py:323](../../../src/parsing/adapters.py#L323)）：来自 `bs4.BeautifulSoup`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[adapters.py:324](../../../src/parsing/adapters.py#L324)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `image.get`（[adapters.py:324](../../../src/parsing/adapters.py#L324)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_html_image_context`（调用点 [adapters.py:342](../../../src/parsing/adapters.py#L342)）→ [_html_image_context](adapters.md)，静态可定位。
- `DocumentIR`（[adapters.py:349](../../../src/parsing/adapters.py#L349)）：来自 `src.domain.DocumentIR`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# HTMLParser ⭐⭐⭐

**位置与等级**：[adapters.py:361](../../../src/parsing/adapters.py#L361)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`HTMLParser.__init__`、`HTMLParser.supports`、`HTMLParser.parse`


---

# HTMLParser.__init__ ⭐⭐⭐

**位置与等级**：[adapters.py:362](../../../src/parsing/adapters.py#L362)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def __init__(self, asset_dir: Path | None=None, allow_remote: bool=False) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`asset_dir`（Path | None；默认 `None`）；`allow_remote`（bool；默认 `False`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.writer`，值来自 `AssetWriter(asset_dir)`。
2. 更新 `self.allow_remote`，值来自 `allow_remote`。

**调用与被调用**：
- `AssetWriter`（调用点 [adapters.py:363](../../../src/parsing/adapters.py#L363)）→ [AssetWriter](adapters.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.writer`、`self.allow_remote`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# HTMLParser.supports ⭐⭐⭐

**位置与等级**：[adapters.py:366](../../../src/parsing/adapters.py#L366)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def supports(self, media_type: str) -> bool`。

**作用**：处理 `supports` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`media_type`（str）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `media_type in HTML_TYPES`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# HTMLParser.parse ⭐⭐⭐

**位置与等级**：[adapters.py:369](../../../src/parsing/adapters.py#L369)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def parse(self, source: SourceDocument) -> DocumentIR`。

**作用**：处理 `parse` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`source`（SourceDocument）。
- 输出类型：`DocumentIR`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `path`，值来自 `source.path.resolve()`。
2. 更新 `source_hash`，值来自 `file_sha256(path)`。
3. 更新 `document_id`，值来自 `stable_id('doc', source_hash)`。
4. 更新 `soup`，值来自 `BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')`。
5. 更新 `blocks`，值来自 `[]`。
6. 更新 `assets`，值来自 `[]`。
7. 更新 `evidence`，值来自 `[]`。
8. 更新 `warnings`，值来自 `[]`。
9. 遍历 `enumerate(soup.find_all(['p', 'li', 'h1', 'h2', 'h3', 'figcaption']))`，逐项处理 `(ordinal, element)`。
10. 遍历 `enumerate(soup.find_all('img'))`，逐项处理 `(ordinal, image)`。
11. 返回 `DocumentIR(id=document_id, source_path=str(path), source_hash=source_hash, media_type='text/html', text_…`。

**关键条件与保护**：
- [adapters.py:382](../../../src/parsing/adapters.py#L382)：`text`，不满足时跳过本分支。
- [adapters.py:389](../../../src/parsing/adapters.py#L389)：`resolved is None`，不满足时跳过本分支。
- [adapters.py:408](../../../src/parsing/adapters.py#L408)：`warning`，不满足时跳过本分支。
- [adapters.py:410](../../../src/parsing/adapters.py#L410)：`asset and asset_ref`，不满足时跳过本分支。

**调用与被调用**：
- `source.path.resolve`（[adapters.py:370](../../../src/parsing/adapters.py#L370)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `file_sha256`（调用点 [adapters.py:371](../../../src/parsing/adapters.py#L371)）→ [file_sha256](../core/ids.md)，静态可定位。
- `stable_id`（调用点 [adapters.py:372](../../../src/parsing/adapters.py#L372)）→ [stable_id](../core/ids.md)，静态可定位。
- `BeautifulSoup`（[adapters.py:373](../../../src/parsing/adapters.py#L373)）：来自 `bs4.BeautifulSoup`；具体实现可能由依赖注入或运行时分派决定。
- `path.read_text`（[adapters.py:373](../../../src/parsing/adapters.py#L373)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `enumerate`（[adapters.py:378](../../../src/parsing/adapters.py#L378)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `soup.find_all`（[adapters.py:379](../../../src/parsing/adapters.py#L379)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `element.get_text`（[adapters.py:381](../../../src/parsing/adapters.py#L381)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_text_block`（调用点 [adapters.py:383](../../../src/parsing/adapters.py#L383)）→ [_text_block](adapters.md)，静态可定位。
- `blocks.append`（[adapters.py:384](../../../src/parsing/adapters.py#L384)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence.append`（[adapters.py:385](../../../src/parsing/adapters.py#L385)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[adapters.py:387](../../../src/parsing/adapters.py#L387)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `image.get`（[adapters.py:387](../../../src/parsing/adapters.py#L387)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_resolve_image`（调用点 [adapters.py:388](../../../src/parsing/adapters.py#L388)）→ [_resolve_image](adapters.md)，静态可定位。
- `src.startswith`（[adapters.py:392](../../../src/parsing/adapters.py#L392)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `warnings.append`（[adapters.py:395](../../../src/parsing/adapters.py#L395)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_html_image_context`（调用点 [adapters.py:398](../../../src/parsing/adapters.py#L398)）→ [_html_image_context](adapters.md)，静态可定位。
- `_asset`（调用点 [adapters.py:399](../../../src/parsing/adapters.py#L399)）→ [_asset](adapters.md)，静态可定位。
- `assets.append`（[adapters.py:411](../../../src/parsing/adapters.py#L411)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `DocumentIR`（[adapters.py:413](../../../src/parsing/adapters.py#L413)）：来自 `src.domain.DocumentIR`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# DOCXParser ⭐⭐⭐

**位置与等级**：[adapters.py:425](../../../src/parsing/adapters.py#L425)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`DOCXParser.__init__`、`DOCXParser.supports`、`DOCXParser.parse`


---

# DOCXParser.__init__ ⭐⭐⭐

**位置与等级**：[adapters.py:426](../../../src/parsing/adapters.py#L426)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def __init__(self, asset_dir: Path | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`asset_dir`（Path | None；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.writer`，值来自 `AssetWriter(asset_dir)`。

**调用与被调用**：
- `AssetWriter`（调用点 [adapters.py:427](../../../src/parsing/adapters.py#L427)）→ [AssetWriter](adapters.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.writer`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# DOCXParser.supports ⭐⭐⭐

**位置与等级**：[adapters.py:429](../../../src/parsing/adapters.py#L429)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def supports(self, media_type: str) -> bool`。

**作用**：处理 `supports` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`media_type`（str）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `media_type == DOCX_TYPE`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# DOCXParser.parse ⭐⭐⭐

**位置与等级**：[adapters.py:432](../../../src/parsing/adapters.py#L432)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def parse(self, source: SourceDocument) -> DocumentIR`。

**作用**：处理 `parse` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`source`（SourceDocument）。
- 输出类型：`DocumentIR`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `path`，值来自 `source.path.resolve()`。
2. 更新 `source_hash`，值来自 `file_sha256(path)`。
3. 更新 `document_id`，值来自 `stable_id('doc', source_hash)`。
4. 更新 `document`，值来自 `Document(str(path))`。
5. 更新 `blocks`，值来自 `[]`。
6. 更新 `assets`，值来自 `[]`。
7. 更新 `evidence`，值来自 `[]`。
8. 更新 `warnings`，值来自 `[]`。
9. 遍历 `enumerate(document.paragraphs)`，逐项处理 `(ordinal, paragraph)`。
10. 返回 `DocumentIR(id=document_id, source_path=str(path), source_hash=source_hash, media_type=DOCX_TYPE, text_bl…`。

**关键条件与保护**：
- [adapters.py:443](../../../src/parsing/adapters.py#L443)：`text`，不满足时跳过本分支。
- [adapters.py:451](../../../src/parsing/adapters.py#L451)：`not rid or rid not in document.part.related_parts`，不满足时跳过本分支。
- [adapters.py:463](../../../src/parsing/adapters.py#L463)：`warning`，不满足时跳过本分支。
- [adapters.py:465](../../../src/parsing/adapters.py#L465)：`asset and asset_ref`，不满足时跳过本分支。

**调用与被调用**：
- `source.path.resolve`（[adapters.py:433](../../../src/parsing/adapters.py#L433)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `file_sha256`（调用点 [adapters.py:434](../../../src/parsing/adapters.py#L434)）→ [file_sha256](../core/ids.md)，静态可定位。
- `stable_id`（调用点 [adapters.py:435](../../../src/parsing/adapters.py#L435)）→ [stable_id](../core/ids.md)，静态可定位。
- `Document`（[adapters.py:436](../../../src/parsing/adapters.py#L436)）：来自 `docx.Document`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[adapters.py:436](../../../src/parsing/adapters.py#L436)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `enumerate`（[adapters.py:441](../../../src/parsing/adapters.py#L441)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `paragraph.text.strip`（[adapters.py:442](../../../src/parsing/adapters.py#L442)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_text_block`（调用点 [adapters.py:444](../../../src/parsing/adapters.py#L444)）→ [_text_block](adapters.md)，静态可定位。
- `blocks.append`（[adapters.py:445](../../../src/parsing/adapters.py#L445)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence.append`（[adapters.py:446](../../../src/parsing/adapters.py#L446)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `paragraph._element.xpath`（[adapters.py:447](../../../src/parsing/adapters.py#L447)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `blip.get`（[adapters.py:448](../../../src/parsing/adapters.py#L448)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_asset`（调用点 [adapters.py:454](../../../src/parsing/adapters.py#L454)）→ [_asset](adapters.md)，静态可定位。
- `getattr`（[adapters.py:458](../../../src/parsing/adapters.py#L458)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `warnings.append`（[adapters.py:464](../../../src/parsing/adapters.py#L464)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `assets.append`（[adapters.py:466](../../../src/parsing/adapters.py#L466)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `DocumentIR`（[adapters.py:468](../../../src/parsing/adapters.py#L468)）：来自 `src.domain.DocumentIR`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# PDFParser ⭐⭐⭐

**位置与等级**：[adapters.py:480](../../../src/parsing/adapters.py#L480)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`PDFParser.__init__`、`PDFParser.supports`、`PDFParser.parse`


---

# PDFParser.__init__ ⭐⭐⭐

**位置与等级**：[adapters.py:481](../../../src/parsing/adapters.py#L481)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def __init__(self, asset_dir: Path | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`asset_dir`（Path | None；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.writer`，值来自 `AssetWriter(asset_dir)`。

**调用与被调用**：
- `AssetWriter`（调用点 [adapters.py:482](../../../src/parsing/adapters.py#L482)）→ [AssetWriter](adapters.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.writer`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# PDFParser.supports ⭐⭐⭐

**位置与等级**：[adapters.py:484](../../../src/parsing/adapters.py#L484)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def supports(self, media_type: str) -> bool`。

**作用**：处理 `supports` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`media_type`（str）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `media_type == 'application/pdf'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# PDFParser.parse ⭐⭐⭐

**位置与等级**：[adapters.py:487](../../../src/parsing/adapters.py#L487)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def parse(self, source: SourceDocument) -> DocumentIR`。

**作用**：处理 `parse` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`source`（SourceDocument）。
- 输出类型：`DocumentIR`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `path`，值来自 `source.path.resolve()`。
2. 更新 `source_hash`，值来自 `file_sha256(path)`。
3. 更新 `document_id`，值来自 `stable_id('doc', source_hash)`。
4. 更新 `blocks`，值来自 `[]`。
5. 更新 `assets`，值来自 `[]`。
6. 更新 `evidence`，值来自 `[]`。
7. 更新 `pages`，值来自 `[]`。
8. 更新 `warnings`，值来自 `[]`。
9. 进入上下文 `pymupdf.open(path)`，由上下文管理器控制资源释放或事务范围。
10. 返回 `DocumentIR(id=document_id, source_path=str(path), source_hash=source_hash, media_type='application/pdf',…`。

**关键条件与保护**：
- [adapters.py:502](../../../src/parsing/adapters.py#L502)：`raw_block.get('type') != 0`，不满足时跳过本分支。
- [adapters.py:509](../../../src/parsing/adapters.py#L509)：`not text`，不满足时跳过本分支。
- [adapters.py:524](../../../src/parsing/adapters.py#L524)：`xref in seen_xrefs`，不满足时跳过本分支。
- [adapters.py:539](../../../src/parsing/adapters.py#L539)：`warning`，不满足时跳过本分支。
- [adapters.py:541](../../../src/parsing/adapters.py#L541)：`asset and asset_ref`，不满足时跳过本分支。
- [adapters.py:546](../../../src/parsing/adapters.py#L546)：`requires_ocr or len(page.get_drawings()) >= 5`，不满足时跳过本分支。
- [adapters.py:559](../../../src/parsing/adapters.py#L559)：`warning`，不满足时跳过本分支。
- [adapters.py:561](../../../src/parsing/adapters.py#L561)：`asset and asset_ref`，不满足时跳过本分支。
- [adapters.py:565](../../../src/parsing/adapters.py#L565)：`requires_ocr`，不满足时跳过本分支。

**调用与被调用**：
- `source.path.resolve`（[adapters.py:488](../../../src/parsing/adapters.py#L488)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `file_sha256`（调用点 [adapters.py:489](../../../src/parsing/adapters.py#L489)）→ [file_sha256](../core/ids.md)，静态可定位。
- `stable_id`（调用点 [adapters.py:490](../../../src/parsing/adapters.py#L490)）→ [stable_id](../core/ids.md)，静态可定位。
- `pymupdf.open`（[adapters.py:496](../../../src/parsing/adapters.py#L496)）：来自 `pymupdf`；具体实现可能由依赖注入或运行时分派决定。
- `enumerate`（[adapters.py:497](../../../src/parsing/adapters.py#L497)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `page.get_text('dict').get`（[adapters.py:501](../../../src/parsing/adapters.py#L501)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `page.get_text`（[adapters.py:501](../../../src/parsing/adapters.py#L501)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `raw_block.get`（[adapters.py:502](../../../src/parsing/adapters.py#L502)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `''.join((span.get('text', '') for line in raw_block.get('lines', []) for span in line.get…`（[adapters.py:504](../../../src/parsing/adapters.py#L504)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `''.join`（[adapters.py:504](../../../src/parsing/adapters.py#L504)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `span.get`（[adapters.py:505](../../../src/parsing/adapters.py#L505)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `line.get`（[adapters.py:507](../../../src/parsing/adapters.py#L507)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `BBox`（[adapters.py:511](../../../src/parsing/adapters.py#L511)）：来自 `src.domain.BBox`；具体实现可能由依赖注入或运行时分派决定。
- `dict`（[adapters.py:512](../../../src/parsing/adapters.py#L512)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `zip`（[adapters.py:512](../../../src/parsing/adapters.py#L512)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_text_block`（调用点 [adapters.py:514](../../../src/parsing/adapters.py#L514)）→ [_text_block](adapters.md)，静态可定位。
- `blocks.append`（[adapters.py:518](../../../src/parsing/adapters.py#L518)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence.append`（[adapters.py:519](../../../src/parsing/adapters.py#L519)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `page_blocks.append`（[adapters.py:520](../../../src/parsing/adapters.py#L520)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `set`（[adapters.py:521](../../../src/parsing/adapters.py#L521)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `page.get_images`（[adapters.py:522](../../../src/parsing/adapters.py#L522)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `int`（[adapters.py:523](../../../src/parsing/adapters.py#L523)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `seen_xrefs.add`（[adapters.py:526](../../../src/parsing/adapters.py#L526)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `pdf.extract_image`（[adapters.py:527](../../../src/parsing/adapters.py#L527)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `extracted.get`（[adapters.py:528](../../../src/parsing/adapters.py#L528)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_asset`（调用点 [adapters.py:529](../../../src/parsing/adapters.py#L529)）→ [_asset](adapters.md)，静态可定位。
- `<字符串常量>.join`（[adapters.py:536](../../../src/parsing/adapters.py#L536)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `warnings.append`（[adapters.py:540](../../../src/parsing/adapters.py#L540)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `assets.append`（[adapters.py:542](../../../src/parsing/adapters.py#L542)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `page_assets.append`（[adapters.py:544](../../../src/parsing/adapters.py#L544)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 此处列出前 30 个不同调用表达式，另有 8 个，需按源码继续追踪。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ImageParser ⭐⭐⭐

**位置与等级**：[adapters.py:591](../../../src/parsing/adapters.py#L591)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`ImageParser.__init__`、`ImageParser.supports`、`ImageParser.parse`


---

# ImageParser.__init__ ⭐⭐⭐

**位置与等级**：[adapters.py:592](../../../src/parsing/adapters.py#L592)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def __init__(self, asset_dir: Path | None=None) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`asset_dir`（Path | None；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self.writer`，值来自 `AssetWriter(asset_dir)`。

**调用与被调用**：
- `AssetWriter`（调用点 [adapters.py:593](../../../src/parsing/adapters.py#L593)）→ [AssetWriter](adapters.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self.writer`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ImageParser.supports ⭐⭐⭐

**位置与等级**：[adapters.py:595](../../../src/parsing/adapters.py#L595)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def supports(self, media_type: str) -> bool`。

**作用**：处理 `supports` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`media_type`（str）。
- 输出类型：`bool`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `media_type in IMAGE_TYPES`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ImageParser.parse ⭐⭐⭐

**位置与等级**：[adapters.py:598](../../../src/parsing/adapters.py#L598)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def parse(self, source: SourceDocument) -> DocumentIR`。

**作用**：处理 `parse` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`source`（SourceDocument）。
- 输出类型：`DocumentIR`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `path`，值来自 `source.path.resolve()`。
2. 更新 `source_hash`，值来自 `file_sha256(path)`。
3. 更新 `document_id`，值来自 `stable_id('doc', source_hash)`。
4. 更新 `media_type`，值来自 `detect_media_type(path, source.media_type)`。
5. 更新 `(asset, ref, warning)`，值来自 `_asset(self.writer, document_id, path.read_bytes(), media_type, 'source_image', str(path), requires…`。
6. 返回 `DocumentIR(id=document_id, source_path=str(path), source_hash=source_hash, media_type=media_type, media_…`。

**调用与被调用**：
- `source.path.resolve`（[adapters.py:599](../../../src/parsing/adapters.py#L599)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `file_sha256`（调用点 [adapters.py:600](../../../src/parsing/adapters.py#L600)）→ [file_sha256](../core/ids.md)，静态可定位。
- `stable_id`（调用点 [adapters.py:601](../../../src/parsing/adapters.py#L601)）→ [stable_id](../core/ids.md)，静态可定位。
- `detect_media_type`（调用点 [adapters.py:602](../../../src/parsing/adapters.py#L602)）→ [detect_media_type](adapters.md)，静态可定位。
- `_asset`（调用点 [adapters.py:603](../../../src/parsing/adapters.py#L603)）→ [_asset](adapters.md)，静态可定位。
- `path.read_bytes`（[adapters.py:606](../../../src/parsing/adapters.py#L606)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[adapters.py:609](../../../src/parsing/adapters.py#L609)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `DocumentIR`（[adapters.py:612](../../../src/parsing/adapters.py#L612)）：来自 `src.domain.DocumentIR`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
