源码：[cli.py:1](../../src/cli.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：37

**模块职责**：PrismKE command-line interface.
**在系统中的位置**：顶层入口或包元数据。
**直接依赖**：[src](__init__.md)、[src.core.errors](core/errors.md)、[src.core.settings](core/settings.md)、[src.domain](domain/__init__.md)、[src.evaluation](evaluation/__init__.md)、[src.evaluation.annotations](evaluation/annotations.md)、[src.governance](governance/__init__.md)、[src.persistence](persistence/__init__.md)、[src.persistence.legacy_evidence](persistence/legacy_evidence.md)、[src.providers](providers/__init__.md)、[src.providers.base](providers/base.md)、[src.workflow](workflow/__init__.md)；外部/标准库：`__future__`、`asyncio`、`orjson`、`pathlib`、`pydantic`、`rich`、`typer`、`typing`、`uuid`。
**主要调用方（静态导入）**：[__main__.py](__main__.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# version ⭐⭐

**位置与等级**：[cli.py:46](../../src/cli.py#L46)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def version() -> None`。

**装饰器/路由**：`app.command`。

**作用**：Show the software version (independent of checkpoint protocol).

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `console.print`，结果未直接赋值。

**调用与被调用**：
- `console.print`（[cli.py:48](../../src/cli.py#L48)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `app.command`（[cli.py:45](../../src/cli.py#L45)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# _print_model ⭐⭐

**位置与等级**：[cli.py:51](../../src/cli.py#L51)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def _print_model(model: object) -> None`。

**作用**：内部辅助步骤；将参数转换为本模块所需的中间对象或操作结果。

**输入与输出**：
- 输入：`model`（object）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `isinstance(model, BaseModel)`；按条件分流，else 分支不存在。
2. 调用 `console.print_json`，结果未直接赋值。

**关键条件与保护**：
- [cli.py:52](../../src/cli.py#L52)：`isinstance(model, BaseModel)`，不满足时跳过本分支。

**调用与被调用**：
- `isinstance`（[cli.py:52](../../src/cli.py#L52)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `model.model_dump`（[cli.py:53](../../src/cli.py#L53)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `console.print_json`（[cli.py:54](../../src/cli.py#L54)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.dumps(model).decode`（[cli.py:54](../../src/cli.py#L54)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `orjson.dumps`（[cli.py:54](../../src/cli.py#L54)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- 静态可定位的调用方：[validate_run](cli.md)、[repair_legacy_evidence](cli.md)、[run](cli.md)、[show_run](cli.md)、[agent_traces](cli.md)、[list_cases_command](cli.md)、[disable_case_command](cli.md)、[rebuild_case_index_command](cli.md)、[execution_status](cli.md)、[cancel_execution](cli.md)。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# validate_schema ⭐⭐⭐⭐

**位置与等级**：[cli.py:58](../../src/cli.py#L58)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def validate_schema(schema: Annotated[Path, typer.Argument(exists=True, dir_okay=False)]) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Validate and summarize a YAML or JSON schema.

**输入与输出**：
- 输入：`schema`（Annotated[Path, typer.Argument(exists=True, dir_okay=False)]；当前任务的 Schema 或索引，约束实体与关系）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `parsed`，值来自 `load_schema(schema)`。
2. 调用 `console.print`，结果未直接赋值。

**调用与被调用**：
- `typer.Argument`（[cli.py:59](../../src/cli.py#L59)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `load_schema`（[cli.py:62](../../src/cli.py#L62)）：来自 `src.domain.load_schema`；具体实现可能由依赖注入或运行时分派决定。
- `console.print`（[cli.py:63](../../src/cli.py#L63)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[cli.py:65](../../src/cli.py#L65)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `app.command`（[cli.py:57](../../src/cli.py#L57)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# validate_run ⭐⭐⭐⭐

**位置与等级**：[cli.py:70](../../src/cli.py#L70)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def validate_run(run_id: str) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Read-only validation of a stored run; exit 1 when blocking issues remain.

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `service`，值来自 `PrismKEService()`。
2. 更新 `result`，值来自 `asyncio.run(execute())`。
3. 调用 `_print_model`，结果未直接赋值。
4. 检查 `getattr(result, 'blocking_count', 0)`；按条件分流，else 分支不存在。

**关键条件与保护**：
- [cli.py:82](../../src/cli.py#L82)：`getattr(result, 'blocking_count', 0)`，不满足时跳过本分支。

**调用与被调用**：
- `PrismKEService`（[cli.py:72](../../src/cli.py#L72)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `asyncio.run`（[cli.py:80](../../src/cli.py#L80)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `execute`（[cli.py:80](../../src/cli.py#L80)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_print_model`（调用点 [cli.py:81](../../src/cli.py#L81)）→ [_print_model](cli.md)，静态可定位。
- `getattr`（[cli.py:82](../../src/cli.py#L82)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `typer.Exit`（[cli.py:83](../../src/cli.py#L83)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `app.command`（[cli.py:69](../../src/cli.py#L69)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`typer.Exit(1)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# validate_run.execute ⭐⭐⭐⭐

**位置与等级**：[cli.py:74](../../src/cli.py#L74)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def execute() -> object`。

**作用**：处理 `execute` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 无显式捕获；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.validate_run`（[cli.py:76](../../src/cli.py#L76)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.close`（[cli.py:78](../../src/cli.py#L78)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# repair_legacy_evidence ⭐⭐

**位置与等级**：[cli.py:87](../../src/cli.py#L87)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def repair_legacy_evidence(source_evidence: Annotated[Path, typer.Option('--source-evidence', exists=True, file_okay=False)], target_evidence: Annotated[Path, typer.Option('--target-evidence', file_okay=False)], expected_data_dir: Annotated[Path, typer.Option('--expected-data-dir', exists=True, file_okay=False)], manifest: Annotated[Path | None, typer.Option('--manifest', exists=True, dir_okay=False)]=None, apply: Annotated[bool, typer.Option('--apply')]=False) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Preview or apply the audited legacy-test closure on an isolated Neo4j clone.

**输入与输出**：
- 输入：`source_evidence`（Annotated[Path, typer.Option('--source-evidence', exists=True, file_okay=False)]）；`target_evidence`（Annotated[Path, typer.Option('--target-evidence', file_okay=False)]）；`expected_data_dir`（Annotated[Path, typer.Option('--expected-data-dir', exists=True, file_okay=False)]）；`manifest`（Annotated[Path | None, typer.Option('--manifest', exists=True, dir_okay=False)]；默认 `None`）；`apply`（Annotated[bool, typer.Option('--apply')]；默认 `False`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `settings`，值来自 `Settings()`。
2. 更新 `canary_root`，值来自 `(Path.cwd() / 'runtime/canary-v092').resolve()`。
3. 检查 `settings.neo4j_uri != 'bolt://127.0.0.1:17687' or not expected_data_dir.resolve().is_relative_to(canary_…`；按条件分流，else 分支不存在。
4. 更新 `password`，值来自 `settings.neo4j_password`。
5. 检查 `password is None`；按条件分流，else 分支不存在。
6. 调用 `_print_model`，结果未直接赋值。

**关键条件与保护**：
- [cli.py:103](../../src/cli.py#L103)：`settings.neo4j_uri != 'bolt://127.0.0.1:17687' or not expected_data_dir.resolve().is_relative_to(canary_root) or (…`，不满足时跳过本分支。
- [cli.py:112](../../src/cli.py#L112)：`password is None`，不满足时跳过本分支。

**调用与被调用**：
- `typer.Option`（[cli.py:89](../../src/cli.py#L89)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `Settings`（调用点 [cli.py:101](../../src/cli.py#L101)）→ [Settings](core/settings.md)，静态可定位。
- `(Path.cwd() / 'runtime/canary-v092').resolve`（[cli.py:102](../../src/cli.py#L102)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `Path.cwd`（[cli.py:102](../../src/cli.py#L102)）：来自 `pathlib.Path`；具体实现可能由依赖注入或运行时分派决定。
- `expected_data_dir.resolve().is_relative_to`（[cli.py:105](../../src/cli.py#L105)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `expected_data_dir.resolve`（[cli.py:105](../../src/cli.py#L105)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `target_evidence.resolve().is_relative_to`（[cli.py:106](../../src/cli.py#L106)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `target_evidence.resolve`（[cli.py:106](../../src/cli.py#L106)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `source_evidence.resolve`（[cli.py:107](../../src/cli.py#L107)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `typer.BadParameter`（[cli.py:110](../../src/cli.py#L110)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `_print_model`（调用点 [cli.py:168](../../src/cli.py#L168)）→ [_print_model](cli.md)，静态可定位。
- `asyncio.run`（[cli.py:168](../../src/cli.py#L168)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `execute`（[cli.py:168](../../src/cli.py#L168)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `app.command`（[cli.py:86](../../src/cli.py#L86)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`typer.BadParameter(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# repair_legacy_evidence.execute ⭐⭐

**位置与等级**：[cli.py:115](../../src/cli.py#L115)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def execute() -> dict[str, object]`。

**作用**：处理 `execute` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`dict[str, object]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `source`，值来自 `FileEvidenceStore(source_evidence)`。
2. 更新 `store`，值来自 `Neo4jGraphStore(settings.neo4j_uri, settings.neo4j_user, password, settings.neo4j_database)`。
3. 捕获 无显式捕获；另检查 finally/else 的清理和传播。

**关键条件与保护**：
- [cli.py:126](../../src/cli.py#L126)：`previous is not None`，不满足时跳过本分支。
- [cli.py:127](../../src/cli.py#L127)：`not apply or manifest is None`，不满足时跳过本分支。
- [cli.py:134](../../src/cli.py#L134)：`previous.parent_id != pinned['parent_id'] or sorted(previous.claim_ids) != sorted(expected_ids) or any((claims[cla…`，不满足时跳过本分支。
- [cli.py:147](../../src/cli.py#L147)：`not apply`，不满足时跳过本分支。
- [cli.py:150](../../src/cli.py#L150)：`read_manifest(manifest) != snapshot`，不满足时跳过本分支。

**调用与被调用**：
- `FileEvidenceStore`（[cli.py:116](../../src/cli.py#L116)）：来自 `src.persistence.FileEvidenceStore`；具体实现可能由依赖注入或运行时分派决定。
- `Neo4jGraphStore`（[cli.py:117](../../src/cli.py#L117)）：来自 `src.persistence.Neo4jGraphStore`；具体实现可能由依赖注入或运行时分派决定。
- `require_isolated_database`（调用点 [cli.py:124](../../src/cli.py#L124)）→ [require_isolated_database](persistence/legacy_evidence.md)，静态可定位。
- `existing_maintenance`（调用点 [cli.py:125](../../src/cli.py#L125)）→ [existing_maintenance](persistence/legacy_evidence.md)，静态可定位。
- `ValueError`（[cli.py:128](../../src/cli.py#L128)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `read_manifest`（调用点 [cli.py:131](../../src/cli.py#L131)）→ [read_manifest](persistence/legacy_evidence.md)，静态可定位。
- `store.list_claims`（[cli.py:133](../../src/cli.py#L133)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `sorted`（[cli.py:136](../../src/cli.py#L136)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `any`（[cli.py:137](../../src/cli.py#L137)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `verify_active_claims`（调用点 [cli.py:143](../../src/cli.py#L143)）→ [verify_active_claims](persistence/legacy_evidence.md)，静态可定位。
- `legacy_snapshot`（调用点 [cli.py:146](../../src/cli.py#L146)）→ [legacy_snapshot](persistence/legacy_evidence.md)，静态可定位。
- `restore_sample_evidence`（调用点 [cli.py:153](../../src/cli.py#L153)）→ [restore_sample_evidence](persistence/legacy_evidence.md)，静态可定位。
- `closure_commit`（调用点 [cli.py:156](../../src/cli.py#L156)）→ [closure_commit](persistence/legacy_evidence.md)，静态可定位。
- `store.commit`（[cli.py:158](../../src/cli.py#L158)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[cli.py:162](../../src/cli.py#L162)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `store.close`（[cli.py:166](../../src/cli.py#L166)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`store.evidence_store`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# run ⭐⭐⭐⭐

**位置与等级**：[cli.py:172](../../src/cli.py#L172)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def run(input_path: Annotated[Path, typer.Argument(exists=True, dir_okay=False)], schema: Annotated[Path, typer.Option('--schema', exists=True, dir_okay=False)], provider: Annotated[str, typer.Option('--provider')]='mock', ocr_provider: Annotated[str, typer.Option('--ocr-provider')]='disabled', vlm_provider: Annotated[str, typer.Option('--vlm-provider')]='disabled', allow_remote_assets: Annotated[bool, typer.Option('--allow-remote-assets')]=False, case_mode: Annotated[Literal['none', 'good', 'good_bad'], typer.Option('--cases')]='none', reflection: Annotated[bool, typer.Option('--reflection/--no-reflection')]=False, reflection_provider: Annotated[str, typer.Option('--reflection-provider')]='disabled', reflection_max_attempts: Annotated[int, typer.Option('--reflection-max-attempts')]=2, reflection_token_budget: Annotated[int, typer.Option(<字符串常量>)]=20000, reflection_time_budget: Annotated[int, typer.Option('--reflection-time-budget')]=180, semantic_advisor: Annotated[str, typer.Option('--semantic-advisor')]='disabled', agent_token_budget: Annotated[int, typer.Option(<字符串常量>)]=20000) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Run the complete PrismKE workflow for one document.

**输入与输出**：
- 输入：`input_path`（Annotated[Path, typer.Argument(exists=True, dir_okay=False)]）；`schema`（Annotated[Path, typer.Option('--schema', exists=True, dir_okay=False)]；当前任务的 Schema 或索引，约束实体与关系）；`provider`（Annotated[str, typer.Option('--provider')]；默认 `'mock'`）；`ocr_provider`（Annotated[str, typer.Option('--ocr-provider')]；默认 `'disabled'`）；`vlm_provider`（Annotated[str, typer.Option('--vlm-provider')]；默认 `'disabled'`）；`allow_remote_assets`（Annotated[bool, typer.Option('--allow-remote-assets')]；默认 `False`）；`case_mode`（Annotated[Literal['none', 'good', 'good_bad'], typer.Option('--cases')]；默认 `'none'`）；`reflection`（Annotated[bool, typer.Option('--reflection/--no-reflection')]；默认 `False`）；`reflection_provider`（Annotated[str, typer.Option('--reflection-provider')]；默认 `'disabled'`）；`reflection_max_attempts`（Annotated[int, typer.Option('--reflection-max-attempts')]；默认 `2`）；`reflection_token_budget`（Annotated[int, typer.Option(<字符串常量>)]；默认 `20000`）；`reflection_time_budget`（Annotated[int, typer.Option('--reflection-time-budget')]；默认 `180`）；`semantic_advisor`（Annotated[str, typer.Option('--semantic-advisor')]；默认 `'disabled'`）；`agent_token_budget`（Annotated[int, typer.Option(<字符串常量>)]；默认 `20000`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state`，值来自 `asyncio.run(PrismKEService().run(input_path, schema, provider, ocr_provider, vlm_provider, allow_re…`。
2. 调用 `console.print`，结果未直接赋值。
3. 调用 `_print_model`，结果未直接赋值。

**调用与被调用**：
- `typer.Argument`（[cli.py:173](../../src/cli.py#L173)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `typer.Option`（[cli.py:174](../../src/cli.py#L174)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `asyncio.run`（[cli.py:189](../../src/cli.py#L189)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `PrismKEService().run`（[cli.py:190](../../src/cli.py#L190)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `PrismKEService`（[cli.py:190](../../src/cli.py#L190)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `console.print`（[cli.py:207](../../src/cli.py#L207)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_print_model`（调用点 [cli.py:208](../../src/cli.py#L208)）→ [_print_model](cli.md)，静态可定位。
- `app.command`（[cli.py:171](../../src/cli.py#L171)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# show_run ⭐⭐⭐⭐

**位置与等级**：[cli.py:212](../../src/cli.py#L212)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def show_run(run_id: str) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Print the latest serialized state of a run.

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `_print_model`，结果未直接赋值。

**调用与被调用**：
- `_print_model`（调用点 [cli.py:214](../../src/cli.py#L214)）→ [_print_model](cli.md)，静态可定位。
- `PrismKEService().show_run`（[cli.py:214](../../src/cli.py#L214)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `PrismKEService`（[cli.py:214](../../src/cli.py#L214)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `app.command`（[cli.py:211](../../src/cli.py#L211)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# agent_traces ⭐⭐

**位置与等级**：[cli.py:218](../../src/cli.py#L218)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def agent_traces(run_id: str) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Show the sanitized, idempotent decisions of the three agents.

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `_print_model`，结果未直接赋值。

**调用与被调用**：
- `_print_model`（调用点 [cli.py:220](../../src/cli.py#L220)）→ [_print_model](cli.md)，静态可定位。
- `PrismKEService().show_run`（[cli.py:220](../../src/cli.py#L220)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `PrismKEService`（[cli.py:220](../../src/cli.py#L220)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `app.command`（[cli.py:217](../../src/cli.py#L217)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# list_cases_command ⭐⭐

**位置与等级**：[cli.py:224](../../src/cli.py#L224)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def list_cases_command(case_type: Annotated[str | None, typer.Option('--type')]=None, task_type: Annotated[str | None, typer.Option('--task-type')]=None, language: Annotated[str | None, typer.Option('--language')]=None, include_disabled: Annotated[bool, typer.Option('--include-disabled')]=False, limit: Annotated[int, typer.Option('--limit', min=1, max=1000)]=200) -> None`。

**装饰器/路由**：`app.command`。

**作用**：List immutable review cases without exposing embedding vectors.

**输入与输出**：
- 输入：`case_type`（Annotated[str | None, typer.Option('--type')]；默认 `None`）；`task_type`（Annotated[str | None, typer.Option('--task-type')]；默认 `None`）；`language`（Annotated[str | None, typer.Option('--language')]；默认 `None`）；`include_disabled`（Annotated[bool, typer.Option('--include-disabled')]；默认 `False`）；`limit`（Annotated[int, typer.Option('--limit', min=1, max=1000)]；默认 `200`；查询或展示的最大条数）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `_print_model`，结果未直接赋值。

**调用与被调用**：
- `typer.Option`（[cli.py:225](../../src/cli.py#L225)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `_print_model`（调用点 [cli.py:232](../../src/cli.py#L232)）→ [_print_model](cli.md)，静态可定位。
- `PrismKEService().list_cases`（[cli.py:233](../../src/cli.py#L233)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `PrismKEService`（[cli.py:233](../../src/cli.py#L233)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `app.command`（[cli.py:223](../../src/cli.py#L223)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# disable_case_command ⭐⭐

**位置与等级**：[cli.py:244](../../src/cli.py#L244)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def disable_case_command(case_id: str, operator: Annotated[str, typer.Option('--operator')], reason: Annotated[str, typer.Option('--reason')]) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Append a disabling event; the historical case remains immutable.

**输入与输出**：
- 输入：`case_id`（str）；`operator`（Annotated[str, typer.Option('--operator')]）；`reason`（Annotated[str, typer.Option('--reason')]；人工操作或审核的理由）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `_print_model`，结果未直接赋值。

**调用与被调用**：
- `typer.Option`（[cli.py:246](../../src/cli.py#L246)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `_print_model`（调用点 [cli.py:250](../../src/cli.py#L250)）→ [_print_model](cli.md)，静态可定位。
- `PrismKEService().disable_case`（[cli.py:251](../../src/cli.py#L251)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `PrismKEService`（[cli.py:251](../../src/cli.py#L251)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `uuid4`（[cli.py:255](../../src/cli.py#L255)）：来自 `uuid.uuid4`；具体实现可能由依赖注入或运行时分派决定。
- `app.command`（[cli.py:243](../../src/cli.py#L243)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# rebuild_case_index_command ⭐⭐

**位置与等级**：[cli.py:261](../../src/cli.py#L261)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def rebuild_case_index_command(dry_run: Annotated[bool, typer.Option('--dry-run')]=False) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Rebuild missing or stale case embeddings.

**输入与输出**：
- 输入：`dry_run`（Annotated[bool, typer.Option('--dry-run')]；默认 `False`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `service`，值来自 `PrismKEService()`。
2. 调用 `_print_model`，结果未直接赋值。

**调用与被调用**：
- `typer.Option`（[cli.py:262](../../src/cli.py#L262)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `PrismKEService`（[cli.py:265](../../src/cli.py#L265)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `_print_model`（调用点 [cli.py:273](../../src/cli.py#L273)）→ [_print_model](cli.md)，静态可定位。
- `asyncio.run`（[cli.py:273](../../src/cli.py#L273)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `execute`（[cli.py:273](../../src/cli.py#L273)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `app.command`（[cli.py:260](../../src/cli.py#L260)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# rebuild_case_index_command.execute ⭐⭐

**位置与等级**：[cli.py:267](../../src/cli.py#L267)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def execute() -> object`。

**作用**：处理 `execute` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 无显式捕获；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `service.rebuild_case_index`（[cli.py:269](../../src/cli.py#L269)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.close`（[cli.py:271](../../src/cli.py#L271)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# execution_status ⭐⭐

**位置与等级**：[cli.py:277](../../src/cli.py#L277)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def execution_status(run_id: str) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Read durable task status without starting a worker.

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `_print_model`，结果未直接赋值。

**调用与被调用**：
- `_print_model`（调用点 [cli.py:279](../../src/cli.py#L279)）→ [_print_model](cli.md)，静态可定位。
- `PrismKEService().executions.view`（[cli.py:279](../../src/cli.py#L279)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `PrismKEService`（[cli.py:279](../../src/cli.py#L279)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `app.command`（[cli.py:276](../../src/cli.py#L276)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# cancel_execution ⭐⭐

**位置与等级**：[cli.py:283](../../src/cli.py#L283)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def cancel_execution(run_id: str, operator: Annotated[str, typer.Option('--operator')], reason: Annotated[str, typer.Option('--reason')]) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Persist a cooperative cancellation without taking worker ownership.

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`operator`（Annotated[str, typer.Option('--operator')]）；`reason`（Annotated[str, typer.Option('--reason')]；人工操作或审核的理由）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `service`，值来自 `PrismKEService()`。
2. 更新 `view`，值来自 `service.executions.view(run_id)`。
3. 调用 `_print_model`，结果未直接赋值。

**调用与被调用**：
- `typer.Option`（[cli.py:285](../../src/cli.py#L285)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `PrismKEService`（[cli.py:289](../../src/cli.py#L289)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `service.executions.view`（[cli.py:290](../../src/cli.py#L290)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_print_model`（调用点 [cli.py:291](../../src/cli.py#L291)）→ [_print_model](cli.md)，静态可定位。
- `service.executions.cancel`（[cli.py:291](../../src/cli.py#L291)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `uuid4`（[cli.py:291](../../src/cli.py#L291)）：来自 `uuid.uuid4`；具体实现可能由依赖注入或运行时分派决定。
- `app.command`（[cli.py:282](../../src/cli.py#L282)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# review ⭐⭐⭐⭐

**位置与等级**：[cli.py:295](../../src/cli.py#L295)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def review(run_id: str, claim_id: Annotated[str, typer.Option('--claim-id')], decision: Annotated[ReviewDecision, typer.Option('--decision')], reviewer: Annotated[str | None, typer.Option('--reviewer')]=None, comment: Annotated[str | None, typer.Option('--comment')]=None) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Record a human decision for one claim.

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`claim_id`（Annotated[str, typer.Option('--claim-id')]）；`decision`（Annotated[ReviewDecision, typer.Option('--decision')]）；`reviewer`（Annotated[str | None, typer.Option('--reviewer')]；默认 `None`；审核操作者，形成审计归属）；`comment`（Annotated[str | None, typer.Option('--comment')]；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state`，值来自 `asyncio.run(PrismKEService().review(run_id, claim_id, decision, reviewer, comment))`。
2. 调用 `console.print`，结果未直接赋值。

**调用与被调用**：
- `typer.Option`（[cli.py:297](../../src/cli.py#L297)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `asyncio.run`（[cli.py:303](../../src/cli.py#L303)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `PrismKEService().review`（[cli.py:303](../../src/cli.py#L303)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `PrismKEService`（[cli.py:303](../../src/cli.py#L303)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `console.print`（[cli.py:304](../../src/cli.py#L304)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `app.command`（[cli.py:294](../../src/cli.py#L294)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# review_entity_command ⭐⭐⭐⭐

**位置与等级**：[cli.py:308](../../src/cli.py#L308)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def review_entity_command(run_id: str, task_id: Annotated[str, typer.Option('--task-id')], action: Annotated[str, typer.Option('--action')], reviewer: Annotated[str, typer.Option('--reviewer')], selected_entity_id: Annotated[str | None, typer.Option('--selected-entity-id')]=None, comment: Annotated[str | None, typer.Option('--comment')]=None) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Record a single entity decision; real tasks have no bulk approval command.

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`task_id`（Annotated[str, typer.Option('--task-id')]；待处理审核任务标识）；`action`（Annotated[str, typer.Option('--action')]）；`reviewer`（Annotated[str, typer.Option('--reviewer')]；审核操作者，形成审计归属）；`selected_entity_id`（Annotated[str | None, typer.Option('--selected-entity-id')]；默认 `None`）；`comment`（Annotated[str | None, typer.Option('--comment')]；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `action not in {'link', 'create', 'reject'}`；按条件分流，else 分支不存在。
2. 调用 `_print_model`，结果未直接赋值。

**关键条件与保护**：
- [cli.py:319](../../src/cli.py#L319)：`action not in {'link', 'create', 'reject'}`，不满足时跳过本分支。

**调用与被调用**：
- `typer.Option`（[cli.py:310](../../src/cli.py#L310)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `typer.BadParameter`（[cli.py:320](../../src/cli.py#L320)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `_print_model`（调用点 [cli.py:321](../../src/cli.py#L321)）→ [_print_model](cli.md)，静态可定位。
- `asyncio.run`（[cli.py:322](../../src/cli.py#L322)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `PrismKEService().review_entity`（[cli.py:323](../../src/cli.py#L323)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `PrismKEService`（[cli.py:323](../../src/cli.py#L323)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `cast`（[cli.py:326](../../src/cli.py#L326)）：来自 `typing.cast`；具体实现可能由依赖注入或运行时分派决定。
- `app.command`（[cli.py:307](../../src/cli.py#L307)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`typer.BadParameter(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# review_progress_command ⭐⭐⭐⭐

**位置与等级**：[cli.py:336](../../src/cli.py#L336)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def review_progress_command(run_id: str) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Inspect pending tasks and the isolated graph submission summary.

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 调用 `_print_model`，结果未直接赋值。

**调用与被调用**：
- `_print_model`（调用点 [cli.py:338](../../src/cli.py#L338)）→ [_print_model](cli.md)，静态可定位。
- `PrismKEService().review_progress`（[cli.py:338](../../src/cli.py#L338)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `PrismKEService`（[cli.py:338](../../src/cli.py#L338)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `app.command`（[cli.py:335](../../src/cli.py#L335)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# resume ⭐⭐⭐⭐

**位置与等级**：[cli.py:342](../../src/cli.py#L342)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def resume(run_id: str) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Resume a failed or reviewed run from its latest SQLite snapshot.

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state`，值来自 `asyncio.run(PrismKEService().resume(run_id))`。
2. 调用 `console.print`，结果未直接赋值。
3. 调用 `_print_model`，结果未直接赋值。

**调用与被调用**：
- `asyncio.run`（[cli.py:344](../../src/cli.py#L344)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `PrismKEService().resume`（[cli.py:344](../../src/cli.py#L344)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `PrismKEService`（[cli.py:344](../../src/cli.py#L344)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `console.print`（[cli.py:345](../../src/cli.py#L345)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_print_model`（调用点 [cli.py:346](../../src/cli.py#L346)）→ [_print_model](cli.md)，静态可定位。
- `app.command`（[cli.py:341](../../src/cli.py#L341)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# import_review_run_command ⭐⭐⭐⭐

**位置与等级**：[cli.py:350](../../src/cli.py#L350)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def import_review_run_command(source: Annotated[Path, typer.Option('--source', exists=True, file_okay=False)], run_id: Annotated[str, typer.Option('--run-id')], target: Annotated[Path, typer.Option('--target', file_okay=False)]) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Copy a verified paused extraction into a new offline review workspace.

**输入与输出**：
- 输入：`source`（Annotated[Path, typer.Option('--source', exists=True, file_okay=False)]）；`run_id`（Annotated[str, typer.Option('--run-id')]；目标运行的稳定标识）；`target`（Annotated[Path, typer.Option('--target', file_okay=False)]）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `state`，值来自 `asyncio.run(import_review_run(source, run_id, target))`。
2. 调用 `console.print`，结果未直接赋值。

**调用与被调用**：
- `typer.Option`（[cli.py:351](../../src/cli.py#L351)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `asyncio.run`（[cli.py:358](../../src/cli.py#L358)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `import_review_run`（调用点 [cli.py:358](../../src/cli.py#L358)）→ [import_review_run](workflow/review_workspace.md)，静态可定位。
- `console.print`（[cli.py:359](../../src/cli.py#L359)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `target.resolve`（[cli.py:359](../../src/cli.py#L359)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `app.command`（[cli.py:349](../../src/cli.py#L349)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# confirm_review_commit_command ⭐⭐⭐⭐

**位置与等级**：[cli.py:363](../../src/cli.py#L363)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def confirm_review_commit_command(run_id: str, reviewer: Annotated[str, typer.Option('--reviewer')], confirm: Annotated[bool, typer.Option('--confirm')]=False) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Explicitly confirm an isolated graph commit after viewing its preview.

**输入与输出**：
- 输入：`run_id`（str；目标运行的稳定标识）；`reviewer`（Annotated[str, typer.Option('--reviewer')]；审核操作者，形成审计归属）；`confirm`（Annotated[bool, typer.Option('--confirm')]；默认 `False`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not confirm`；按条件分流，else 分支不存在。
2. 调用 `_print_model`，结果未直接赋值。

**关键条件与保护**：
- [cli.py:369](../../src/cli.py#L369)：`not confirm`，不满足时跳过本分支。

**调用与被调用**：
- `typer.Option`（[cli.py:365](../../src/cli.py#L365)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `typer.BadParameter`（[cli.py:370](../../src/cli.py#L370)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `_print_model`（调用点 [cli.py:371](../../src/cli.py#L371)）→ [_print_model](cli.md)，静态可定位。
- `asyncio.run`（[cli.py:371](../../src/cli.py#L371)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `PrismKEService().confirm_review_commit`（[cli.py:371](../../src/cli.py#L371)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `PrismKEService`（[cli.py:371](../../src/cli.py#L371)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `app.command`（[cli.py:362](../../src/cli.py#L362)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`typer.BadParameter(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# show_evidence ⭐⭐

**位置与等级**：[cli.py:375](../../src/cli.py#L375)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def show_evidence(evidence_id: str) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Print immutable evidence metadata.

**输入与输出**：
- 输入：`evidence_id`（str）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `service`，值来自 `PrismKEService()`。
2. 更新 `evidence`，值来自 `asyncio.run(service.evidence_store.get(evidence_id))`。
3. 调用 `_print_model`，结果未直接赋值。

**调用与被调用**：
- `PrismKEService`（[cli.py:377](../../src/cli.py#L377)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `asyncio.run`（[cli.py:378](../../src/cli.py#L378)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `service.evidence_store.get`（[cli.py:378](../../src/cli.py#L378)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_print_model`（调用点 [cli.py:379](../../src/cli.py#L379)）→ [_print_model](cli.md)，静态可定位。
- `app.command`（[cli.py:374](../../src/cli.py#L374)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# export_evidence ⭐⭐

**位置与等级**：[cli.py:383](../../src/cli.py#L383)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def export_evidence(evidence_id: str, output: Annotated[Path, typer.Option('--output', dir_okay=False)]) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Export an evidence image or region as PNG/binary data.

**输入与输出**：
- 输入：`evidence_id`（str）；`output`（Annotated[Path, typer.Option('--output', dir_okay=False)]）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `service`，值来自 `PrismKEService()`。
2. 更新 `payload`，值来自 `asyncio.run(service.evidence_store.crop(evidence_id))`。
3. 调用 `output.parent.mkdir`，结果未直接赋值。
4. 调用 `output.write_bytes`，结果未直接赋值。
5. 调用 `console.print`，结果未直接赋值。

**调用与被调用**：
- `typer.Option`（[cli.py:385](../../src/cli.py#L385)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `PrismKEService`（[cli.py:388](../../src/cli.py#L388)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `asyncio.run`（[cli.py:389](../../src/cli.py#L389)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `service.evidence_store.crop`（[cli.py:389](../../src/cli.py#L389)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `output.parent.mkdir`（[cli.py:390](../../src/cli.py#L390)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `output.write_bytes`（[cli.py:391](../../src/cli.py#L391)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `console.print`（[cli.py:392](../../src/cli.py#L392)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `output.resolve`（[cli.py:392](../../src/cli.py#L392)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `app.command`（[cli.py:382](../../src/cli.py#L382)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# evaluate ⭐⭐

**位置与等级**：[cli.py:396](../../src/cli.py#L396)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def evaluate(manifest: Annotated[Path, typer.Argument(exists=True, dir_okay=False)], output: Annotated[Path, typer.Option('--output', dir_okay=False)], provider: Annotated[str, typer.Option('--provider')]='mock', ocr_provider: Annotated[str, typer.Option('--ocr-provider')]='disabled', vlm_provider: Annotated[str, typer.Option('--vlm-provider')]='disabled') -> None`。

**装饰器/路由**：`app.command`。

**作用**：Run a reproducible evaluation manifest and write a JSON report.

**输入与输出**：
- 输入：`manifest`（Annotated[Path, typer.Argument(exists=True, dir_okay=False)]）；`output`（Annotated[Path, typer.Option('--output', dir_okay=False)]）；`provider`（Annotated[str, typer.Option('--provider')]；默认 `'mock'`）；`ocr_provider`（Annotated[str, typer.Option('--ocr-provider')]；默认 `'disabled'`）；`vlm_provider`（Annotated[str, typer.Option('--vlm-provider')]；默认 `'disabled'`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `report`，值来自 `asyncio.run(evaluate_manifest(manifest, PrismKEService(), provider_name=provider, ocr_provider_name…`。
2. 调用 `output.parent.mkdir`，结果未直接赋值。
3. 调用 `output.write_bytes`，结果未直接赋值。
4. 调用 `console.print`，结果未直接赋值。

**调用与被调用**：
- `typer.Argument`（[cli.py:397](../../src/cli.py#L397)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `typer.Option`（[cli.py:398](../../src/cli.py#L398)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `asyncio.run`（[cli.py:405](../../src/cli.py#L405)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `evaluate_manifest`（[cli.py:406](../../src/cli.py#L406)）：来自 `src.evaluation.evaluate_manifest`；具体实现可能由依赖注入或运行时分派决定。
- `PrismKEService`（[cli.py:408](../../src/cli.py#L408)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `output.parent.mkdir`（[cli.py:414](../../src/cli.py#L414)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `output.write_bytes`（[cli.py:415](../../src/cli.py#L415)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.dumps`（[cli.py:415](../../src/cli.py#L415)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `report.model_dump`（[cli.py:415](../../src/cli.py#L415)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `console.print`（[cli.py:416](../../src/cli.py#L416)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `output.resolve`（[cli.py:418](../../src/cli.py#L418)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `app.command`（[cli.py:395](../../src/cli.py#L395)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# evaluate_entities ⭐⭐

**位置与等级**：[cli.py:423](../../src/cli.py#L423)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def evaluate_entities(manifest: Annotated[Path, typer.Argument(exists=True, dir_okay=False)], output: Annotated[Path, typer.Option('--output', dir_okay=False)], embedding_provider: Annotated[str | None, typer.Option('--embedding-provider')]=None, protocol: Annotated[str | None, typer.Option('--protocol')]=None) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Evaluate semantic linking, NIL decisions and cross-document clustering.

**输入与输出**：
- 输入：`manifest`（Annotated[Path, typer.Argument(exists=True, dir_okay=False)]）；`output`（Annotated[Path, typer.Option('--output', dir_okay=False)]）；`embedding_provider`（Annotated[str | None, typer.Option('--embedding-provider')]；默认 `None`）；`protocol`（Annotated[str | None, typer.Option('--protocol')]；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `settings`，值来自 `Settings()`。
2. 检查 `embedding_provider is not None`；按条件分流，else 分支不存在。
3. 检查 `protocol not in {None, 'fixed', 'sequential'}`；按条件分流，else 分支不存在。
4. 更新 `provider_instance`，值来自 `声明`。
5. 检查 `settings.embedding_provider == 'mock'`；按条件分流，else 分支存在。
6. 更新 `report`，值来自 `asyncio.run(execute())`。
7. 调用 `output.parent.mkdir`，结果未直接赋值。
8. 调用 `output.write_bytes`，结果未直接赋值。
9. 调用 `_print_model`，结果未直接赋值。

**关键条件与保护**：
- [cli.py:431](../../src/cli.py#L431)：`embedding_provider is not None`，不满足时跳过本分支。
- [cli.py:433](../../src/cli.py#L433)：`protocol not in {None, 'fixed', 'sequential'}`，不满足时跳过本分支。
- [cli.py:436](../../src/cli.py#L436)：`settings.embedding_provider == 'mock'`，不满足时有 else 分支。
- [cli.py:438](../../src/cli.py#L438)：`settings.embedding_provider == 'bge-m3'`，不满足时有 else 分支。

**调用与被调用**：
- `typer.Argument`（[cli.py:424](../../src/cli.py#L424)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `typer.Option`（[cli.py:425](../../src/cli.py#L425)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `Settings`（调用点 [cli.py:430](../../src/cli.py#L430)）→ [Settings](core/settings.md)，静态可定位。
- `typer.BadParameter`（[cli.py:434](../../src/cli.py#L434)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `MockEmbeddingProvider`（[cli.py:437](../../src/cli.py#L437)）：来自 `src.providers.MockEmbeddingProvider`；具体实现可能由依赖注入或运行时分派决定。
- `BGEM3EmbeddingProvider`（[cli.py:439](../../src/cli.py#L439)）：来自 `src.providers.BGEM3EmbeddingProvider`；具体实现可能由依赖注入或运行时分派决定。
- `asyncio.run`（[cli.py:464](../../src/cli.py#L464)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `execute`（[cli.py:464](../../src/cli.py#L464)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `output.parent.mkdir`（[cli.py:465](../../src/cli.py#L465)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `output.write_bytes`（[cli.py:466](../../src/cli.py#L466)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `orjson.dumps`（[cli.py:466](../../src/cli.py#L466)）：来自 `orjson`；具体实现可能由依赖注入或运行时分派决定。
- `report.model_dump`（[cli.py:466](../../src/cli.py#L466)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `_print_model`（调用点 [cli.py:467](../../src/cli.py#L467)）→ [_print_model](cli.md)，静态可定位。
- `app.command`（[cli.py:422](../../src/cli.py#L422)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`settings.embedding_provider`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`typer.BadParameter(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# evaluate_entities.execute ⭐⭐

**位置与等级**：[cli.py:453](../../src/cli.py#L453)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def execute() -> EntityLinkingEvaluationReport`。

**作用**：处理 `execute` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`EntityLinkingEvaluationReport`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `await evaluate_entity_linking_manifest(manifest, provider_instance, top_k=settings.entity_top_k, auto_li…`。

**调用与被调用**：
- `evaluate_entity_linking_manifest`（[cli.py:454](../../src/cli.py#L454)）：来自 `src.evaluation.evaluate_entity_linking_manifest`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# export_entity_annotations ⭐⭐

**位置与等级**：[cli.py:471](../../src/cli.py#L471)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def export_entity_annotations(workbook: Annotated[Path, typer.Argument(exists=True, dir_okay=False)], package: Annotated[Path, typer.Option('--package', exists=True, file_okay=False)], output: Annotated[Path, typer.Option('--output', file_okay=False)]) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Export human-confirmed entity answers without modifying the workbook.

**输入与输出**：
- 输入：`workbook`（Annotated[Path, typer.Argument(exists=True, dir_okay=False)]）；`package`（Annotated[Path, typer.Option('--package', exists=True, file_okay=False)]）；`output`（Annotated[Path, typer.Option('--output', file_okay=False)]）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 ValueError；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `typer.Argument`（[cli.py:472](../../src/cli.py#L472)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `typer.Option`（[cli.py:473](../../src/cli.py#L473)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `_print_model`（调用点 [cli.py:478](../../src/cli.py#L478)）→ [_print_model](cli.md)，静态可定位。
- `export_reviewed_annotations`（调用点 [cli.py:478](../../src/cli.py#L478)）→ [export_reviewed_annotations](evaluation/annotations.md)，静态可定位。
- `typer.BadParameter`（[cli.py:480](../../src/cli.py#L480)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `str`（[cli.py:480](../../src/cli.py#L480)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `app.command`（[cli.py:470](../../src/cli.py#L470)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`typer.BadParameter(str(exc))`。
- 本地捕获：`ValueError`。


---

# validate_real_documents ⭐⭐⭐⭐

**位置与等级**：[cli.py:484](../../src/cli.py#L484)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def validate_real_documents(manifest: Annotated[Path, typer.Argument(exists=True, dir_okay=False)], output: Annotated[Path, typer.Option('--output', file_okay=False)], token_limit: Annotated[int, typer.Option(<字符串常量>)]=100000, stop_at: Annotated[int, typer.Option('--stop-at')]=90000, budget_ledger: Annotated[Path | None, typer.Option('--budget-ledger', exists=True)]=None, extend_budget: Annotated[bool, typer.Option('--extend-budget')]=False) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Run budgeted real-model document validation on an isolated JSON graph.

**输入与输出**：
- 输入：`manifest`（Annotated[Path, typer.Argument(exists=True, dir_okay=False)]）；`output`（Annotated[Path, typer.Option('--output', file_okay=False)]）；`token_limit`（Annotated[int, typer.Option(<字符串常量>)]；默认 `100000`）；`stop_at`（Annotated[int, typer.Option('--stop-at')]；默认 `90000`）；`budget_ledger`（Annotated[Path | None, typer.Option('--budget-ledger', exists=True)]；默认 `None`）；`extend_budget`（Annotated[bool, typer.Option('--extend-budget')]；默认 `False`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not 0 < stop_at < token_limit`；按条件分流，else 分支不存在。
2. 更新 `report`，值来自 `asyncio.run(validate_documents(manifest, Settings(), output, token_limit=token_limit, stop_at=stop_…`。
3. 更新 `finished`，值来自 `sum((case['status'] in {'completed', 'awaiting_review'} for case in report['cases']))`。
4. 调用 `console.print`，结果未直接赋值。

**关键条件与保护**：
- [cli.py:495](../../src/cli.py#L495)：`not 0 < stop_at < token_limit`，不满足时跳过本分支。

**调用与被调用**：
- `typer.Argument`（[cli.py:485](../../src/cli.py#L485)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `typer.Option`（[cli.py:486](../../src/cli.py#L486)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `typer.BadParameter`（[cli.py:496](../../src/cli.py#L496)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `asyncio.run`（[cli.py:497](../../src/cli.py#L497)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `validate_documents`（调用点 [cli.py:498](../../src/cli.py#L498)）→ [validate_documents](evaluation/document_validation.md)，静态可定位。
- `Settings`（调用点 [cli.py:500](../../src/cli.py#L500)）→ [Settings](core/settings.md)，静态可定位。
- `sum`（[cli.py:508](../../src/cli.py#L508)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `console.print`（[cli.py:509](../../src/cli.py#L509)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[cli.py:510](../../src/cli.py#L510)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `app.command`（[cli.py:483](../../src/cli.py#L483)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`typer.BadParameter(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# evaluate_reflection_command ⭐⭐⭐⭐

**位置与等级**：[cli.py:515](../../src/cli.py#L515)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def evaluate_reflection_command(manifest: Annotated[Path, typer.Argument(exists=True, dir_okay=False)], output: Annotated[Path, typer.Option('--output', file_okay=False)], reflection_provider: Annotated[str, typer.Option('--reflection-provider')]='mock', embedding_provider: Annotated[str, typer.Option('--embedding-provider')]='mock', token_limit: Annotated[int, typer.Option(<字符串常量>)]=200000, stop_at: Annotated[int, typer.Option('--stop-at')]=180000) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Run the isolated nine-cell case retrieval and Reflection evaluation.

**输入与输出**：
- 输入：`manifest`（Annotated[Path, typer.Argument(exists=True, dir_okay=False)]）；`output`（Annotated[Path, typer.Option('--output', file_okay=False)]）；`reflection_provider`（Annotated[str, typer.Option('--reflection-provider')]；默认 `'mock'`）；`embedding_provider`（Annotated[str, typer.Option('--embedding-provider')]；默认 `'mock'`）；`token_limit`（Annotated[int, typer.Option(<字符串常量>)]；默认 `200000`）；`stop_at`（Annotated[int, typer.Option('--stop-at')]；默认 `180000`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `not 0 < stop_at < token_limit`；按条件分流，else 分支不存在。
2. 更新 `report`，值来自 `asyncio.run(evaluate_reflection_manifest(manifest, output, reflection_provider_name=reflection_prov…`。
3. 调用 `_print_model`，结果未直接赋值。
4. 调用 `console.print`，结果未直接赋值。

**关键条件与保护**：
- [cli.py:524](../../src/cli.py#L524)：`not 0 < stop_at < token_limit`，不满足时跳过本分支。

**调用与被调用**：
- `typer.Argument`（[cli.py:516](../../src/cli.py#L516)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `typer.Option`（[cli.py:517](../../src/cli.py#L517)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `typer.BadParameter`（[cli.py:525](../../src/cli.py#L525)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `asyncio.run`（[cli.py:526](../../src/cli.py#L526)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `evaluate_reflection_manifest`（[cli.py:527](../../src/cli.py#L527)）：来自 `src.evaluation.evaluate_reflection_manifest`；具体实现可能由依赖注入或运行时分派决定。
- `_print_model`（调用点 [cli.py:536](../../src/cli.py#L536)）→ [_print_model](cli.md)，静态可定位。
- `str`（[cli.py:541](../../src/cli.py#L541)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `console.print`（[cli.py:544](../../src/cli.py#L544)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `app.command`（[cli.py:514](../../src/cli.py#L514)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`typer.BadParameter(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# migrate_graph ⭐⭐

**位置与等级**：[cli.py:548](../../src/cli.py#L548)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def migrate_graph(source: Annotated[Path, typer.Option('--from-json', exists=True, dir_okay=False)], destination: Annotated[str, typer.Option('--to')]='neo4j', dry_run: Annotated[bool, typer.Option('--dry-run')]=False) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Validate or migrate a JSON graph into the configured Neo4j backend.

**输入与输出**：
- 输入：`source`（Annotated[Path, typer.Option('--from-json', exists=True, dir_okay=False)]）；`destination`（Annotated[str, typer.Option('--to')]；默认 `'neo4j'`）；`dry_run`（Annotated[bool, typer.Option('--dry-run')]；默认 `False`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `destination != 'neo4j'`；按条件分流，else 分支不存在。
2. 更新 `settings`，值来自 `Settings()`。
3. 调用 `_print_model`，结果未直接赋值。

**关键条件与保护**：
- [cli.py:554](../../src/cli.py#L554)：`destination != 'neo4j'`，不满足时跳过本分支。

**调用与被调用**：
- `typer.Option`（[cli.py:549](../../src/cli.py#L549)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `typer.BadParameter`（[cli.py:555](../../src/cli.py#L555)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `Settings`（调用点 [cli.py:556](../../src/cli.py#L556)）→ [Settings](core/settings.md)，静态可定位。
- `_print_model`（调用点 [cli.py:578](../../src/cli.py#L578)）→ [_print_model](cli.md)，静态可定位。
- `asyncio.run`（[cli.py:578](../../src/cli.py#L578)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `execute`（[cli.py:578](../../src/cli.py#L578)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `app.command`（[cli.py:547](../../src/cli.py#L547)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`typer.BadParameter(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# migrate_graph.execute ⭐⭐

**位置与等级**：[cli.py:558](../../src/cli.py#L558)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def execute() -> object`。

**作用**：处理 `execute` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `target`，值来自 `None`。
2. 检查 `not dry_run`；按条件分流，else 分支不存在。
3. 更新 `evidence`，值来自 `FileEvidenceStore(source.resolve().parent.parent / 'evidence')`。
4. 捕获 无显式捕获；另检查 finally/else 的清理和传播。

**关键条件与保护**：
- [cli.py:560](../../src/cli.py#L560)：`not dry_run`，不满足时跳过本分支。
- [cli.py:561](../../src/cli.py#L561)：`not settings.neo4j_password`，不满足时跳过本分支。
- [cli.py:575](../../src/cli.py#L575)：`target is not None`，不满足时跳过本分支。

**调用与被调用**：
- `ProviderConfigurationError`（调用点 [cli.py:562](../../src/cli.py#L562)）→ [ProviderConfigurationError](core/errors.md)，静态可定位。
- `Neo4jGraphStore`（[cli.py:563](../../src/cli.py#L563)）：来自 `src.persistence.Neo4jGraphStore`；具体实现可能由依赖注入或运行时分派决定。
- `FileEvidenceStore`（[cli.py:569](../../src/cli.py#L569)）：来自 `src.persistence.FileEvidenceStore`；具体实现可能由依赖注入或运行时分派决定。
- `source.resolve`（[cli.py:569](../../src/cli.py#L569)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `migrate_json_graph`（[cli.py:571](../../src/cli.py#L571)）：来自 `src.persistence.migrate_json_graph`；具体实现可能由依赖注入或运行时分派决定。
- `target.close`（[cli.py:576](../../src/cli.py#L576)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ProviderConfigurationError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# prepare_model ⭐⭐⭐⭐

**位置与等级**：[cli.py:582](../../src/cli.py#L582)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def prepare_model(embedding: Annotated[str, typer.Option('--embedding')]='BAAI/bge-m3') -> None`。

**装饰器/路由**：`app.command`。

**作用**：Download and validate the configured local embedding model.

**输入与输出**：
- 输入：`embedding`（Annotated[str, typer.Option('--embedding')]；默认 `'BAAI/bge-m3'`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `settings`，值来自 `Settings(embedding_provider='bge-m3', embedding_model=embedding, embedding_allow_download=True)`。
2. 调用 `_print_model`，结果未直接赋值。

**调用与被调用**：
- `typer.Option`（[cli.py:583](../../src/cli.py#L583)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `Settings`（调用点 [cli.py:586](../../src/cli.py#L586)）→ [Settings](core/settings.md)，静态可定位。
- `_print_model`（调用点 [cli.py:608](../../src/cli.py#L608)）→ [_print_model](cli.md)，静态可定位。
- `asyncio.run`（[cli.py:608](../../src/cli.py#L608)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `execute`（[cli.py:608](../../src/cli.py#L608)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `app.command`（[cli.py:581](../../src/cli.py#L581)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# prepare_model.execute ⭐⭐⭐⭐

**位置与等级**：[cli.py:592](../../src/cli.py#L592)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`async def execute() -> dict[str, object]`。

**作用**：处理 `execute` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`dict[str, object]`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `service`，值来自 `PrismKEService(settings)`。
2. 捕获 无显式捕获；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `PrismKEService`（[cli.py:593](../../src/cli.py#L593)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `service.embedding_provider().encode`（[cli.py:595](../../src/cli.py#L595)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.embedding_provider`（[cli.py:595](../../src/cli.py#L595)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[cli.py:600](../../src/cli.py#L600)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.embedding_provider().fingerprint`（[cli.py:601](../../src/cli.py#L601)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `len`（[cli.py:602](../../src/cli.py#L602)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.close`（[cli.py:606](../../src/cli.py#L606)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# rebuild_entity_index_command ⭐⭐

**位置与等级**：[cli.py:612](../../src/cli.py#L612)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def rebuild_entity_index_command(backend: Annotated[str, typer.Option('--backend')]='neo4j', batch_size: Annotated[int, typer.Option('--batch-size', min=1)]=32, dry_run: Annotated[bool, typer.Option('--dry-run')]=False) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Build missing or outdated entity vectors without changing graph revisions.

**输入与输出**：
- 输入：`backend`（Annotated[str, typer.Option('--backend')]；默认 `'neo4j'`）；`batch_size`（Annotated[int, typer.Option('--batch-size', min=1)]；默认 `32`）；`dry_run`（Annotated[bool, typer.Option('--dry-run')]；默认 `False`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `backend not in {'json', 'neo4j'}`；按条件分流，else 分支不存在。
2. 更新 `settings`，值来自 `Settings(graph_store=backend)`。
3. 调用 `_print_model`，结果未直接赋值。

**关键条件与保护**：
- [cli.py:618](../../src/cli.py#L618)：`backend not in {'json', 'neo4j'}`，不满足时跳过本分支。

**调用与被调用**：
- `typer.Option`（[cli.py:613](../../src/cli.py#L613)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `typer.BadParameter`（[cli.py:619](../../src/cli.py#L619)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `Settings`（调用点 [cli.py:620](../../src/cli.py#L620)）→ [Settings](core/settings.md)，静态可定位。
- `_print_model`（调用点 [cli.py:635](../../src/cli.py#L635)）→ [_print_model](cli.md)，静态可定位。
- `asyncio.run`（[cli.py:635](../../src/cli.py#L635)）：来自 `asyncio`；具体实现可能由依赖注入或运行时分派决定。
- `execute`（[cli.py:635](../../src/cli.py#L635)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `app.command`（[cli.py:611](../../src/cli.py#L611)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`typer.BadParameter(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# rebuild_entity_index_command.execute ⭐⭐

**位置与等级**：[cli.py:622](../../src/cli.py#L622)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`async def execute() -> object`。

**作用**：处理 `execute` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`object`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `service`，值来自 `PrismKEService(settings)`。
2. 捕获 无显式捕获；另检查 finally/else 的清理和传播。

**调用与被调用**：
- `PrismKEService`（[cli.py:623](../../src/cli.py#L623)）：来自 `src.workflow.PrismKEService`；具体实现可能由依赖注入或运行时分派决定。
- `rebuild_entity_index`（[cli.py:625](../../src/cli.py#L625)）：来自 `src.governance.rebuild_entity_index`；具体实现可能由依赖注入或运行时分派决定。
- `service.embedding_provider`（[cli.py:627](../../src/cli.py#L627)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `service.close`（[cli.py:633](../../src/cli.py#L633)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# serve ⭐⭐

**位置与等级**：[cli.py:639](../../src/cli.py#L639)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def serve(host: Annotated[str | None, typer.Option('--host')]=None, port: Annotated[int | None, typer.Option('--port')]=None) -> None`。

**装饰器/路由**：`app.command`。

**作用**：Start the FastAPI service and mounted Gradio workspace.

**输入与输出**：
- 输入：`host`（Annotated[str | None, typer.Option('--host')]；默认 `None`）；`port`（Annotated[int | None, typer.Option('--port')]；默认 `None`）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 捕获 ImportError；另检查 finally/else 的清理和传播。
2. 更新 `settings`，值来自 `Settings()`。
3. 检查 `host is not None`；按条件分流，else 分支不存在。
4. 检查 `port is not None`；按条件分流，else 分支不存在。
5. 调用 `uvicorn.run`，结果未直接赋值。

**关键条件与保护**：
- [cli.py:651](../../src/cli.py#L651)：`host is not None`，不满足时跳过本分支。
- [cli.py:653](../../src/cli.py#L653)：`port is not None`，不满足时跳过本分支。

**调用与被调用**：
- `typer.Option`（[cli.py:640](../../src/cli.py#L640)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `typer.BadParameter`（[cli.py:649](../../src/cli.py#L649)）：来自 `typer`；具体实现可能由依赖注入或运行时分派决定。
- `Settings`（调用点 [cli.py:650](../../src/cli.py#L650)）→ [Settings](core/settings.md)，静态可定位。
- `uvicorn.run`（[cli.py:655](../../src/cli.py#L655)）：来自 `uvicorn`；具体实现可能由依赖注入或运行时分派决定。
- `create_app`（[cli.py:656](../../src/cli.py#L656)）：来自 `src.api.create_app`；具体实现可能由依赖注入或运行时分派决定。
- `app.command`（[cli.py:638](../../src/cli.py#L638)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：`settings.api_host`、`settings.api_port`。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`typer.BadParameter(<字符串常量>)`。
- 本地捕获：`ImportError`。


---
