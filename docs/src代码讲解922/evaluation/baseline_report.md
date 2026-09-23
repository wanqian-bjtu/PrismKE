源码：[baseline_report.py:1](../../../src/evaluation/baseline_report.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：1

**模块职责**：Human-readable baseline results without copying original document contexts.
**在系统中的位置**：离线评测、预算账本、标注导出及报告；不等于生产工作流。
**直接依赖**：[src.evaluation.entity_linking](entity_linking.md)；外部/标准库：`__future__`、`csv`、`json`、`pathlib`。
**主要调用方（静态导入）**：未见静态直接导入；可能由包入口、框架注册或动态加载。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# write_baseline_report ⭐⭐

**位置与等级**：[baseline_report.py:12](../../../src/evaluation/baseline_report.py#L12)；局部辅助逻辑，需理解其调用条件与失败传播。

**签名**：`def write_baseline_report(reports: list[EntityLinkingEvaluationReport], output: Path) -> None`。

**作用**：创建、更新或记录相应资源；写入/审计边界以实际调用和状态赋值为准。

**输入与输出**：
- 输入：`reports`（list[EntityLinkingEvaluationReport]）；`output`（Path）。
- 输出类型：`None`；具体返回路径见流程步骤。

**处理流程**：
1. 更新 `rows`，值来自 `[<字符串常量>, '', <字符串常量>, <字符串常量>, <字符串常量>, '', <字符串常量>, <字符串常量>]`。
2. 遍历 `reports`，逐项处理 `report`。
3. 更新 `rows`，值来自 `['', <字符串常量>, <字符串常量>, <字符串常量>, '']`。
4. 遍历 `reports`，逐项处理 `report`。
5. 调用 `output.parent.mkdir`，结果未直接赋值。
6. 调用 `output.write_text`，结果未直接赋值。
7. 遍历 `reports`，逐项处理 `report`。

**调用与被调用**：
- `rows.append`（[baseline_report.py:27](../../../src/evaluation/baseline_report.py#L27)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `report.provenance.get`（[baseline_report.py:45](../../../src/evaluation/baseline_report.py#L45)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `report.modality_summary.items`（[baseline_report.py:55](../../../src/evaluation/baseline_report.py#L55)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `item.get`（[baseline_report.py:68](../../../src/evaluation/baseline_report.py#L68)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `evidence.get`（[baseline_report.py:69](../../../src/evaluation/baseline_report.py#L69)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str(item['name']).replace`（[baseline_report.py:70](../../../src/evaluation/baseline_report.py#L70)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `str`（[baseline_report.py:70](../../../src/evaluation/baseline_report.py#L70)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `<字符串常量>.join`（[baseline_report.py:71](../../../src/evaluation/baseline_report.py#L71)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `output.parent.mkdir`（[baseline_report.py:77](../../../src/evaluation/baseline_report.py#L77)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `output.write_text`（[baseline_report.py:78](../../../src/evaluation/baseline_report.py#L78)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `output.with_name(f<字符串常量>).open`（[baseline_report.py:98](../../../src/evaluation/baseline_report.py#L98)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `output.with_name`（[baseline_report.py:98](../../../src/evaluation/baseline_report.py#L98)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `csv.DictWriter`（[baseline_report.py:101](../../../src/evaluation/baseline_report.py#L101)）：来自 `csv`；具体实现可能由依赖注入或运行时分派决定。
- `writer.writeheader`（[baseline_report.py:102](../../../src/evaluation/baseline_report.py#L102)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `writer.writerow`（[baseline_report.py:104](../../../src/evaluation/baseline_report.py#L104)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `dict`（[baseline_report.py:105](../../../src/evaluation/baseline_report.py#L105)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `zip`（[baseline_report.py:106](../../../src/evaluation/baseline_report.py#L106)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `json.dumps`（[baseline_report.py:123](../../../src/evaluation/baseline_report.py#L123)）：来自 `json`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：未见 `raise`；下游异常可能继续上抛。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---
