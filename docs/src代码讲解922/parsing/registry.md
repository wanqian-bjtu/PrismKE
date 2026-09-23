源码：[registry.py:1](../../../src/parsing/registry.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：3

**模块职责**：Parser selection by media type.
**在系统中的位置**：输入文档适配、格式注册与视觉资产提取，向后续抽取提供 DocumentIR。
**直接依赖**：[src.core.errors](../core/errors.md)、[src.domain](../domain/__init__.md)、[src.parsing.adapters](adapters.md)、[src.parsing.base](base.md)；外部/标准库：`pathlib`。
**主要调用方（静态导入）**：[parsing/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# ParserRegistry ⭐⭐⭐

**位置与等级**：[registry.py:19](../../../src/parsing/registry.py#L19)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：无显式基类。

**字段与类级约束**：
- 类体未直接声明字段；实例状态请看 `__init__` 及方法中的赋值。

**内部成员**：`ParserRegistry.__init__`、`ParserRegistry.parse`


---

# ParserRegistry.__init__ ⭐⭐⭐

**位置与等级**：[registry.py:20](../../../src/parsing/registry.py#L20)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def __init__(self, parsers: list[ParserAdapter] | None=None, asset_dir: Path | None=None, allow_remote_assets: bool=False) -> None`。

**作用**：初始化对象并保存依赖或配置；需检查是否创建持久化资源。

**输入与输出**：
- 输入：`parsers`（list[ParserAdapter] | None；默认 `None`）；`asset_dir`（Path | None；默认 `None`）；`allow_remote_assets`（bool；默认 `False`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `self._parsers`，值来自 `parsers or [TextParser(), MarkdownParser(asset_dir, allow_remote_assets), HTMLParser(asset_dir, all…`。

**调用与被调用**：
- `TextParser`（调用点 [registry.py:27](../../../src/parsing/registry.py#L27)）→ [TextParser](adapters.md)，静态可定位。
- `MarkdownParser`（调用点 [registry.py:28](../../../src/parsing/registry.py#L28)）→ [MarkdownParser](adapters.md)，静态可定位。
- `HTMLParser`（调用点 [registry.py:29](../../../src/parsing/registry.py#L29)）→ [HTMLParser](adapters.md)，静态可定位。
- `DOCXParser`（调用点 [registry.py:30](../../../src/parsing/registry.py#L30)）→ [DOCXParser](adapters.md)，静态可定位。
- `PDFParser`（调用点 [registry.py:31](../../../src/parsing/registry.py#L31)）→ [PDFParser](adapters.md)，静态可定位。
- `ImageParser`（调用点 [registry.py:32](../../../src/parsing/registry.py#L32)）→ [ImageParser](adapters.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`self._parsers`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# ParserRegistry.parse ⭐⭐⭐

**位置与等级**：[registry.py:35](../../../src/parsing/registry.py#L35)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def parse(self, source: SourceDocument) -> DocumentIR`。

**作用**：处理 `parse` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`source`（SourceDocument）。
- 输出类型：`DocumentIR`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `media_type`，值来自 `detect_media_type(source.path, source.media_type)`。
2. 遍历 `self._parsers`，逐项处理 `parser`。
3. 抛出 `UnsupportedDocumentError(f<字符串常量>unknown<字符串常量>)`。

**关键条件与保护**：
- [registry.py:38](../../../src/parsing/registry.py#L38)：`parser.supports(media_type)`，不满足时跳过本分支。

**调用与被调用**：
- `detect_media_type`（调用点 [registry.py:36](../../../src/parsing/registry.py#L36)）→ [detect_media_type](adapters.md)，静态可定位。
- `parser.supports`（[registry.py:38](../../../src/parsing/registry.py#L38)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `parser.parse`（[registry.py:39](../../../src/parsing/registry.py#L39)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `UnsupportedDocumentError`（调用点 [registry.py:40](../../../src/parsing/registry.py#L40)）→ [UnsupportedDocumentError](../core/errors.md)，静态可定位。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`UnsupportedDocumentError(f<字符串常量>unknown<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
