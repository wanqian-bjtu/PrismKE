# core 目录导读

**职责**：全局设置、稳定标识、执行控制与错误类型；为其他层提供通用约束。

**上下游**：依赖领域契约及本目录所列导入；上层 CLI/API/工作流可经应用服务或协议调用。跨层调用请以逐文件导入与调用点为准，不将动态注入写成静态依赖。

## 文件

- [__init__.py](__init__.md)：Shared configuration, identifiers, and errors.（0 个符号）。
- [errors.py](errors.md)：PrismKE-specific exceptions.（12 个符号）。
- [execution_control.py](execution_control.md)：Cooperative control propagates into LangGraph branches and native OCR threads.（12 个符号）。
- [ids.py](ids.md)：Stable content-derived identifiers and fingerprints.（3 个符号）。
- [settings.py](settings.md)：Environment-backed application settings.（12 个符号）。

返回[总索引](../README.md)。
