# api 目录导读

**职责**：FastAPI 路由和请求/响应模型；负责参数解析、调用应用服务与 HTTP 错误映射。

**上下游**：依赖领域契约及本目录所列导入；上层 CLI/API/工作流可经应用服务或协议调用。跨层调用请以逐文件导入与调用点为准，不将动态注入写成静态依赖。

## 文件

- [__init__.py](__init__.md)：HTTP application factory.（0 个符号）。
- [app.py](app.md)：FastAPI adapter for the shared PrismKE application service.（50 个符号）。
- [models.py](models.md)：Public HTTP request and response models.（14 个符号）。

返回[总索引](../README.md)。
