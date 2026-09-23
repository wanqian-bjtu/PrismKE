# web 目录导读

**职责**：指向项目根目录 frontend 的兼容转发层，不是页面实现。

**上下游**：依赖领域契约及本目录所列导入；上层 CLI/API/工作流可经应用服务或协议调用。跨层调用请以逐文件导入与调用点为准，不将动态注入写成静态依赖。

## 文件

- [__init__.py](__init__.md)：Gradio research workspace.（0 个符号）。
- [app.py](app.md)：Compatibility import; the Gradio implementation lives in frontend.app.（0 个符号）。
- [corrections.py](corrections.md)：Compatibility import for the moved correction frontend.（0 个符号）。
- [execution.py](execution.md)：Compatibility import for the moved execution frontend.（0 个符号）。
- [review.py](review.md)：Compatibility imports for the moved review frontend.（0 个符号）。
- [validation.py](validation.md)：Compatibility import for the moved validation frontend.（0 个符号）。

返回[总索引](../README.md)。
