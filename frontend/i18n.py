# ruff: noqa: E501
"""Bilingual presentation catalog and browser-side locale controller."""

from __future__ import annotations

import json
from typing import Literal, cast

LocaleCode = Literal["en", "zh-CN"]
DEFAULT_LOCALE: LocaleCode = "en"
LOCALE_STORAGE_KEY = "prismke.ui.locale.v1"

EN_BY_ZH: dict[str, str] = {
    '### 合并与拆分审核': '### Merge and split review',
    '### 实体合并建议': '### Entity Merger Suggestions',
    '### 实体拆分建议': '### Entity splitting suggestions',
    '### 实体治理历史': '### Entity Governance History',
    '### 尚无执行任务': '### No tasks have been executed yet',
    '**Neo4j 密码：**': '**Neo4j password:**',
    '**密钥状态** LLM：': '**Key Status** LLM:',
    '**工作区** Development · `': '**Workspace** Development · `',
    '**隔离审核工作区** 原评测只读，抽取调用禁用。': '**Isolated review workspace** The original evaluation is read-only and extraction calls are disabled.',
    'Agent 交接': 'Agent handoffs',
    'Agent 协作': 'Agent collaboration',
    'Agent 建议 Token 预算': 'Agent advisory token budget',
    'Claim 关联图片': 'Claim associated image',
    'Claim 到新 Entity 的映射 JSON': 'Claim to new Entity mapping JSON',
    'LLM API Key（当前会话）': 'LLM API Key (current session)',
    'LLM 模型别名': 'LLM model alias',
    'MinerU 高精度解析': 'MinerU high-accuracy parser',
    'Neo4j 密码': 'Neo4j password',
    'Neo4j 数据库': 'Neo4j database',
    'Neo4j 用户': 'Neo4j user',
    'OCR 模型': 'OCR model',
    'OCR 设备': 'OCR device',
    'OCR 语言': 'OCR language',
    'PDF 解析决定': 'PDF parsing decisions',
    'PDF 解析模式': 'PDF parser',
    'PrismKE 研究工作台': 'PrismKE Research Workspace',
    'PyMuPDF 快速解析': 'PyMuPDF fast parser',
    'Reflection 摘要': 'Reflection summary',
    'Reflection 详情': 'Reflection Details',
    'Run ID（链接审核时填写）': 'Run ID (fill in during link review)',
    'Schema 信息抽取': 'Schema-guided information extraction',
    'Schema 文件': 'Schema file',
    'Schema 文本（JSON/YAML）': 'Schema text (JSON/YAML)',
    'Schema 来源': 'Schema source',
    'VLM API Key（当前会话）': 'VLM API Key (current session)',
    'VLM 模型别名': 'VLM model alias',
    '上下文': 'context',
    '上传文件': 'Upload file',
    '业务状态': 'Run status',
    '中文': 'Chinese',
    '中英混合': 'Chinese and English',
    '主体/名称': 'Subject / name',
    '事件 · ': 'Event · ',
    '事件：': 'Event: ',
    '事实审核': 'Claim review',
    '交接与模态详情': 'Handoff and modality details',
    '仅检查': 'Check only',
    '任务': 'Task',
    '任务列表': 'task list',
    '任务模式': 'Task mode',
    '任务版本': 'Task version',
    '任务状态': 'Task status',
    '任务类型': 'Task type',
    '任务配置': 'Task configuration',
    '使用提供实体': 'Use provided entities',
    '保存抽取审核': 'Save extraction review',
    '保存核对事件': 'Save reconciliation event',
    '保存设置': 'Save settings',
    '保留的 Entity ID': 'Reserved Entity ID',
    '候选': 'Candidate',
    '候选 Entity ID': 'Candidate Entity ID',
    '候选 ID': 'Candidate ID',
    '候选、实体与 Schema 约束': 'Candidates, Entities and Schema Constraints',
    '候选及评分分解': 'Candidate score breakdown',
    '候选数': 'number of candidates',
    '候选评分': 'candidate scoring',
    '候选评分详情': 'Candidate scoring details',
    '候选邻域': 'candidate neighborhood',
    '候选邻域详情': 'Candidate neighborhood details',
    '停用原因': 'Reason for deactivation',
    '停用案例': 'Deactivate case',
    '健康状态': 'health status',
    '允许远程资源': 'Allow remote resources',
    '全部': 'all',
    '公式': 'Formula',
    '关系 · ': 'Relation · ',
    '关系实体来源': 'Entity source for relations',
    '关系抽取': 'Relation extraction',
    '关联知识': 'Linked knowledge',
    '具体页面': 'Page',
    '冲突对方事实': 'conflicting facts',
    '决定': 'Decide',
    '分支': 'branch',
    '分支进度': 'branch progress',
    '创建合并审核任务': 'Create a merge review task',
    '创建拆分审核任务': 'Create split review tasks',
    '创建新实体': 'Create a new entity',
    '别名': 'Alias',
    '刷新': 'refresh',
    '刷新媒体资产': 'Refresh media assets',
    '刷新审核历史': 'Refresh review history',
    '刷新总览': 'Refresh overview',
    '刷新校验问题': 'Refresh validation problem',
    '刷新案例': 'Refresh case',
    '刷新版本': 'refresh version',
    '刷新视觉审核队列': 'Refresh visual review queue',
    '刷新运行': 'Refresh runs',
    '刷新运行状态': 'Refresh run status',
    '功能分组': 'Section',
    '包含已停用': 'Contains disabled',
    '区域证据': 'regional evidence',
    '单候选最大修复次数': 'Maximum repair attempts per candidate',
    '单运行 Token 预算': 'Token budget per run',
    '单运行时间预算（秒）': 'Time budget per run (seconds)',
    '历史与版本': 'History and revisions',
    '历史任务': 'historical task',
    '原 Entity ID': 'Original Entity ID',
    '原因': 'reason',
    '原审核事件': 'Original review event',
    '取消原因': 'Reason for cancellation',
    '取消操作者': 'cancel operator',
    '受控证据预览': 'Controlled evidence preview',
    '变更数': 'Number of changes',
    '只有经人工确认“未发送”或“未计费”的请求可重新派发；可能已计费的请求仍保持阻断。': 'Only requests that have been manually confirmed as "not sent" or "unbilled" can be redistributed; requests that may have been billed remain blocked.',
    '召回': 'recall',
    '可查询媒体对象': 'Queryable media objects',
    '可能已计费，继续阻断': 'It may have been billed and will continue to be blocked.',
    '合并建议': 'Merge suggestions',
    '名称': 'name',
    '名称、别名或上下文': 'name, alias, or context',
    '启用': 'enable',
    '启用 Reflection': 'Enable Reflection',
    '图存储': 'Graph store',
    '图存储健康状态': 'Graph store health',
    '图片': 'Image',
    '图表': 'Chart',
    '图谱': 'Knowledge graph',
    '复用来源': 'Reuse sources',
    '失败': 'Failed',
    '失败代码': 'Failure code',
    '媒体、实体与 Claim 详情': 'Media, Entity and Claim Details',
    '媒体关系': 'Media relation',
    '媒体知识': 'Media knowledge',
    '媒体类型': 'Media type',
    '媒体详情': 'Media details',
    '媒体资产': 'Media assets',
    '字符串': 'string',
    '安全取消': 'Safe cancellation',
    '完整差异': 'Full diff',
    '完整执行状态': 'complete execution status',
    '完整知识构建': 'Knowledge graph construction',
    '完整运行状态': 'Full run state',
    '实体 Entity ID': 'Entity Entity ID',
    '实体 Revision 历史': 'Entity Revision History',
    '实体 · ': 'Entity · ',
    '实体关系抽取与消歧': 'Joint extraction and disambiguation',
    '实体关联图片': 'Entity association image',
    '实体名称或别名': 'Entity name or alias',
    '实体审核': 'Entity review',
    '实体抽取': 'Entity extraction',
    '实体提及': 'Entity mention',
    '实体治理': 'Entity governance',
    '实体清单 JSON': 'Entity list JSON',
    '实体类型': 'Entity type',
    '实体邻域': 'entity neighborhood',
    '审核人': 'Reviewer',
    '审核决定': 'review decision',
    '审核动作': 'Review action',
    '审核历史': 'Review history',
    '审核历史与纠正': 'Review history and corrections',
    '审核原因': 'Review reason',
    '审核对象': 'Review object',
    '审核意见': 'Review comments',
    '审核结果': 'Review results',
    '审核详情': 'Review details',
    '审核进度': 'Review progress',
    '宾语/值': 'Object / value',
    '对方原文与位置': 'The other party’s original text and location',
    '对方证据': "Opposite party's evidence",
    '对方证据区域': "Opponent's evidence area",
    '对象': 'object',
    '对象类型': 'Object type',
    '尚无 PDF 解析决定。': 'No PDF parsing decision yet.',
    '尚未启动构建': 'No run has been started',
    '尚未审核抽取结果': 'The extraction results have not been reviewed yet',
    '尚未执行批次操作': 'No batch operation has been performed yet',
    '尚未提交视觉审核': 'Not yet submitted for visual review',
    '尚未校验 Schema': 'Schema has not been validated',
    '展开实体关联媒体': 'Expand entity associated media',
    '属性 · ': 'Attribute · ',
    '属性：': 'Attribute: ',
    '工作区': 'Workspace',
    '工具': 'tool',
    '已停用': 'Inactive',
    '已创建': 'Created',
    '已取消': 'Cancelled',
    '已处理': 'Resolved',
    '已完成': 'Completed',
    '已批准': 'Approved',
    '已拒绝': 'Rejected',
    '已排除': 'Excluded',
    '已暂停': 'Paused',
    '已暂缓': 'Deferred',
    '已配置': 'Configured',
    '已阻断': 'Blocked',
    '开始构建': 'Start run',
    '当前事实': 'current facts',
    '当前决定与证据': 'Current decisions and evidence',
    '当前对象证据': 'current object evidence',
    '当前节点': 'Current node',
    '当前资产': 'current assets',
    '当前运行': 'Current run',
    '待处理': 'Pending',
    '待审核': 'Pending review',
    '待核对请求': 'Pending request',
    '待核查提示': 'Tips to be verified',
    '得分': 'Score',
    '总览': 'Overview',
    '恢复运行': 'Resume run',
    '我确认停用该案例': 'I confirm to deactivate this case',
    '我确认创建补偿 Revision': 'I confirm the creation of compensation Revision',
    '我确认将该批次的已批准事实写入图谱': 'I confirm that the approved facts for this batch will be written into the map',
    '执行与交接': 'Execution and handoffs',
    '执行任务': 'Run execution',
    '执行回滚': 'perform rollback',
    '执行操作结果': 'Execute operation result',
    '执行时间线': 'Execution timeline',
    '执行状态': 'Execution status',
    '批准': 'Approve',
    '批准事实': 'Approval fact',
    '批次处理': 'Batch processing',
    '批次文件': 'Batch files',
    '技术详情': 'Technical details',
    '抽取结果': 'Extraction results',
    '抽取结果审核': 'Extraction result review',
    '拆分建议': 'Split proposal',
    '拒绝': 'Reject',
    '拒绝事实': 'reject facts',
    '排队中': 'Queued',
    '排除候选': 'Eliminate candidates',
    '排除原因': 'Troubleshooting causes',
    '排除意见': 'exclude opinions',
    '排除文件': 'Exclude files',
    '排除错误提及': 'Exclude false mentions',
    '提交实体审核': 'Submit entity review',
    '提交审核人': 'Submit for reviewer',
    '提交当前审核': 'Submit current review',
    '提交批次到图谱': 'Submit batch to graph',
    '提交视觉审核': 'Submit visual review',
    '提交预览': 'Submit preview',
    '提及 Evidence ID': 'Mention Evidence ID',
    '提及与关联事实': 'mention and related facts',
    '提及证据': 'Mention evidence',
    '搜索实体': 'Search entities',
    '搜索结果': 'Search results',
    '操作影响': 'Run impact',
    '操作结果': 'Operation result',
    '操作者': 'operator',
    '文件': 'document',
    '文本 Provider': 'Text provider',
    '文本输入': 'Text input',
    '文档': 'document',
    '文档 ID': 'Document ID',
    '文档（最多 20 个）': 'Documents (up to 20)',
    '新实体 JSON 数组': 'New entity JSON array',
    '新建构建': 'New extraction run',
    '时间': 'time',
    '暂无媒体出现记录': 'No media occurrences available',
    '暂无审核任务': 'No review tasks available',
    '暂无批次文件': 'No batch files available',
    '暂无未知请求': 'No unknown requests available',
    '暂无校验问题': 'No validation issues available',
    '暂无案例': 'No cases available',
    '暂无记录': 'No records available',
    '暂无证据': 'No evidence available',
    '暂无运行': 'No runs available',
    '暂缓': 'Defer',
    '暂缓判断': 'Suspend judgment',
    '更新时间': 'Update time',
    '替代候选实体': 'alternative candidate entity',
    '替代决定': 'alternative decision',
    '最近运行': 'Recent runs',
    '有效': 'Active',
    '服务状态': 'Service status',
    '服务详情': 'Service details',
    '未知': 'Unknown',
    '未知 Provider 请求核对': 'Unknown Provider request validation',
    '未配置': 'Not configured',
    '查看 Claim 关联媒体': 'View Claim associated media',
    '查看候选邻域': 'View candidate neighborhoods',
    '查看所选候选邻域': 'View selected candidate neighborhoods',
    '查看提及证据': 'View mention evidence',
    '查看检索与修复记录': 'View search and repair records',
    '查看轨迹': 'View trace',
    '查询治理与回滚历史': 'Query governance and rollback history',
    '查询邻域': 'Query neighborhood',
    '标题': 'title',
    '校验 Schema': 'Validate Schema',
    '校验审核人': 'Validation reviewer',
    '校验操作结果': 'Verify operation results',
    '校验汇总': 'Check summary',
    '校验证据区域': 'Calibration evidence area',
    '校验证据文本': 'Calibration evidence text',
    '校验运行': 'Check run',
    '校验问题': 'Validation issues',
    '校验阶段': 'Validation phase',
    '核对人': 'Checker',
    '核对依据': 'Check basis',
    '核对结果': 'Check results',
    '核对结论': 'Check conclusion',
    '案例、证据与停用历史': 'Cases, evidence and deactivation history',
    '案例与反思': 'Cases and reflection',
    '案例库': 'Case library',
    '案例检索': 'Case retrieval',
    '案例类型': 'Case type',
    '案例详情': 'Case details',
    '检查或重建索引': 'Check or rebuild index',
    '检查连接': 'Check connections',
    '检索候选': 'Search candidates',
    '模型与图存储': 'Models and graph storage',
    '步骤': 'step',
    '比较版本': 'Compare revisions',
    '治理/融合语义建议': 'Governance and fusion semantic advisor',
    '清除已保存 Neo4j 密码': 'Clear the saved Neo4j password',
    '源 Entity ID，逗号分隔': 'Source Entity IDs, comma separated',
    '父版本': 'Parent revision',
    '版本': 'Version',
    '版本差异': 'Version differences',
    '版本管理': 'Revision management',
    '状态': 'Status',
    '理由，分号分隔': 'Reasons, separated by semicolon',
    '用量': 'Dosage',
    '留空则使用服务器配置': 'Leave blank to use the server configuration',
    '留空则保持已有密码': 'Leave blank to keep existing password',
    '留空显示全部': 'Leave blank to show all',
    '目标 Revision': 'Target revision',
    '确认使用 PyMuPDF 重试': 'Confirm to try again using PyMuPDF',
    '确认写入隔离图谱': 'Confirm writing of isolated graph',
    '确认将预览内容写入隔离图谱': 'Confirm that the preview content will be written to the quarantine map',
    '确认应用纠正': 'Confirm application correction',
    '确认应用纠正并保留历史': 'Confirm to apply correction and retain history',
    '确认排除此候选，保留原始问题及审计': 'Confirm to eliminate this candidate and keep the original question and review',
    '确认未发送': 'Confirm not sent',
    '确认未计费': 'Confirm no billing',
    '端到端实体关系抽取': 'Joint entity and relation extraction',
    '管理员': 'Administrator',
    '类型': 'type',
    '类型/关系': 'Type / relation',
    '系统状态': 'System status',
    '系统自动识别': 'Detect entities automatically',
    '索引状态': 'index status',
    '索引维护': 'Index maintenance',
    '纠正关联证据': 'Correct evidence of association',
    '纠正原因': 'Correct the cause',
    '纠正审核人': 'correct reviewer',
    '纠正影响': 'correction effects',
    '纠正影响与版本差异': 'Correct impact and version differences',
    '纠正状态': 'correct status',
    '纠正证据区域': 'Correct evidence area',
    '纠正证据原文': 'Correct the original text of the evidence',
    '纠正运行': 'Correction operation',
    '结果 ID': 'Result ID',
    '继续处理': 'Continue processing',
    '综合': 'comprehensive',
    '置信度': 'Confidence',
    '自动判定（推荐）': 'Automatic (recommended)',
    '自动模式选择 MinerU 后不会静默回退。只有解析阻断时，操作者填写身份与原因，才可改用 PyMuPDF 重试。': 'Automatic routing never silently falls back after selecting MinerU. When parsing is blocked, an identified operator may retry with PyMuPDF after providing a reason.',
    '自动（当前：': 'automatic (currently:',
    '节点': 'node',
    '英文': 'English',
    '补偿 Revision': 'Compensation Revision',
    '补偿回滚': 'Compensating rollback',
    '表格': 'Table',
    '要回滚的 Revision': 'Revision to roll back',
    '视觉 Provider': 'Vision provider',
    '视觉审核': 'Visual review',
    '视觉审核任务': 'Visual review tasks',
    '视觉断言': 'Visual assertion',
    '解析已阻断': 'Parser blocked',
    '警告': 'Warnings',
    '设置结果': 'Settings result',
    '证据': 'Evidence',
    '证据与候选邻域': 'Evidence and candidate neighborhoods',
    '证据元数据': 'evidence metadata',
    '证据区域': 'evidence area',
    '证据原文与位置': 'Evidence text and location',
    '证据哈希': 'evidence hash',
    '证据定位': 'Evidence location',
    '语义名称': 'Semantic name',
    '语言': 'language',
    '说明': 'illustrate',
    '请求 ID': 'Request ID',
    '读取证据': 'Load evidence',
    '资产': 'assets',
    '起始 Revision': 'Base revision',
    '输入摘要': 'Enter summary',
    '运行': 'run',
    '运行中': 'Running',
    '进度': 'schedule',
    '选择任务': 'Select task',
    '选择媒体出现记录': 'Select a media occurrence',
    '选择实体': 'Select entity',
    '选择校验问题': 'Select validation question',
    '选择案例': 'Select case',
    '选择的 Entity ID': 'Selected Entity ID',
    '邻域': 'Neighborhood',
    '邻域事实与证据引用': 'Neighborhood Facts and Evidence Citations',
    '邻域深度': 'neighborhood depth',
    '配置操作者': 'Configuration operator',
    '重试文件': 'retry file',
    '链接候选': 'Link candidate',
    '错误': 'Errors',
    '问题与候选影响': 'Issues and Candidate Impacts',
    '问题代码': 'Issue code',
    '问题状态': 'Issue status',
    '问题证据': 'question evidence',
    '问题详情': 'Issue details',
    '阶段': 'stage',
    '降级原因': 'Reason for downgrade',
    '降级确认人': 'downgrade confirmer',
    '降级结果': 'downgrade result',
    '隔离图谱提交摘要': 'Isolated Graph Subtask Abstract',
    '页码': 'page number',
    '页面': 'Page',
    '页面不回显旧密码；新值保存到权限为 600 的私密运行配置。': 'The existing password is never displayed. A new value is stored in the private runtime configuration with mode 600.',
    '页面渲染': 'Page render',
    '页面输入的 API Key 仅保存在当前服务进程内，不写入运行文件或日志。': 'API keys entered here stay in the current service process and are never written to run files or logs.',
    '预览纠正影响': 'Preview correction effects',
    '风险': 'risk',
    '风险提示': 'Risk warning',
    '高级治理操作': 'Advanced governance operations',
    '高级策略': 'Advanced policies',
    '默认启用受预算限制的 Reflection 与语义建议，会产生额外模型调用；缺少 LLM Key 时将在调用前阻断。': 'Budget-limited Reflection and semantic advice are enabled by default and make additional model calls. A missing LLM key blocks the run before dispatch.',
}

EN_BY_ZH.update(
    {
        "### 实体合并建议": "### Entity merge suggestions",
        "### 实体拆分建议": "### Entity split suggestions",
        "### 实体治理历史": "### Entity governance history",
        "### 尚无执行任务": "### No execution task available",
        "Reflection 详情": "Reflection details",
        "上下文": "Context",
        "任务列表": "Task list",
        "保留的 Entity ID": "Retained Entity ID",
        "候选、实体与 Schema 约束": "Candidates, entities, and Schema constraints",
        "候选数": "Candidate count",
        "候选评分": "Candidate score",
        "候选邻域": "Candidate neighborhood",
        "健康状态": "Health status",
        "全部": "All",
        "冲突对方事实": "Conflicting claim",
        "分支": "Branch",
        "分支进度": "Branch progress",
        "取消操作者": "Cancellation operator",
        "召回": "Recall",
        "可查询媒体对象": "Queryable media occurrences",
        "可能已计费，继续阻断": "Possibly billed; keep blocked",
        "名称": "Name",
        "名称、别名或上下文": "Name, alias, or context",
        "完整执行状态": "Full execution status",
        "实体 Entity ID": "Entity ID",
        "实体关联图片": "Images linked to entity",
        "实体邻域": "Entity neighborhood",
        "审核决定": "Review decision",
        "对方原文与位置": "Conflicting source text and location",
        "对方证据": "Conflicting evidence",
        "对方证据区域": "Conflicting evidence region",
        "对象": "Object",
        "当前事实": "Current claims",
        "当前对象证据": "Evidence for current object",
        "待核查提示": "Items requiring verification",
        "执行回滚": "Perform rollback",
        "执行操作结果": "Operation result",
        "批准事实": "Approve claim",
        "拒绝事实": "Reject claim",
        "排除候选": "Exclude candidate",
        "排除原因": "Exclusion reason",
        "排除意见": "Exclusion comments",
        "提交审核人": "Submitting reviewer",
        "提及与关联事实": "Mention and linked claims",
        "操作者": "Operator",
        "文件": "File",
        "文档": "Document",
        "时间": "Time",
        "更新时间": "Updated at",
        "替代候选实体": "Replacement candidate entity",
        "替代决定": "Replacement decision",
        "核对人": "Reconciler",
        "核对依据": "Reconciliation basis",
        "核对结果": "Reconciliation result",
        "核对结论": "Reconciliation decision",
        "标题": "Title",
        "校验操作结果": "Validation operation result",
        "校验汇总": "Validation summary",
        "校验证据区域": "Validation evidence region",
        "校验证据文本": "Validation evidence text",
        "校验运行": "Validation run",
        "索引状态": "Index status",
        "用量": "Usage",
        "确认将预览内容写入隔离图谱": "Confirm writing the preview to the isolated graph",
        "确认排除此候选，保留原始问题及审计": "Confirm excluding this candidate while retaining the original issue and audit trail",
        "类型": "Type",
        "纠正原因": "Correction reason",
        "纠正审核人": "Correction reviewer",
        "纠正影响": "Correction impact",
        "纠正状态": "Correction status",
        "纠正证据区域": "Correction evidence region",
        "纠正证据原文": "Correction evidence text",
        "纠正运行": "Correction run",
        "综合": "Overall",
        "自动（当前：": "Automatic (current:",
        "节点": "Node",
        "证据元数据": "Evidence metadata",
        "证据区域": "Evidence region",
        "证据哈希": "Evidence hash",
        "语言": "Language",
        "说明": "Description",
        "资产": "Assets",
        "输入摘要": "Input summary",
        "运行": "Run",
        "进度": "Progress",
        "邻域深度": "Neighborhood depth",
        "重试文件": "Retry file",
        "问题证据": "Issue evidence",
        "阶段": "Stage",
        "降级确认人": "Fallback operator",
        "降级结果": "Fallback result",
        "隔离图谱提交摘要": "Isolated graph commit summary",
        "页码": "Page",
        "风险": "Risk",
        "构建与执行": "Build and execution",
        "审核与校验": "Review and validation",
        "证据与图谱": "Evidence and graph",
        "媒体知识": "Media knowledge",
        "实体治理": "Entity governance",
        "历史与版本": "History and revisions",
        "案例与反思": "Cases and reflection",
        "Agent 协作": "Agent collaboration",
        "系统状态": "System status",
        "新建抽取与构建": "New extraction and construction",
        "运行、审核、校验和图存储状态": "Run, review, validation, and graph store status",
        "批量提交文档并选择可追溯的抽取或知识构建任务": "Submit documents in batches and select a traceable extraction or knowledge construction task",
        "分支进度、执行时间线与安全恢复": "Branch progress, execution timeline, and safe recovery",
        "核对实体候选、证据与链接决定": "Review entity candidates, evidence, and linking decisions",
        "核对规范事实、冲突与原始证据": "Review canonical facts, conflicts, and source evidence",
        "检查阻断问题并保留排除审计": "Inspect blocking issues and retain exclusion audits",
        "预览并应用可追溯的历史决定纠正": "Preview and apply traceable corrections to historical decisions",
        "按运行和事实定位文本或视觉证据": "Locate textual or visual evidence by run and claim",
        "检索实体并浏览有限邻域": "Search entities and browse bounded neighborhoods",
        "查看可校验的图片、图表、表格和公式出现记录": "View verifiable image, chart, table, and formula occurrences",
        "审核图片描绘关系、视觉属性与区域证据": "Review image depictions, visual assertions, and regional evidence",
        "管理候选、合并、拆分与实体历史": "Manage candidates, merges, splits, and entity history",
        "查询审核案例及其索引状态": "Query review cases and their index status",
        "查看问题修复、案例使用与预算记录": "Inspect issue repairs, case usage, and budget records",
        "查看三 Agent 的结构化决策与交接轨迹": "Inspect structured decisions and handoff traces from the three agents",
        "比较 Revision 并执行补偿回滚": "Compare revisions and perform compensating rollback",
        "检查应用、工作器与存储连接": "Check application, worker, and storage connections",
        "**隔离审核工作区**\n\n原评测只读，抽取调用禁用。": "**Isolated review workspace**\n\nThe original evaluation is read-only and extraction calls are disabled.",
        "将文件拖放到此处": "Drop files here",
        "点击上传": "Click to upload",
        "-或-": "or",
        "- 或 -": "or",
        "工作区概览": "Workspace overview",
        "尚无执行任务": "No execution task available",
        "实体邻域图": "Entity neighborhood graph",
        "通过 API 使用": "Use via API",
        "使用 Gradio 构建": "Built with Gradio",
        "设置": "Settings",
        "请填写审核人、审核原因和请求编号。": "Enter the reviewer, review reason, and request ID.",
        "请填写审核人。": "Enter the reviewer.",
        "请填写操作原因。": "Enter the operation reason.",
        "请填写请求编号。": "Enter the request ID.",
        "当前数据版本已更新，请刷新页面后重试。": "The data version has changed. Refresh the page and try again.",
        "证据不可用或完整性校验失败，请刷新后核对。": "The evidence is unavailable or failed integrity validation. Refresh and verify it.",
        "请先选择运行。": "Select a run first.",
        "请先选择实体。": "Select an entity first.",
        "请先选择媒体出现记录。": "Select a media occurrence first.",
        "请先选择媒体出现记录": "Select a media occurrence first.",
        "请先选择审核任务。": "Select a review task first.",
        "请先上传至少一个文档": "Upload at least one document.",
        "请上传 Schema 文件": "Upload a Schema file.",
        "Schema 内容格式无效，请检查 JSON/YAML 语法和字段约束。": "The Schema is invalid. Check its JSON/YAML syntax and field constraints.",
        "实体清单必须是合法的 JSON 数组": "The entity list must be a valid JSON array.",
        "操作失败，请刷新后重试。": "The operation failed. Refresh and try again.",
    }
)

GRADIO_ZH_BY_EN: dict[str, str] = {
    "Drop File Here": "拖放文件到这里",
    "Drop files here": "拖放文件到这里",
    "Click to Upload": "点击上传",
    "Browse files": "浏览文件",
    "Upload": "上传",
    "Download": "下载",
    "Clear": "清除",
    "Remove": "移除",
    "Edit": "编辑",
    "Fullscreen": "全屏",
    "Copy": "复制",
    "Copied": "已复制",
    "Submit": "提交",
    "Cancel": "取消",
    "Retry": "重试",
    "Reset": "重置",
    "Loading...": "加载中……",
    "Error": "错误",
    "Warning": "警告",
    "Info": "信息",
    "Success": "成功",
    "Runs": "运行",
    "Use via API": "通过 API 使用",
    "Settings": "设置",
    "Built with Gradio": "基于 Gradio 构建",
    "or": "或",
}


def normalize_locale(value: object) -> LocaleCode:
    """Normalize untrusted browser locale state to one of two supported values."""

    return cast(LocaleCode, value if value in {"en", "zh-CN"} else DEFAULT_LOCALE)


def tr(source_zh: str, locale: object = DEFAULT_LOCALE) -> str:
    """Translate an application-owned Chinese source string for display."""

    return source_zh if normalize_locale(locale) == "zh-CN" else EN_BY_ZH.get(source_zh, source_zh)


def browser_i18n_bootstrap_js() -> str:
    """Return the locale controller body injected into the Gradio load hook."""

    catalog = json.dumps(EN_BY_ZH, ensure_ascii=False, separators=(",", ":"))
    gradio_zh = json.dumps(GRADIO_ZH_BY_EN, ensure_ascii=False, separators=(",", ":"))
    return rf"""
      const prismkeEnglish = {catalog};
      const prismkeChinese = Object.fromEntries(
        Object.entries(prismkeEnglish).map(([zh, en]) => [en, zh])
      );
      const prismkeGradioChinese = {gradio_zh};
      const prismkeTextOrigins = window.__prismkeTextOrigins || new WeakMap();
      const prismkeAttributeOrigins = window.__prismkeAttributeOrigins || new WeakMap();
      window.__prismkeTextOrigins = prismkeTextOrigins;
      window.__prismkeAttributeOrigins = prismkeAttributeOrigins;
      const localeKey = '{LOCALE_STORAGE_KEY}';
      const normalizeLocale = value => value === 'zh-CN' ? 'zh-CN' : 'en';
      const effectiveLocale = (element, fallback) => {{
        const toast = element?.closest?.('.toast-wrap, .toast-container, [role="alert"]');
        if (!toast) return fallback;
        const actionLocale = normalizeLocale(window.__prismkeActionLocale || fallback);
        toast.dataset.prismkeLocale = actionLocale;
        return actionLocale;
      }};
      const replaceDynamic = (text, locale) => {{
        if (locale === 'en') {{
          return text
            .replace(/^警告 (\d+) · 错误 (\d+)$/, 'Warnings $1 · Errors $2')
            .replace(/^自动（当前：(CPU|GPU 0)）$/, 'Automatic (current: $1)')
            .replace(/^操作失败，请刷新后重试；如问题持续，请联系管理员。错误编号：([a-f0-9]+)。$/i, 'The operation failed. Refresh and try again. If it persists, contact the administrator with error reference: $1.')
            .replace(/^运行 (\d+) · 执行中 (\d+) · 待审核 (\d+) · 阻断问题 (\d+) · 工作器 (.+)$/, 'Runs $1 · Running $2 · Pending review $3 · Blocking issues $4 · Worker $5')
            .replace(/· 健康 ·/g, '· Healthy ·');
        }}
        return text;
      }};
      const translateRaw = (raw, locale) => {{
        if (locale === 'en') return replaceDynamic(prismkeEnglish[raw] || raw, locale);
        return prismkeChinese[raw] || prismkeGradioChinese[raw] || raw;
      }};
      const withWhitespace = (original, translated) => {{
        const leading = original.match(/^\s*/)?.[0] || '';
        const trailing = original.match(/\s*$/)?.[0] || '';
        return `${{leading}}${{translated}}${{trailing}}`;
      }};
      const translateTextNode = (node, locale) => {{
        if (!node.parentElement || node.parentElement.closest('pre, code, textarea, [data-prismke-no-i18n]')) return;
        locale = effectiveLocale(node.parentElement, locale);
        if (!prismkeTextOrigins.has(node)) prismkeTextOrigins.set(node, node.textContent || '');
        const original = prismkeTextOrigins.get(node) || '';
        const raw = original.trim();
        if (!raw) return;
        const translated = locale === 'zh-CN' && prismkeEnglish[raw] ? raw : translateRaw(raw, locale);
        const next = withWhitespace(original, translated);
        if (node.textContent !== next) node.textContent = next;
      }};
      const translateAttributes = (element, locale) => {{
        if (element.closest('pre, code, textarea, [data-prismke-no-i18n]')) return;
        locale = effectiveLocale(element, locale);
        let origins = prismkeAttributeOrigins.get(element);
        if (!origins) {{ origins = {{}}; prismkeAttributeOrigins.set(element, origins); }}
        ['placeholder', 'title', 'aria-label'].forEach(attribute => {{
          if (!element.hasAttribute(attribute)) return;
          if (!(attribute in origins)) origins[attribute] = element.getAttribute(attribute) || '';
          const original = origins[attribute];
          const translated = locale === 'zh-CN' && prismkeEnglish[original] ? original : translateRaw(original, locale);
          if (element.getAttribute(attribute) !== translated) element.setAttribute(attribute, translated);
        }});
        if (element instanceof HTMLInputElement && element.readOnly && element.getAttribute('role') !== 'combobox') {{
          if (!('value' in origins)) origins.value = element.value;
          const original = origins.value;
          const translated = locale === 'zh-CN' && prismkeEnglish[original] ? original : translateRaw(original, locale);
          if (element.value !== translated) element.value = translated;
        }}
      }};
      const translateComboboxValues = locale => {{
        document.querySelectorAll('input[role="combobox"]').forEach(input => {{
          const current = input.value || '';
          let source = input.dataset.prismkeI18nSourceValue || '';
          if (prismkeEnglish[current]) {{
            source = current;
            input.dataset.prismkeI18nSourceValue = current;
          }} else if (prismkeChinese[current]) {{
            source = prismkeChinese[current];
            input.dataset.prismkeI18nSourceValue = source;
          }} else if (source && current !== source && current !== prismkeEnglish[source]) {{
            source = '';
            delete input.dataset.prismkeI18nSourceValue;
          }}
          if (!source) return;
          const translated = locale === 'en' ? (prismkeEnglish[source] || source) : source;
          if (input.value !== translated) input.value = translated;
        }});
      }};
      const translateTree = (root, locale) => {{
        if (root instanceof Text) {{ translateTextNode(root, locale); return; }}
        if (!(root instanceof Element || root instanceof Document)) return;
        if (root instanceof Element) translateAttributes(root, locale);
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
        let node;
        while ((node = walker.nextNode())) {{
          if (node instanceof Text) translateTextNode(node, locale);
          else if (node instanceof Element) translateAttributes(node, locale);
        }}
      }};
      const syncLanguageSwitch = locale => {{
        const input = document.querySelector('#language-switch input[type="checkbox"]');
        const checked = locale === 'zh-CN';
        if (input && input.checked !== checked) input.checked = checked;
        const control = document.querySelector('#language-switch');
        if (control) {{
          control.dataset.locale = locale;
          control.setAttribute('role', 'switch');
          control.setAttribute('aria-checked', String(checked));
          control.setAttribute('aria-label', checked ? '切换到英文' : 'Switch to Chinese');
        }}
        if (input && !input.dataset.prismkeKeyboardBound) {{
          input.dataset.prismkeKeyboardBound = 'true';
          input.addEventListener('keydown', event => {{
            if (event.key !== 'Enter' && event.key !== ' ' && event.code !== 'Space') return;
            event.preventDefault();
            input.click();
          }});
          input.addEventListener('change', () => {{
            applyLocale(input.checked ? 'zh-CN' : 'en', true);
          }});
        }}
      }};
      const applyLocale = (requested, persist = true) => {{
        const locale = normalizeLocale(requested);
        window.__prismkeLocale = locale;
        document.documentElement.lang = locale;
        document.documentElement.dataset.prismkeLocale = locale;
        if (persist) localStorage.setItem(localeKey, locale);
        translateTree(document, locale);
        translateComboboxValues(locale);
        syncLanguageSwitch(locale);
        document.querySelector('#prismke-workspace')?.classList.add('i18n-ready');
        window.dispatchEvent(new CustomEvent('prismke:localechange', {{detail: {{locale}}}}));
        return locale;
      }};
      window.PrismKEI18n = {{ setLocale: applyLocale, getLocale: () => window.__prismkeLocale || 'en', translateTree }};
      if (!window.__prismkeI18nObserver) {{
        window.__prismkeI18nObserver = new MutationObserver(records => {{
          const locale = window.__prismkeLocale || 'en';
          records.forEach(record => {{
            if (record.type === 'characterData') translateTextNode(record.target, locale);
            record.addedNodes?.forEach(node => translateTree(node, locale));
          }});
        }});
        window.__prismkeI18nObserver.observe(document.body, {{childList: true, subtree: true, characterData: true}});
      }}
      if (!window.__prismkeI18nActionBound) {{
        window.__prismkeI18nActionBound = true;
        document.addEventListener('click', event => {{
          if (event.target.closest?.('#language-switch')) return;
          if (event.target.closest?.('button, [role="button"]')) {{
            window.__prismkeActionLocale = window.__prismkeLocale || 'en';
            document.querySelectorAll('.toast-wrap, .toast-container, [role="alert"]').forEach(
              toast => translateTree(toast, window.__prismkeActionLocale)
            );
          }}
        }}, true);
        window.addEventListener('storage', event => {{
          if (event.key === localeKey) applyLocale(event.newValue, false);
        }});
      }}
      if (!window.__prismkeI18nValueTimer) {{
        window.__prismkeI18nValueTimer = window.setInterval(
          () => translateComboboxValues(window.__prismkeLocale || 'en'),
          100
        );
      }}
      applyLocale(normalizeLocale(localStorage.getItem(localeKey)), false);
    """
