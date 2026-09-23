源码：[app.py:1](../../../src/api/app.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：50

**模块职责**：FastAPI adapter for the shared PrismKE application service.
**在系统中的位置**：FastAPI 路由和请求/响应模型；负责参数解析、调用应用服务与 HTTP 错误映射。
**阅读重点**：HTTP 层维护资源生命周期、服务注入和路由闭包。业务规则在应用服务中，HTTP 异常映射需要与服务异常区分。
**直接依赖**：[src](../__init__.md)、[src.api.models](models.md)、[src.core.errors](../core/errors.md)、[src.core.settings](../core/settings.md)、[src.persistence.execution](../persistence/execution.md)、[src.workflow](../workflow/__init__.md)；外部/标准库：`__future__`、`collections`、`contextlib`、`fastapi`、`filelock`、`hmac`、`pathlib`、`typing`、`uuid`。
**主要调用方（静态导入）**：[api/__init__.py](__init__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

## 核心路径解读

- `create_app` 组合 FastAPI 生命周期、授权和路由；上传、运行、审核、校验、证据、图谱及版本接口从请求模型进入 PrismKEService/ExecutionManager。
- 位于 `create_app` 内部的路由闭包也是实际 API 处理函数，已在下文单独列出。调用依赖注入服务而非让 HTTP 层直接拼写 Neo4j Cypher。
- 鉴权、运行版本冲突、缺失资源、证据损坏和存储失败应分别处理；健康接口只能报告状态，不能泄露密钥和完整请求。

---

# _safe_suffix ⭐⭐

**位置与等级**：[app.py:58](../../../src/api/app.py#L58)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _safe_suffix(filename: str | None) -> str`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`filename`（str | None）。
- 输出类型：`str`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `suffix`，值来自 `Path(filename or 'upload.bin').suffix.lower()`。
2. 返回 `suffix if suffix and len(suffix) <= 12 else '.bin'`。

**调用与被调用**：
- `Path(filename or 'upload.bin').suffix.lower`（[app.py:59](../../../src/api/app.py#L59)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Path`（[app.py:59](../../../src/api/app.py#L59)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `len`（[app.py:60](../../../src/api/app.py#L60)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[_save_upload](app.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _save_upload ⭐⭐

**位置与等级**：[app.py:63](../../../src/api/app.py#L63)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def _save_upload(upload: UploadFile, directory: Path) -> Path`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`upload`（UploadFile）；`directory`（Path）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `content`，值来自 `await upload.read(MAX_UPLOAD_BYTES + 1)`。
2. 检查 `len(content) > MAX_UPLOAD_BYTES`；按条件分流，else 分支不存在。
3. 调用 `directory.mkdir`，结果未直接赋值。
4. 更新 `path`，值来自 `directory / f<字符串常量>`。
5. 调用 `path.write_bytes`，结果未直接赋值。
6. 返回 `path`。

**关键条件与保护**：
- [app.py:65](../../../src/api/app.py#L65)：`len(content) > MAX_UPLOAD_BYTES`，不满足时跳过本分支。

**调用与被调用**：
- `upload.read`（[app.py:64](../../../src/api/app.py#L64)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[app.py:65](../../../src/api/app.py#L65)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:66](../../../src/api/app.py#L66)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `directory.mkdir`（[app.py:67](../../../src/api/app.py#L67)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `uuid4`（[app.py:68](../../../src/api/app.py#L68)）：来自 `uuid.uuid4`；具体实现可能由依赖注入或运行时分派决定。
- `_safe_suffix`（调用点 [app.py:68](../../../src/api/app.py#L68)）→ [_safe_suffix](app.md)，静态可定位。
- `path.write_bytes`（[app.py:69](../../../src/api/app.py#L69)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态可定位的调用方：[create_app.create_run](app.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=413, detail=<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# create_app ⭐⭐⭐

**位置与等级**：[app.py:73](../../../src/api/app.py#L73)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`def create_app(settings: Settings | None=None, service: PrismKEService | None=None, *, mount_ui: bool=True) -> FastAPI`。

**作用**：创建、更新或记录相应资源；写入/审计边界以实际调用和状态赋值为准。

**输入与输出**：
- 输入：`settings`（Settings | None；默认 `None`；服务配置；敏感值不应进入输出或文档）；`service`（PrismKEService | None；默认 `None`）；`mount_ui`（bool；默认 `True`）。
- 输出类型：`FastAPI`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `settings`，值来自 `settings or Settings()`。
2. 检查 `settings.api_host not in LOOPBACK_HOSTS and (not settings.api_token)`；按条件分流，else 分支不存在。
3. 更新 `service`，值来自 `service or PrismKEService(settings)`。
4. 更新 `app`，值来自 `FastAPI(title=<字符串常量>, version=__version__, lifespan=lifespan)`。
5. 更新 `app.state.prismke_service`，值来自 `service`。
6. 更新 `api`，值来自 `APIRouter(prefix='/api/v1', dependencies=[Depends(authorize)])`。
7. 调用 `app.include_router`，结果未直接赋值。
8. 检查 `mount_ui`；按条件分流，else 分支不存在。
9. 返回 `app`。

**关键条件与保护**：
- [app.py:80](../../../src/api/app.py#L80)：`settings.api_host not in LOOPBACK_HOSTS and (not settings.api_token)`，不满足时跳过本分支。
- [app.py:618](../../../src/api/app.py#L618)：`mount_ui`，不满足时跳过本分支。

**调用与被调用**：
- `Settings`（调用点 [app.py:79](../../../src/api/app.py#L79)）→ [Settings](../core/settings.md)，静态可定位。
- `ValueError`（[app.py:81](../../../src/api/app.py#L81)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `PrismKEService`（[app.py:82](../../../src/api/app.py#L82)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `FastAPI`（[app.py:101](../../../src/api/app.py#L101)）：来自 `fastapi.FastAPI`；具体实现可能由依赖注入或运行时分派决定。
- `APIRouter`（[app.py:122](../../../src/api/app.py#L122)）：来自 `fastapi.APIRouter`；具体实现可能由依赖注入或运行时分派决定。
- `Depends`（[app.py:122](../../../src/api/app.py#L122)）：来自 `fastapi.Depends`；具体实现可能由依赖注入或运行时分派决定。
- `app.include_router`（[app.py:617](../../../src/api/app.py#L617)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `mount_gradio`（[app.py:624](../../../src/api/app.py#L624)）：来自 `frontend.app.mount_gradio`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`app.state.prismke_service`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：`ImportError`。


---

# create_app.lifespan ⭐⭐⭐

**位置与等级**：[app.py:85](../../../src/api/app.py#L85)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def lifespan(_: FastAPI) -> AsyncIterator[None]`。

**装饰器/路由**：`asynccontextmanager`。

**作用**：处理 `lifespan` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`_`（FastAPI）。
- 输出类型：`AsyncIterator[None]`；具体返回路径见流程步骤。

**处理流程**：
1. 遍历 `{e.run_id for e, _ in service.reviews.repository.pending()}`，逐项处理 `run_id`。
2. 进入上下文 `suppress(Exception)`，由上下文管理器控制资源释放或事务范围。
3. 等待 `service.executions.start()` 完成。
4. 捕获 无显式捕获；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.reviews.repository.pending`（[app.py:86](../../../src/api/app.py#L86)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.runs.mutation_lock`（[app.py:88](../../../src/api/app.py#L88)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.reviews.recover`（[app.py:89](../../../src/api/app.py#L89)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `suppress`（[app.py:93](../../../src/api/app.py#L93)）：来自 `contextlib.suppress`；具体实现可能由依赖注入或运行时分派决定。
- `service.replay_case_projections`（[app.py:94](../../../src/api/app.py#L94)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.executions.start`（[app.py:95](../../../src/api/app.py#L95)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.close`（[app.py:99](../../../src/api/app.py#L99)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：`Exception`。


---

# create_app.execution_conflict ⭐⭐⭐⭐

**位置与等级**：[app.py:105](../../../src/api/app.py#L105)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def execution_conflict(_: Request, exc: ExecutionConflict) -> JSONResponse`。

**装饰器/路由**：`app.exception_handler`。

**作用**：处理 `execution_conflict` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`_`（Request）；`exc`（ExecutionConflict）。
- 输出类型：`JSONResponse`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `code`，值来自 `str(exc)`。
2. 返回 `JSONResponse(status_code=503 if code == 'WORKER_SHUTTING_DOWN' else 409, content={'detail': {'code': cod…`。

**调用与被调用**：
- `str`（[app.py:106](../../../src/api/app.py#L106)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `JSONResponse`（[app.py:107](../../../src/api/app.py#L107)）：来自 `fastapi.responses.JSONResponse`；具体实现可能由依赖注入或运行时分派决定。
- `app.exception_handler`（[app.py:104](../../../src/api/app.py#L104)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# create_app.authorize ⭐⭐⭐

**位置与等级**：[app.py:112](../../../src/api/app.py#L112)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def authorize(authorization: str | None=Header(default=None)) -> None`。

**作用**：处理 `authorize` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`authorization`（str | None；默认 `Header(default=None)`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not settings.api_token`；按条件分流，else 分支不存在。
2. 更新 `expected`，值来自 `f<字符串常量>`。
3. 检查 `authorization is None or not hmac.compare_digest(authorization, expected)`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [app.py:113](../../../src/api/app.py#L113)：`not settings.api_token`，不满足时跳过本分支。
- [app.py:116](../../../src/api/app.py#L116)：`authorization is None or not hmac.compare_digest(authorization, expected)`，不满足时跳过本分支。

**调用与被调用**：
- `Header`（[app.py:112](../../../src/api/app.py#L112)）：来自 `fastapi.Header`；具体实现可能由依赖注入或运行时分派决定。
- `hmac.compare_digest`（[app.py:116](../../../src/api/app.py#L116)）：来自 `hmac`；具体实现可能由依赖注入或运行时分派决定。
- `HTTPException`（[app.py:117](../../../src/api/app.py#L117)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# create_app.create_run ⭐⭐⭐⭐

**位置与等级**：[app.py:125](../../../src/api/app.py#L125)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def create_run(document: Annotated[UploadFile, File()], schema_file: Annotated[UploadFile, File(alias='schema')], provider: Annotated[str, Form()]='mock', ocr_provider: Annotated[str, Form()]='disabled', vlm_provider: Annotated[str, Form()]='disabled', allow_remote_assets: Annotated[bool, Form()]=False, case_mode: Annotated[Literal['none', 'good', 'good_bad'], Form()]='none', reflection_enabled: Annotated[bool, Form()]=False, reflection_provider: Annotated[str, Form()]='disabled', reflection_max_attempts: Annotated[int, Form(ge=0, le=2)]=2, reflection_token_budget: Annotated[int, Form(gt=0)]=20000, reflection_time_budget_seconds: Annotated[int, Form(gt=0)]=180, semantic_advisor: Annotated[str, Form()]='disabled', agent_token_budget: Annotated[int, Form(gt=0)]=20000) -> RunAccepted`。

**装饰器/路由**：`POST /api/v1/runs`。

**作用**：创建、更新或记录相应资源；写入/审计边界以实际调用和状态赋值为准。

**输入与输出**：
- 输入：`document`（Annotated[UploadFile, File()]；解析后的文档及其文本、媒体、证据定位）；`schema_file`（Annotated[UploadFile, File(alias='schema')]）；`provider`（Annotated[str, Form()]；默认 `'mock'`）；`ocr_provider`（Annotated[str, Form()]；默认 `'disabled'`）；`vlm_provider`（Annotated[str, Form()]；默认 `'disabled'`）；`allow_remote_assets`（Annotated[bool, Form()]；默认 `False`）；`case_mode`（Annotated[Literal['none', 'good', 'good_bad'], Form()]；默认 `'none'`）；`reflection_enabled`（Annotated[bool, Form()]；默认 `False`）；`reflection_provider`（Annotated[str, Form()]；默认 `'disabled'`）；`reflection_max_attempts`（Annotated[int, Form(ge=0, le=2)]；默认 `2`）；`reflection_token_budget`（Annotated[int, Form(gt=0)]；默认 `20000`）；`reflection_time_budget_seconds`（Annotated[int, Form(gt=0)]；默认 `180`）；`semantic_advisor`（Annotated[str, Form()]；默认 `'disabled'`）；`agent_token_budget`（Annotated[int, Form(gt=0)]；默认 `20000`）。
- 输出类型：`RunAccepted`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `service.executions.ensure_accepting`，结果未直接赋值。
2. 检查 `service.review_metadata`；按条件分流，else 分支不存在。
3. 更新 `document_path`，值来自 `await _save_upload(document, settings.uploads_dir / 'documents')`。
4. 更新 `schema_path`，值来自 `await _save_upload(schema_file, settings.uploads_dir / 'schemas')`。
5. 更新 `(state, created)`，值来自 `service.create_run(document_path, schema_path, provider, ocr_provider, vlm_provider, allow_remote_a…`。
6. 检查 `created`；按条件分流，else 分支不存在。
7. 返回 `RunAccepted(run_id=state.run_id, status=state.status, created=created, execution=service.executions.view…`。

**关键条件与保护**：
- [app.py:142](../../../src/api/app.py#L142)：`service.review_metadata`，不满足时跳过本分支。
- [app.py:162](../../../src/api/app.py#L162)：`created`，不满足时跳过本分支。

**调用与被调用**：
- `File`（[app.py:126](../../../src/api/app.py#L126)）：来自 `fastapi.File`；具体实现可能由依赖注入或运行时分派决定。
- `Form`（[app.py:128](../../../src/api/app.py#L128)）：来自 `fastapi.Form`；具体实现可能由依赖注入或运行时分派决定。
- `service.executions.ensure_accepting`（[app.py:141](../../../src/api/app.py#L141)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:143](../../../src/api/app.py#L143)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `_save_upload`（调用点 [app.py:144](../../../src/api/app.py#L144)）→ [_save_upload](app.md)，静态可定位。
- `service.create_run`（[app.py:146](../../../src/api/app.py#L146)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.executions.enqueue`（[app.py:163](../../../src/api/app.py#L163)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `RunAccepted`（调用点 [app.py:164](../../../src/api/app.py#L164)）→ [RunAccepted](models.md)，静态可定位。
- `service.executions.view`（[app.py:168](../../../src/api/app.py#L168)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.post`（[app.py:124](../../../src/api/app.py#L124)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=409, detail=<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# create_app.list_runs ⭐⭐⭐⭐

**位置与等级**：[app.py:172](../../../src/api/app.py#L172)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def list_runs() -> object`。

**装饰器/路由**：`GET /api/v1/runs`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `[{**service.review_progress(item.run_id), 'filename': Path(item.input_path).name} for item in service.ru…`。

**调用与被调用**：
- `service.review_progress`（[app.py:174](../../../src/api/app.py#L174)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Path`（[app.py:174](../../../src/api/app.py#L174)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `service.runs.list`（[app.py:175](../../../src/api/app.py#L175)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.get`（[app.py:171](../../../src/api/app.py#L171)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# create_app.review_progress ⭐⭐⭐⭐

**位置与等级**：[app.py:179](../../../src/api/app.py#L179)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def review_progress(run_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/runs/{run_id}/review-progress`。

**作用**：处理 `review_progress` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 FileNotFoundError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.review_progress`（[app.py:181](../../../src/api/app.py#L181)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:183](../../../src/api/app.py#L183)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.get`（[app.py:178](../../../src/api/app.py#L178)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`FileNotFoundError`。


---

# create_app.entity_review_detail ⭐⭐⭐⭐

**位置与等级**：[app.py:186](../../../src/api/app.py#L186)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def entity_review_detail(run_id: str, task_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/runs/{run_id}/entity-reviews/{task_id}`。

**作用**：处理 `entity_review_detail` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`task_id`（str；待处理审核任务标识）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 (KeyError, FileNotFoundError)；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.entity_review_detail`（[app.py:188](../../../src/api/app.py#L188)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:190](../../../src/api/app.py#L190)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.get`（[app.py:185](../../../src/api/app.py#L185)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`(KeyError, FileNotFoundError)`。


---

# create_app.claim_review_detail ⭐⭐⭐⭐

**位置与等级**：[app.py:193](../../../src/api/app.py#L193)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def claim_review_detail(run_id: str, task_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/runs/{run_id}/reviews/{task_id}`。

**作用**：处理 `claim_review_detail` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`task_id`（str；待处理审核任务标识）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 (KeyError, FileNotFoundError)；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.claim_review_detail`（[app.py:195](../../../src/api/app.py#L195)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:197](../../../src/api/app.py#L197)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.get`（[app.py:192](../../../src/api/app.py#L192)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`(KeyError, FileNotFoundError)`。


---

# create_app.confirm_commit ⭐⭐⭐

**位置与等级**：[app.py:200](../../../src/api/app.py#L200)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def confirm_commit(run_id: str, request: RollbackRequest, reviewer: str=Query(min_length=1)) -> object`。

**装饰器/路由**：`POST /api/v1/runs/{run_id}/confirm-commit`。

**作用**：处理 `confirm_commit` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`request`（RollbackRequest）；`reviewer`（str；默认 `Query(min_length=1)`；审核操作者，形成审计归属）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 (ValueError, GraphIntegrityError, Timeout), FileNotFoundError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `Query`（[app.py:201](../../../src/api/app.py#L201)）：来自 `fastapi.Query`；具体实现可能由依赖注入或运行时分派决定。
- `service.confirm_review_commit`（[app.py:204](../../../src/api/app.py#L204)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:206](../../../src/api/app.py#L206)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.post`（[app.py:199](../../../src/api/app.py#L199)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=409, detail=<字符串常量>)`、`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`(ValueError, GraphIntegrityError, Timeout)`、`FileNotFoundError`。


---

# create_app.get_run ⭐⭐⭐⭐

**位置与等级**：[app.py:213](../../../src/api/app.py#L213)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def get_run(run_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/runs/{run_id}`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 FileNotFoundError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.show_run`（[app.py:215](../../../src/api/app.py#L215)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:217](../../../src/api/app.py#L217)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.get`（[app.py:212](../../../src/api/app.py#L212)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`FileNotFoundError`。


---

# create_app.run_validation ⭐⭐⭐⭐

**位置与等级**：[app.py:220](../../../src/api/app.py#L220)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def run_validation(run_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/runs/{run_id}/validation`。

**作用**：处理 `run_validation` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 FileNotFoundError, ValueError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.validate_run`（[app.py:222](../../../src/api/app.py#L222)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:224](../../../src/api/app.py#L224)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[app.py:226](../../../src/api/app.py#L226)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.get`（[app.py:219](../../../src/api/app.py#L219)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`、`HTTPException(status_code=409, detail=str(exc))`。
- 本地捕获：`FileNotFoundError`、`ValueError`。


---

# create_app.agent_traces ⭐⭐⭐

**位置与等级**：[app.py:229](../../../src/api/app.py#L229)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def agent_traces(run_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/runs/{run_id}/agent-traces`。

**作用**：处理 `agent_traces` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 FileNotFoundError；另检查 finally/else 的清理和传播。
2. 返回 `{'policy': state.agent_policy_version, 'handoffs': state.agent_handoffs, 'traces': state.agent_traces, '…`。

**调用与被调用**：
- `service.show_run`（[app.py:231](../../../src/api/app.py#L231)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:233](../../../src/api/app.py#L233)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.get`（[app.py:228](../../../src/api/app.py#L228)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`FileNotFoundError`。


---

# create_app.exclude_validation ⭐⭐⭐

**位置与等级**：[app.py:244](../../../src/api/app.py#L244)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def exclude_validation(run_id: str, issue_id: str, request: ValidationExcludeRequest) -> object`。

**装饰器/路由**：`POST /api/v1/runs/{run_id}/validation-issues/{issue_id}/exclude`。

**作用**：处理 `exclude_validation` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`issue_id`（str）；`request`（ValidationExcludeRequest）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 FileNotFoundError, (ValueError, LegacyCheckpointError, Timeout)；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.exclude_validation_issue`（[app.py:248](../../../src/api/app.py#L248)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:252](../../../src/api/app.py#L252)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.post`（[app.py:243](../../../src/api/app.py#L243)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`、`HTTPException(status_code=409, detail=<字符串常量>)`。
- 本地捕获：`FileNotFoundError`、`(ValueError, LegacyCheckpointError, Timeout)`。


---

# create_app.resume_run ⭐⭐⭐⭐

**位置与等级**：[app.py:259](../../../src/api/app.py#L259)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def resume_run(run_id: str, request: ResumeRequest | None=None) -> RunAccepted`。

**装饰器/路由**：`POST /api/v1/runs/{run_id}/resume`。

**作用**：处理 `resume_run` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`request`（ResumeRequest | None；默认 `None`）。
- 输出类型：`RunAccepted`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 FileNotFoundError；另检查 finally/else 的清理和传播。
2. 捕获 (ExecutionConflict, LegacyCheckpointError)；另检查 finally/else 的清理和传播。
3. 返回 `RunAccepted(run_id=run_id, status=state.status, created=False, execution=service.executions.view(run_id))`。

**调用与被调用**：
- `service.show_run`（[app.py:261](../../../src/api/app.py#L261)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:263](../../../src/api/app.py#L263)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `service.executions.enqueue`（[app.py:266](../../../src/api/app.py#L266)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[app.py:270](../../../src/api/app.py#L270)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `RunAccepted`（调用点 [app.py:271](../../../src/api/app.py#L271)）→ [RunAccepted](models.md)，静态可定位。
- `service.executions.view`（[app.py:275](../../../src/api/app.py#L275)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.post`（[app.py:258](../../../src/api/app.py#L258)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`、`HTTPException(status_code=409, detail={'code': str(exc)})`。
- 本地捕获：`FileNotFoundError`、`(ExecutionConflict, LegacyCheckpointError)`。


---

# create_app.execution_status ⭐⭐⭐

**位置与等级**：[app.py:279](../../../src/api/app.py#L279)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def execution_status(run_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/runs/{run_id}/execution`。

**作用**：处理 `execution_status` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 FileNotFoundError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.review_progress`（[app.py:281](../../../src/api/app.py#L281)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:288](../../../src/api/app.py#L288)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.get`（[app.py:278](../../../src/api/app.py#L278)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`FileNotFoundError`。


---

# create_app.execution_events ⭐⭐⭐

**位置与等级**：[app.py:291](../../../src/api/app.py#L291)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def execution_events(run_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/runs/{run_id}/execution-events`。

**作用**：处理 `execution_events` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 FileNotFoundError；另检查 finally/else 的清理和传播。
2. 返回 `service.executions.repository.events(run_id)`。

**调用与被调用**：
- `service.show_run`（[app.py:293](../../../src/api/app.py#L293)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:295](../../../src/api/app.py#L295)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `service.executions.repository.events`（[app.py:296](../../../src/api/app.py#L296)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.get`（[app.py:290](../../../src/api/app.py#L290)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`FileNotFoundError`。


---

# create_app.workspace_summary ⭐⭐⭐

**位置与等级**：[app.py:299](../../../src/api/app.py#L299)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def workspace_summary() -> object`。

**装饰器/路由**：`GET /api/v1/workspace/summary`。

**作用**：处理 `workspace_summary` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await service.workspace_summary()`。

**调用与被调用**：
- `service.workspace_summary`（[app.py:300](../../../src/api/app.py#L300)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.get`（[app.py:298](../../../src/api/app.py#L298)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# create_app.list_cases ⭐⭐⭐

**位置与等级**：[app.py:303](../../../src/api/app.py#L303)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def list_cases(case_type: str | None=Query(default=None), task_type: str | None=Query(default=None), language: str | None=Query(default=None), active_only: bool=Query(default=True), limit: int=Query(default=200, ge=1, le=1000)) -> object`。

**装饰器/路由**：`GET /api/v1/cases`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`case_type`（str | None；默认 `Query(default=None)`）；`task_type`（str | None；默认 `Query(default=None)`）；`language`（str | None；默认 `Query(default=None)`）；`active_only`（bool；默认 `Query(default=True)`）；`limit`（int；默认 `Query(default=200, ge=1, le=1000)`；查询或展示的最大条数）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `service.list_cases(case_type=case_type, task_type=task_type, language=language, active_only=active_only,…`。

**调用与被调用**：
- `Query`（[app.py:304](../../../src/api/app.py#L304)）：来自 `fastapi.Query`；具体实现可能由依赖注入或运行时分派决定。
- `service.list_cases`（[app.py:310](../../../src/api/app.py#L310)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.get`（[app.py:302](../../../src/api/app.py#L302)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# create_app.rebuild_case_index ⭐⭐⭐

**位置与等级**：[app.py:319](../../../src/api/app.py#L319)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def rebuild_case_index(request: CaseIndexRequest) -> object`。

**装饰器/路由**：`POST /api/v1/cases/rebuild-index`。

**作用**：处理 `rebuild_case_index` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（CaseIndexRequest）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 ProviderConfigurationError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.rebuild_case_index`（[app.py:321](../../../src/api/app.py#L321)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:323](../../../src/api/app.py#L323)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[app.py:323](../../../src/api/app.py#L323)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.post`（[app.py:318](../../../src/api/app.py#L318)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=409, detail=str(exc))`。
- 本地捕获：`ProviderConfigurationError`。


---

# create_app.get_case ⭐⭐⭐

**位置与等级**：[app.py:326](../../../src/api/app.py#L326)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def get_case(case_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/cases/{case_id}`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`case_id`（str）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 KeyError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.get_case`（[app.py:328](../../../src/api/app.py#L328)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:330](../../../src/api/app.py#L330)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.get`（[app.py:325](../../../src/api/app.py#L325)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`KeyError`。


---

# create_app.disable_case ⭐⭐⭐

**位置与等级**：[app.py:333](../../../src/api/app.py#L333)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def disable_case(case_id: str, request: CaseDisableRequest) -> object`。

**装饰器/路由**：`POST /api/v1/cases/{case_id}/disable`。

**作用**：处理 `disable_case` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`case_id`（str）；`request`（CaseDisableRequest）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 KeyError, ValueError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.disable_case`（[app.py:335](../../../src/api/app.py#L335)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:342](../../../src/api/app.py#L342)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[app.py:344](../../../src/api/app.py#L344)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.post`（[app.py:332](../../../src/api/app.py#L332)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`、`HTTPException(status_code=409, detail=str(exc))`。
- 本地捕获：`KeyError`、`ValueError`。


---

# create_app.retrieved_cases ⭐⭐⭐

**位置与等级**：[app.py:347](../../../src/api/app.py#L347)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def retrieved_cases(run_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/runs/{run_id}/retrieved-cases`。

**作用**：处理 `retrieved_cases` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 FileNotFoundError；另检查 finally/else 的清理和传播。
2. 返回 `state.retrieved_cases`。

**调用与被调用**：
- `service.show_run`（[app.py:349](../../../src/api/app.py#L349)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:351](../../../src/api/app.py#L351)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.get`（[app.py:346](../../../src/api/app.py#L346)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`FileNotFoundError`。


---

# create_app.runtime_settings ⭐⭐⭐⭐

**位置与等级**：[app.py:355](../../../src/api/app.py#L355)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def runtime_settings() -> object`。

**装饰器/路由**：`GET /api/v1/settings`。

**作用**：处理 `runtime_settings` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `service.settings_view()`。

**调用与被调用**：
- `service.settings_view`（[app.py:356](../../../src/api/app.py#L356)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.get`（[app.py:354](../../../src/api/app.py#L354)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# create_app.update_runtime_settings ⭐⭐⭐⭐

**位置与等级**：[app.py:359](../../../src/api/app.py#L359)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def update_runtime_settings(request: RuntimeSettingsUpdate) -> object`。

**装饰器/路由**：`PATCH /api/v1/settings`。

**作用**：创建、更新或记录相应资源；写入/审计边界以实际调用和状态赋值为准。

**输入与输出**：
- 输入：`request`（RuntimeSettingsUpdate）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 (ValueError, ProviderConfigurationError)；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.update_settings`（[app.py:361](../../../src/api/app.py#L361)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[app.py:363](../../../src/api/app.py#L363)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:367](../../../src/api/app.py#L367)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.patch`（[app.py:358](../../../src/api/app.py#L358)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=422, detail=str(exc))`。
- 本地捕获：`(ValueError, ProviderConfigurationError)`。


---

# create_app.branch_progress ⭐⭐⭐

**位置与等级**：[app.py:370](../../../src/api/app.py#L370)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def branch_progress(run_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/runs/{run_id}/branch-progress`。

**作用**：处理 `branch_progress` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 FileNotFoundError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.executions.branch_progress`（[app.py:372](../../../src/api/app.py#L372)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:374](../../../src/api/app.py#L374)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.get`（[app.py:369](../../../src/api/app.py#L369)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`FileNotFoundError`。


---

# create_app.provider_requests ⭐⭐⭐

**位置与等级**：[app.py:377](../../../src/api/app.py#L377)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def provider_requests(run_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/runs/{run_id}/provider-requests`。

**作用**：处理 `provider_requests` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 FileNotFoundError；另检查 finally/else 的清理和传播。
2. 返回 `{'requests': service.executions.repository.requests(run_id), 'reconciliations': [item.model_dump(mode='j…`。

**调用与被调用**：
- `service.show_run`（[app.py:379](../../../src/api/app.py#L379)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:381](../../../src/api/app.py#L381)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `service.executions.repository.requests`（[app.py:383](../../../src/api/app.py#L383)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item.model_dump`（[app.py:385](../../../src/api/app.py#L385)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.executions.repository.reconciliations`（[app.py:386](../../../src/api/app.py#L386)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.get`（[app.py:376](../../../src/api/app.py#L376)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`FileNotFoundError`。


---

# create_app.reconcile_provider_request ⭐⭐⭐⭐

**位置与等级**：[app.py:391](../../../src/api/app.py#L391)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def reconcile_provider_request(run_id: str, request_id: str, request: RequestReconciliationRequest) -> object`。

**装饰器/路由**：`POST /api/v1/runs/{run_id}/requests/{request_id}/reconcile`。

**作用**：处理 `reconcile_provider_request` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`request_id`（str；幂等请求标识，避免重复动作）；`request`（RequestReconciliationRequest）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `request.request_id != request_id`；按条件分流，else 分支不存在。
2. 捕获 FileNotFoundError, (ExecutionConflict, LegacyCheckpointError)；另检查 finally/else 的清理和传播。

**关键条件与保护**：
- [app.py:394](../../../src/api/app.py#L394)：`request.request_id != request_id`，不满足时跳过本分支。

**调用与被调用**：
- `HTTPException`（[app.py:395](../../../src/api/app.py#L395)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `service.executions.reconcile_request`（[app.py:397](../../../src/api/app.py#L397)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[app.py:401](../../../src/api/app.py#L401)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.post`（[app.py:390](../../../src/api/app.py#L390)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=422, detail=<字符串常量>)`、`HTTPException(status_code=404, detail=<字符串常量>)`、`HTTPException(status_code=409, detail={'code': str(exc)})`。
- 本地捕获：`FileNotFoundError`、`(ExecutionConflict, LegacyCheckpointError)`。


---

# create_app.cancel_run ⭐⭐⭐⭐

**位置与等级**：[app.py:404](../../../src/api/app.py#L404)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def cancel_run(run_id: str, request: CancelRequest) -> object`。

**装饰器/路由**：`POST /api/v1/runs/{run_id}/cancel`。

**作用**：处理 `cancel_run` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`request`（CancelRequest）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 FileNotFoundError, (ExecutionConflict, LegacyCheckpointError)；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.executions.cancel`（[app.py:406](../../../src/api/app.py#L406)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `request.model_dump`（[app.py:406](../../../src/api/app.py#L406)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:408](../../../src/api/app.py#L408)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[app.py:410](../../../src/api/app.py#L410)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.post`（[app.py:403](../../../src/api/app.py#L403)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`、`HTTPException(status_code=409, detail={'code': str(exc)})`。
- 本地捕获：`FileNotFoundError`、`(ExecutionConflict, LegacyCheckpointError)`。


---

# create_app.get_run_claims ⭐⭐⭐⭐

**位置与等级**：[app.py:413](../../../src/api/app.py#L413)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def get_run_claims(run_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/runs/{run_id}/claims`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 FileNotFoundError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.show_run`（[app.py:415](../../../src/api/app.py#L415)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:417](../../../src/api/app.py#L417)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.get`（[app.py:412](../../../src/api/app.py#L412)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`FileNotFoundError`。


---

# create_app.get_evidence ⭐⭐⭐

**位置与等级**：[app.py:420](../../../src/api/app.py#L420)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def get_evidence(evidence_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/evidence/{evidence_id}`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`evidence_id`（str）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 Exception；另检查 finally/else 的清理和传播。

**关键条件与保护**：
- [app.py:425](../../../src/api/app.py#L425)：`graph_evidence is None`，不满足时跳过本分支。

**调用与被调用**：
- `service.evidence_store.get`（[app.py:422](../../../src/api/app.py#L422)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.graph_store.get_evidence`（[app.py:424](../../../src/api/app.py#L424)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:426](../../../src/api/app.py#L426)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.get`（[app.py:419](../../../src/api/app.py#L419)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`Exception`。


---

# create_app.get_evidence_content ⭐⭐⭐

**位置与等级**：[app.py:430](../../../src/api/app.py#L430)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def get_evidence_content(evidence_id: str) -> Response`。

**装饰器/路由**：`GET /api/v1/evidence/{evidence_id}/content`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`evidence_id`（str）。
- 输出类型：`Response`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 Exception；另检查 finally/else 的清理和传播。
2. 返回 `Response(content=content, media_type='application/octet-stream')`。

**调用与被调用**：
- `service.evidence_store.crop`（[app.py:432](../../../src/api/app.py#L432)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:434](../../../src/api/app.py#L434)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `Response`（[app.py:435](../../../src/api/app.py#L435)）：来自 `fastapi.responses.Response`；具体实现可能由依赖注入或运行时分派决定。
- `api.get`（[app.py:429](../../../src/api/app.py#L429)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`Exception`。


---

# create_app.submit_review ⭐⭐⭐⭐

**位置与等级**：[app.py:438](../../../src/api/app.py#L438)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def submit_review(task_id: str, request: ReviewRequest) -> object`。

**装饰器/路由**：`POST /api/v1/reviews/{task_id}`。

**作用**：处理 `submit_review` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`task_id`（str；待处理审核任务标识）；`request`（ReviewRequest）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 KeyError, (ValueError, LegacyCheckpointError, ProviderConfigurat…；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.runs.find_review`（[app.py:440](../../../src/api/app.py#L440)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.review`（[app.py:441](../../../src/api/app.py#L441)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:451](../../../src/api/app.py#L451)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[app.py:451](../../../src/api/app.py#L451)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.post`（[app.py:437](../../../src/api/app.py#L437)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=str(exc))`、`HTTPException(status_code=409, detail=str(exc))`。
- 本地捕获：`KeyError`、`(ValueError, LegacyCheckpointError, ProviderConfigurationError, Timeout)`。


---

# create_app.review_events ⭐⭐⭐⭐

**位置与等级**：[app.py:456](../../../src/api/app.py#L456)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def review_events(run_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/runs/{run_id}/review-events`。

**作用**：处理 `review_events` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 FileNotFoundError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.show_run`（[app.py:458](../../../src/api/app.py#L458)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.reviews.repository.events`（[app.py:459](../../../src/api/app.py#L459)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:461](../../../src/api/app.py#L461)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.get`（[app.py:455](../../../src/api/app.py#L455)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`FileNotFoundError`。


---

# create_app.propose_review_correction ⭐⭐⭐⭐

**位置与等级**：[app.py:464](../../../src/api/app.py#L464)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def propose_review_correction(run_id: str, request: CorrectionRequest) -> object`。

**装饰器/路由**：`POST /api/v1/runs/{run_id}/review-corrections`。

**作用**：处理 `propose_review_correction` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`request`（CorrectionRequest）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 (ValueError, LegacyCheckpointError, GraphIntegrityErro…, (KeyError, FileNotFoundError)；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.corrections.propose`（[app.py:466](../../../src/api/app.py#L466)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `request.model_dump`（[app.py:466](../../../src/api/app.py#L466)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:468](../../../src/api/app.py#L468)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[app.py:468](../../../src/api/app.py#L468)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.post`（[app.py:463](../../../src/api/app.py#L463)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=409, detail=str(exc))`、`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`(ValueError, LegacyCheckpointError, GraphIntegrityError, Timeout)`、`(KeyError, FileNotFoundError)`。


---

# create_app.get_review_correction ⭐⭐⭐⭐

**位置与等级**：[app.py:473](../../../src/api/app.py#L473)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def get_review_correction(correction_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/review-corrections/{correction_id}`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`correction_id`（str）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 KeyError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.reviews.repository.correction`（[app.py:475](../../../src/api/app.py#L475)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:477](../../../src/api/app.py#L477)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `api.get`（[app.py:472](../../../src/api/app.py#L472)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`KeyError`。


---

# create_app.apply_review_correction ⭐⭐⭐⭐

**位置与等级**：[app.py:480](../../../src/api/app.py#L480)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def apply_review_correction(correction_id: str, request: RollbackRequest) -> object`。

**装饰器/路由**：`POST /api/v1/review-corrections/{correction_id}/apply`。

**作用**：处理 `apply_review_correction` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`correction_id`（str）；`request`（RollbackRequest）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 (ValueError, LegacyCheckpointError, GraphIntegrityErro…, (KeyError, FileNotFoundError)；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.corrections.apply`（[app.py:482](../../../src/api/app.py#L482)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:484](../../../src/api/app.py#L484)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[app.py:484](../../../src/api/app.py#L484)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.post`（[app.py:479](../../../src/api/app.py#L479)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=409, detail=str(exc))`、`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：`(ValueError, LegacyCheckpointError, GraphIntegrityError, Timeout)`、`(KeyError, FileNotFoundError)`。


---

# create_app.search_entities ⭐⭐⭐

**位置与等级**：[app.py:489](../../../src/api/app.py#L489)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def search_entities(q: str=Query(min_length=1), entity_type: str=Query(min_length=1), limit: int=Query(default=10, ge=1, le=100)) -> object`。

**装饰器/路由**：`GET /api/v1/entities/search`。

**作用**：处理 `search_entities` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`q`（str；默认 `Query(min_length=1)`）；`entity_type`（str；默认 `Query(min_length=1)`）；`limit`（int；默认 `Query(default=10, ge=1, le=100)`；查询或展示的最大条数）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await service.search_entities(q, entity_type, limit)`。

**调用与被调用**：
- `Query`（[app.py:490](../../../src/api/app.py#L490)）：来自 `fastapi.Query`；具体实现可能由依赖注入或运行时分派决定。
- `service.search_entities`（[app.py:494](../../../src/api/app.py#L494)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.get`（[app.py:488](../../../src/api/app.py#L488)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# create_app.list_entity_reviews ⭐⭐⭐⭐

**位置与等级**：[app.py:497](../../../src/api/app.py#L497)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def list_entity_reviews(review_status: str | None=Query(default=None, alias='status')) -> object`。

**装饰器/路由**：`GET /api/v1/entity-reviews`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`review_status`（str | None；默认 `Query(default=None, alias='status')`）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `review_status not in {None, 'pending', 'resolved'}`；按条件分流，else 分支不存在。
2. 返回 `service.list_entity_reviews(review_status)`。

**关键条件与保护**：
- [app.py:500](../../../src/api/app.py#L500)：`review_status not in {None, 'pending', 'resolved'}`，不满足时跳过本分支。

**调用与被调用**：
- `Query`（[app.py:498](../../../src/api/app.py#L498)）：来自 `fastapi.Query`；具体实现可能由依赖注入或运行时分派决定。
- `HTTPException`（[app.py:501](../../../src/api/app.py#L501)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `service.list_entity_reviews`（[app.py:502](../../../src/api/app.py#L502)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.get`（[app.py:496](../../../src/api/app.py#L496)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=422, detail=<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# create_app.submit_entity_review ⭐⭐⭐⭐

**位置与等级**：[app.py:505](../../../src/api/app.py#L505)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def submit_entity_review(task_id: str, request: EntityReviewRequest) -> object`。

**装饰器/路由**：`POST /api/v1/entity-reviews/{task_id}`。

**作用**：处理 `submit_entity_review` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`task_id`（str；待处理审核任务标识）；`request`（EntityReviewRequest）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 KeyError, (ValueError, GraphIntegrityError, ProviderConfiguratio…；另检查 finally/else 的清理和传播。

**关键条件与保护**：
- [app.py:507](../../../src/api/app.py#L507)：`request.action in {'approve', 'reject'} and request.run_id is None`，不满足时跳过本分支。
- [app.py:513](../../../src/api/app.py#L513)：`request.run_id is None or request.action not in {'link', 'create', 'reject', 'defer'}`，不满足时跳过本分支。

**调用与被调用**：
- `service.review_entity_operation`（[app.py:508](../../../src/api/app.py#L508)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:519](../../../src/api/app.py#L519)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `service.review_entity`（[app.py:523](../../../src/api/app.py#L523)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `cast`（[app.py:526](../../../src/api/app.py#L526)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[app.py:534](../../../src/api/app.py#L534)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.post`（[app.py:504](../../../src/api/app.py#L504)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=422, detail=<字符串常量>)`、`HTTPException(status_code=404, detail=str(exc))`、`HTTPException(status_code=409, detail=str(exc))`。
- 本地捕获：`KeyError`、`(ValueError, GraphIntegrityError, ProviderConfigurationError, LegacyCheckpointError, Timeout)`。


---

# create_app.propose_entity_merge ⭐⭐⭐

**位置与等级**：[app.py:545](../../../src/api/app.py#L545)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def propose_entity_merge(request: MergeProposalRequest) -> object`。

**装饰器/路由**：`POST /api/v1/entities/merge-proposals`。

**作用**：处理 `propose_entity_merge` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`request`（MergeProposalRequest）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 KeyError, ValueError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.propose_entity_merge`（[app.py:547](../../../src/api/app.py#L547)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:551](../../../src/api/app.py#L551)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[app.py:551](../../../src/api/app.py#L551)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.post`（[app.py:544](../../../src/api/app.py#L544)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=str(exc))`、`HTTPException(status_code=422, detail=str(exc))`。
- 本地捕获：`KeyError`、`ValueError`。


---

# create_app.propose_entity_split ⭐⭐⭐

**位置与等级**：[app.py:556](../../../src/api/app.py#L556)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def propose_entity_split(entity_id: str, request: SplitProposalRequest) -> object`。

**装饰器/路由**：`POST /api/v1/entities/{entity_id}/split-proposals`。

**作用**：处理 `propose_entity_split` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：`entity_id`（str）；`request`（SplitProposalRequest）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 KeyError, ValueError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.propose_entity_split`（[app.py:558](../../../src/api/app.py#L558)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:565](../../../src/api/app.py#L565)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[app.py:565](../../../src/api/app.py#L565)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.post`（[app.py:555](../../../src/api/app.py#L555)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=str(exc))`、`HTTPException(status_code=422, detail=str(exc))`。
- 本地捕获：`KeyError`、`ValueError`。


---

# create_app.get_entity_history ⭐⭐⭐

**位置与等级**：[app.py:570](../../../src/api/app.py#L570)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def get_entity_history(entity_id: str) -> object`。

**装饰器/路由**：`GET /api/v1/entities/{entity_id}/history`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`entity_id`（str）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `await service.graph_store.get_entity(entity_id) is None`；按条件分流，else 分支不存在。
2. 返回 `await service.entity_history(entity_id)`。

**关键条件与保护**：
- [app.py:571](../../../src/api/app.py#L571)：`await service.graph_store.get_entity(entity_id) is None`，不满足时跳过本分支。

**调用与被调用**：
- `service.graph_store.get_entity`（[app.py:571](../../../src/api/app.py#L571)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:572](../../../src/api/app.py#L572)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `service.entity_history`（[app.py:573](../../../src/api/app.py#L573)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.get`（[app.py:569](../../../src/api/app.py#L569)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# create_app.get_neighborhood ⭐⭐⭐

**位置与等级**：[app.py:576](../../../src/api/app.py#L576)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def get_neighborhood(entity_id: str, depth: int=Query(default=1, ge=1, le=3)) -> object`。

**装饰器/路由**：`GET /api/v1/entities/{entity_id}/neighborhood`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`entity_id`（str）；`depth`（int；默认 `Query(default=1, ge=1, le=3)`）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 KeyError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `Query`（[app.py:576](../../../src/api/app.py#L576)）：来自 `fastapi.Query`；具体实现可能由依赖注入或运行时分派决定。
- `service.graph_store.get_neighborhood`（[app.py:578](../../../src/api/app.py#L578)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:580](../../../src/api/app.py#L580)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[app.py:580](../../../src/api/app.py#L580)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.get`（[app.py:575](../../../src/api/app.py#L575)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=str(exc))`。
- 本地捕获：`KeyError`。


---

# create_app.list_revisions ⭐⭐⭐

**位置与等级**：[app.py:583](../../../src/api/app.py#L583)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def list_revisions(limit: int=Query(default=50, ge=1, le=500)) -> object`。

**装饰器/路由**：`GET /api/v1/revisions`。

**作用**：读取或组装对应资源；是否纯只读及异常行为需结合下方显式调用与状态写入判断。

**输入与输出**：
- 输入：`limit`（int；默认 `Query(default=50, ge=1, le=500)`；查询或展示的最大条数）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await service.graph_store.list_revisions(limit)`。

**调用与被调用**：
- `Query`（[app.py:583](../../../src/api/app.py#L583)）：来自 `fastapi.Query`；具体实现可能由依赖注入或运行时分派决定。
- `service.graph_store.list_revisions`（[app.py:584](../../../src/api/app.py#L584)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.get`（[app.py:582](../../../src/api/app.py#L582)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# create_app.diff_revisions ⭐⭐⭐

**位置与等级**：[app.py:587](../../../src/api/app.py#L587)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def diff_revisions(from_id: str=Query(alias='from'), to_id: str=Query(alias='to')) -> object`。

**装饰器/路由**：`GET /api/v1/revisions/diff`。

**作用**：比较两个版本间的资源变化，不修改图谱。

**输入与输出**：
- 输入：`from_id`（str；默认 `Query(alias='from')`）；`to_id`（str；默认 `Query(alias='to')`）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 KeyError, ValueError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `Query`（[app.py:588](../../../src/api/app.py#L588)）：来自 `fastapi.Query`；具体实现可能由依赖注入或运行时分派决定。
- `service.graph_store.diff_revisions`（[app.py:591](../../../src/api/app.py#L591)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:593](../../../src/api/app.py#L593)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[app.py:593](../../../src/api/app.py#L593)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.get`（[app.py:586](../../../src/api/app.py#L586)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=str(exc))`、`HTTPException(status_code=422, detail=str(exc))`。
- 本地捕获：`KeyError`、`ValueError`。


---

# create_app.rollback_revision ⭐⭐⭐

**位置与等级**：[app.py:598](../../../src/api/app.py#L598)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def rollback_revision(revision_id: str, _: RollbackRequest) -> object`。

**装饰器/路由**：`POST /api/v1/revisions/{revision_id}/rollback`。

**作用**：构造补偿版本恢复目标状态，保留历史记录而不是删除 Revision。

**输入与输出**：
- 输入：`revision_id`（str）；`_`（RollbackRequest）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 KeyError, GraphIntegrityError；另检查 finally/else 的清理和传播。
2. 调用 `service.audit.record`，结果未直接赋值。
3. 返回 `revision`。

**调用与被调用**：
- `service.graph_store.rollback_revision`（[app.py:600](../../../src/api/app.py#L600)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `HTTPException`（[app.py:602](../../../src/api/app.py#L602)）：来自 `fastapi.HTTPException`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[app.py:602](../../../src/api/app.py#L602)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.audit.record`（[app.py:605](../../../src/api/app.py#L605)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.post`（[app.py:597](../../../src/api/app.py#L597)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`HTTPException(status_code=404, detail=str(exc))`、`HTTPException(status_code=409, detail=str(exc))`。
- 本地捕获：`KeyError`、`GraphIntegrityError`。


---

# create_app.health ⭐⭐⭐

**位置与等级**：[app.py:609](../../../src/api/app.py#L609)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**签名**：`async def health() -> object`。

**装饰器/路由**：`GET /api/v1/health`。

**作用**：处理 `health` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `graph`，值来自 `await service.graph_store.healthcheck()`。
2. 返回 `{'status': 'ok' if graph.healthy else 'degraded', 'graph': graph, 'execution': service.executions.health…`。

**调用与被调用**：
- `service.graph_store.healthcheck`（[app.py:610](../../../src/api/app.py#L610)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.executions.health`（[app.py:614](../../../src/api/app.py#L614)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `api.get`（[app.py:608](../../../src/api/app.py#L608)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
