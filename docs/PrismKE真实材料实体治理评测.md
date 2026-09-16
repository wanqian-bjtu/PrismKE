# 真实材料实体治理基线评测

本轮只评测给定实体提及后的解析，不调用LLM/VLM、OCR或生产图数据库，也不调参。
开发继续使用`dev/v0.4`，不改变`v0.4.0`发布标签。

## 工作簿导出

安装`evaluation`可选依赖后，使用`prismke export-entity-annotations WORKBOOK --package PACKAGE --output OUTPUT`。
PACKAGE为包含materials、sources.json及annotations原始答案的材料包；OUTPUT必须选择新的子目录。

程序以提及ID匹配原始JSON：已确认且人工答案为空时接受原始建议，人工答案非空则覆盖评分标签。
显示换行不改变实体名称，原始名称、类型和证据来自下载原文，不使用“判断依据”作为模型输入。
未知ID、类型冲突、重复记录、缺失提及或哈希/位置不一致时停止导出。
输出包括manifest、确认版答案、初始库、证据索引、工作簿和答案文件哈希。
原始Excel、原始JSON和待复核事项不会被改写。

## 两种协议

`prismke evaluate-entities MANIFEST --output REPORT --embedding-provider bge-m3 --protocol fixed`

固定模式每次都只使用同一个初始候选库，不持久化新实体。库外对象按NIL计分。
旧manifest未指定协议时仍使用fixed。

`prismke evaluate-entities MANIFEST --output REPORT --embedding-provider bge-m3 --protocol sequential`

顺序模式严格按manifest顺序处理。系统自动选择或创建的实体写入临时JSON图谱并更新索引；
待审核结果不入库。实体ID、名称、别名和上下文全部来自解析器，不由标准答案生成。
标准聚类与运行时ID的对应仅用于计分，不传给解析器。
前序待审核会使后续文档继续遇到库外对象；重复创建和聚类碎片必须如实报告。

默认参数为Top-K 10、自动链接0.88、审核0.65、候选差距0.08；基线运行需显式固定这些值。
BGE-M3仅使用已下载模型，失败时停止，不自动下载或回退Mock。
API模式与生产GraphStore不会被初始化；临时图谱没有Claim邻域，不能证明邻域验证有效。

## 指标边界

- Top-1是候选排名第一/精确匹配是否正确；待审核候选可以排名正确，但没有自动成功。
- 自动链接覆盖率是exact/vector数量除以全部样本；错误率的分母是自动链接数量。
- NIL Precision/Recall/F1以每条提及处理前的候选库为准，顺序模式与固定模式分母不同。
- B-Cubed使用系统选择的真实运行时ID，待审核提及形成独立未决簇；不按标准答案修补聚类。
- 报告的governance_cases仅保留旧manifest计数，不表示执行了合并/拆分。
- 图片组输入是人工给定名称/类型，不是VLM或OCR识别输出；需与文本组分别统计。

真实基线报告和逐条候选分数保存于runtime，不上传原文、详细答案或私有工作簿到GitHub。
Q01保留人工同人结论但缺少身份依据暂不计分，Q02作不合并的定性案例，Q03仅排除计分。
公开材料的授权和独立性需另外检查，相关论文与README复述不等于跨领域独立盲测。
