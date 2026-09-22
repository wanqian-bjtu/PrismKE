# governance/validation 目录导读

**职责**：候选及提交前的统一结构、Schema、引用和证据校验。

**上下游**：依赖领域契约及本目录所列导入；上层 CLI/API/工作流可经应用服务或协议调用。跨层调用请以逐文件导入与调用点为准，不将动态注入写成静态依赖。

## 文件

- [__init__.py](__init__.md)：Shared deterministic validation, used by providers, workflows and stores.（0 个符号）。
- [context.py](context.md)：Reuse recorded schema provenance; never infer a schema from graph data.（3 个符号）。
- [service.py](service.md)：Validation does not repair facts or invoke models.（9 个符号）。

返回[总索引](../../README.md)。
