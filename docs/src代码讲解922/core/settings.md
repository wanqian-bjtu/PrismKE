源码：[settings.py:1](../../../src/core/settings.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：12

**模块职责**：Environment-backed application settings.
**在系统中的位置**：全局设置、稳定标识、执行控制与错误类型；为其他层提供通用约束。
**直接依赖**：无显式项目内模块导入；外部/标准库：`pathlib`、`pydantic_settings`。
**主要调用方（静态导入）**：[api/app.py](../api/app.md)、[cli.py](../cli.md)、[evaluation/document_validation.py](../evaluation/document_validation.md)、[evaluation/reflection.py](../evaluation/reflection.md)、[persistence/runtime_config.py](../persistence/runtime_config.md)、[workflow/service.py](../workflow/service.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# Settings ⭐⭐⭐

**位置与等级**：[settings.py:8](../../../src/core/settings.py#L8)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：`BaseSettings`。
**源码说明**：Runtime configuration with a PrismKE-specific environment prefix.

**字段与类级约束**：
- `model_config`：类级默认或常量，取值由 `SettingsConfigDict(env_file='.env', env_prefix='PRISMKE_', extra='ignore')` 决定。
- `llm_base_url`：`str`；默认 `'https://api.openai.com/v1'`。
- `llm_api_key`：`str | None`；默认 `None`。
- `llm_model`：`str | None`；默认 `None`。
- `vlm_base_url`：`str`；默认 `'https://api.openai.com/v1'`。
- `vlm_api_key`：`str | None`；默认 `None`。
- `vlm_model`：`str | None`；默认 `None`。
- `vlm_timeout`：`float`；默认 `120.0`。
- `vlm_max_image_edge`：`int`；默认 `2048`。
- `ocr_device`：`str`；默认 `'cpu'`。
- `ocr_lang`：`str`；默认 `'ch'`。
- `ocr_model`：`str`；默认 `'PP-OCRv5'`。
- `allow_remote_assets`：`bool`；默认 `False`。
- `runtime_dir`：`Path`；默认 `Path('runtime')`。
- `request_timeout`：`float`；默认 `60.0`。
- `graph_store`：`str`；默认 `'json'`。
- `neo4j_uri`：`str`；默认 `'bolt://127.0.0.1:7687'`。
- `neo4j_user`：`str`；默认 `'neo4j'`。
- `neo4j_password`：`str | None`；默认 `None`。
- `neo4j_database`：`str`；默认 `'neo4j'`。
- `api_token`：`str | None`；默认 `None`。
- `api_host`：`str`；默认 `'127.0.0.1'`。
- `api_port`：`int`；默认 `8000`。
- `embedding_provider`：`str`；默认 `'disabled'`。
- `embedding_model`：`str`；默认 `'BAAI/bge-m3'`。
- `embedding_model_revision`：`str`；默认 `'5617a9f61b028005a4858fdac845db406aefb181'`。
- `embedding_device`：`str`；默认 `'cuda:0'`。
- `embedding_use_fp16`：`bool`；默认 `True`。
- `embedding_batch_size`：`int`；默认 `32`。
- `embedding_max_tokens`：`int`；默认 `512`。
- `embedding_model_cache`：`Path | None`；默认 `None`。
- `embedding_allow_download`：`bool`；默认 `False`。
- `entity_top_k`：`int`；默认 `10`。
- `entity_auto_link_threshold`：`float`；默认 `0.88`。
- `entity_review_threshold`：`float`；默认 `0.65`。

**内部成员**：`Settings.runs_dir`、`Settings.graph_dir`、`Settings.evidence_dir`、`Settings.assets_dir`、`Settings.checkpoint_path`、`Settings.uploads_dir`、`Settings.audit_path`、`Settings.embedding_cache_dir`、`Settings.embedding_model_cache_dir`、`Settings.entity_governance_path`、`Settings.cases_path`


---

# Settings.runs_dir ⭐⭐⭐⭐

**位置与等级**：[settings.py:56](../../../src/core/settings.py#L56)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def runs_dir(self) -> Path`。

**装饰器/路由**：`property`。

**作用**：处理 `runs_dir` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.runtime_dir / 'runs'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# Settings.graph_dir ⭐⭐

**位置与等级**：[settings.py:60](../../../src/core/settings.py#L60)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def graph_dir(self) -> Path`。

**装饰器/路由**：`property`。

**作用**：处理 `graph_dir` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.runtime_dir / 'graph'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# Settings.evidence_dir ⭐⭐

**位置与等级**：[settings.py:64](../../../src/core/settings.py#L64)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def evidence_dir(self) -> Path`。

**装饰器/路由**：`property`。

**作用**：处理 `evidence_dir` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.runtime_dir / 'evidence'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# Settings.assets_dir ⭐⭐

**位置与等级**：[settings.py:68](../../../src/core/settings.py#L68)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def assets_dir(self) -> Path`。

**装饰器/路由**：`property`。

**作用**：处理 `assets_dir` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.runtime_dir / 'assets'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# Settings.checkpoint_path ⭐⭐

**位置与等级**：[settings.py:72](../../../src/core/settings.py#L72)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def checkpoint_path(self) -> Path`。

**装饰器/路由**：`property`。

**作用**：处理 `checkpoint_path` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.runtime_dir / 'checkpoints.sqlite3'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# Settings.uploads_dir ⭐⭐

**位置与等级**：[settings.py:76](../../../src/core/settings.py#L76)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def uploads_dir(self) -> Path`。

**装饰器/路由**：`property`。

**作用**：处理 `uploads_dir` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.runtime_dir / 'uploads'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# Settings.audit_path ⭐⭐

**位置与等级**：[settings.py:80](../../../src/core/settings.py#L80)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def audit_path(self) -> Path`。

**装饰器/路由**：`property`。

**作用**：处理 `audit_path` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.runtime_dir / 'audit.jsonl'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# Settings.embedding_cache_dir ⭐⭐

**位置与等级**：[settings.py:84](../../../src/core/settings.py#L84)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def embedding_cache_dir(self) -> Path`。

**装饰器/路由**：`property`。

**作用**：处理 `embedding_cache_dir` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.runtime_dir / 'embeddings'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# Settings.embedding_model_cache_dir ⭐⭐

**位置与等级**：[settings.py:88](../../../src/core/settings.py#L88)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def embedding_model_cache_dir(self) -> Path`。

**装饰器/路由**：`property`。

**作用**：处理 `embedding_model_cache_dir` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.embedding_model_cache or self.runtime_dir / 'models' / 'huggingface'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# Settings.entity_governance_path ⭐⭐

**位置与等级**：[settings.py:92](../../../src/core/settings.py#L92)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def entity_governance_path(self) -> Path`。

**装饰器/路由**：`property`。

**作用**：处理 `entity_governance_path` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.runtime_dir / 'entity-governance.json'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# Settings.cases_path ⭐⭐

**位置与等级**：[settings.py:96](../../../src/core/settings.py#L96)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def cases_path(self) -> Path`。

**装饰器/路由**：`property`。

**作用**：处理 `cases_path` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`Path`；具体返回路径见流程步骤。

**处理流程**：
1. 返回 `self.runtime_dir / 'cases.sqlite'`。

**调用与被调用**：
- 无显式函数调用，或仅声明协议/常量。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
