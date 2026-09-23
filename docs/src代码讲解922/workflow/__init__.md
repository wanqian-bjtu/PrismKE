源码：[__init__.py:1](../../../src/workflow/__init__.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：0

**模块职责**：PrismKE application workflow.
**在系统中的位置**：应用服务、LangGraph 编排、执行状态、审核接续、图提交及纠正流程。
**直接依赖**：[src.workflow.graph](graph.md)、[src.workflow.service](service.md)；外部/标准库：无。
**主要调用方（静态导入）**：[api/app.py](../api/app.md)、[cli.py](../cli.md)、[evaluation/document_validation.py](../evaluation/document_validation.md)、[evaluation/reflection.py](../evaluation/reflection.md)、[evaluation/runner.py](../evaluation/runner.md)、[workflow/graph.py](graph.md)、[workflow/nodes.py](nodes.md)、[workflow/reflection.py](reflection.md)、[workflow/review_workspace.py](review_workspace.md)、[workflow/service.py](service.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# 模块导出与初始化 ⭐

**重要性**：包适配或常量导出；本文件未定义类或函数。

**行为**：阅读 [__init__.py:1](../../../src/workflow/__init__.py#L1) 中的导入、`__all__` 与模块级赋值；导入该模块时模块级语句仍会执行。
