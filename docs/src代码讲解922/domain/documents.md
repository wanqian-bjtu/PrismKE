源码：[documents.py:1](../../../src/domain/documents.py#L1) | 基准：`dev/v0.10@f2f34d7` | 本文件符号数：13

**模块职责**：Document intermediate representation and evidence coordinates.
**在系统中的位置**：文档、知识、Schema、运行、审核、校验、案例等结构化领域契约。
**直接依赖**：无显式项目内模块导入；外部/标准库：`__future__`、`enum`、`pathlib`、`pydantic`、`typing`。
**主要调用方（静态导入）**：[domain/__init__.py](__init__.md)、[domain/knowledge.py](knowledge.md)、[domain/workflow.py](workflow.md)。
**阅读提示**：下列流程根据当前源码控制流整理；`self`/接口对象的实际类型可能在运行时注入，未能静态解析的调用会明确标注。链接指向源码行或对应讲解文件。

---

# Modality ⭐⭐⭐

**位置与等级**：[documents.py:12](../../../src/domain/documents.py#L12)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：`StrEnum`。

**字段与类级约束**：
- `TEXT`：类级默认或常量，取值由 `'text'` 决定。
- `IMAGE`：类级默认或常量，取值由 `'image'` 决定。
- `OCR`：类级默认或常量，取值由 `'ocr'` 决定。
- `TABLE`：类级默认或常量，取值由 `'table'` 决定。
- `CHART`：类级默认或常量，取值由 `'chart'` 决定。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EvidenceKind ⭐⭐⭐

**位置与等级**：[documents.py:20](../../../src/domain/documents.py#L20)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：`StrEnum`。

**字段与类级约束**：
- `TEXT_SPAN`：类级默认或常量，取值由 `'text_span'` 决定。
- `PDF_BBOX`：类级默认或常量，取值由 `'pdf_bbox'` 决定。
- `IMAGE`：类级默认或常量，取值由 `'image'` 决定。
- `VISUAL_REGION`：类级默认或常量，取值由 `'visual_region'` 决定。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# CoordinateSpace ⭐⭐⭐

**位置与等级**：[documents.py:27](../../../src/domain/documents.py#L27)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：`StrEnum`。

**字段与类级约束**：
- `PDF_POINTS`：类级默认或常量，取值由 `'pdf_points'` 决定。
- `IMAGE_PIXELS`：类级默认或常量，取值由 `'image_pixels'` 决定。
- `NORMALIZED`：类级默认或常量，取值由 `'normalized'` 决定。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# LocalizationLevel ⭐⭐⭐

**位置与等级**：[documents.py:33](../../../src/domain/documents.py#L33)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：本模块的对象实现或数据契约；具体语义由字段、基类和方法共同决定。基类：`StrEnum`。

**字段与类级约束**：
- `TEXT_SPAN`：类级默认或常量，取值由 `'text_span'` 决定。
- `REGION`：类级默认或常量，取值由 `'region'` 决定。
- `ASSET`：类级默认或常量，取值由 `'asset'` 决定。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# BBox ⭐⭐⭐

**位置与等级**：[documents.py:39](../../../src/domain/documents.py#L39)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `x0`：`float`。
- `y0`：`float`。
- `x1`：`float`。
- `y1`：`float`。

**内部成员**：`BBox.validate_bounds`


---

# BBox.validate_bounds ⭐⭐⭐⭐

**位置与等级**：[documents.py:46](../../../src/domain/documents.py#L46)；承担主要 Agent、应用服务或审核/执行入口，跨模块影响显著。

**签名**：`def validate_bounds(self) -> BBox`。

**装饰器/路由**：`model_validator(mode='after')`。

**作用**：处理 `validate_bounds` 对应步骤；下列步骤依据函数体的实际控制流和调用点整理。

**输入与输出**：
- 输入：无业务参数（或仅隐式接收实例）。
- 输出类型：`BBox`；具体返回路径见流程步骤。

**处理流程**：
1. 检查 `self.x0 >= self.x1 or self.y0 >= self.y1`；按条件分流，else 分支不存在。
2. 返回 `self`。

**关键条件与保护**：
- [documents.py:47](../../../src/domain/documents.py#L47)：`self.x0 >= self.x1 or self.y0 >= self.y1`，不满足时跳过本分支。

**调用与被调用**：
- `ValueError`（[documents.py:48](../../../src/domain/documents.py#L48)）：显式调用表达式；动态目标无法仅凭静态分析确定。
- `model_validator`（[documents.py:45](../../../src/domain/documents.py#L45)）：来自 `pydantic.model_validator`；具体实现可能由依赖注入或运行时分派决定。
- 静态扫描未定位直接调用方；可能通过路由注册、LangGraph 节点、协议方法或依赖注入动态调用，不据此判断为死代码。

**状态、副作用与异常**：
- 显式状态/容器赋值：未见属性或容器赋值。外部 I/O 仍可能通过被调用对象发生。
- 显式抛出：`ValueError(<字符串常量>)`。
- 本地捕获：未见 `except`；恢复通常交由调用方或执行管理器。


---

# SourceDocument ⭐⭐⭐

**位置与等级**：[documents.py:52](../../../src/domain/documents.py#L52)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `path`：`Path`。
- `media_type`：`str | None`；默认 `None`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# TextBlock ⭐⭐⭐

**位置与等级**：[documents.py:57](../../../src/domain/documents.py#L57)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `text`：`str`。
- `page_number`：`int | None`；默认 `None`。
- `char_start`：`int | None`；默认 `None`。
- `char_end`：`int | None`；默认 `None`。
- `bbox`：`BBox | None`；默认 `None`。
- `evidence_id`：`str`。
- `modality`：`Modality`；默认 `Modality.TEXT`。
- `source_media_asset_id`：`str | None`；默认 `None`。
- `confidence`：`float | None`；默认 `Field(default=None, ge=0.0, le=1.0)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# MediaAsset ⭐⭐⭐

**位置与等级**：[documents.py:70](../../../src/domain/documents.py#L70)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `path`：`str`。
- `media_type`：`str`。
- `width`：`int | None`；默认 `None`。
- `height`：`int | None`；默认 `None`。
- `page_number`：`int | None`；默认 `None`。
- `evidence_id`：`str`。
- `blob_hash`：`str | None`；默认 `None`。
- `origin`：`Literal['source_image', 'pdf_embedded', 'pdf_page_render', 'docx_embedded', 'html_em…`；默认 `'source_image'`。
- `source_ref`：`str | None`；默认 `None`。
- `context_text`：`str`；默认 `''`。
- `requires_ocr`：`bool`；默认 `False`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# DocumentPage ⭐⭐⭐

**位置与等级**：[documents.py:92](../../../src/domain/documents.py#L92)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `page_number`：`int`；默认 `Field(ge=1)`。
- `width`：`float`；默认 `Field(gt=0)`。
- `height`：`float`；默认 `Field(gt=0)`。
- `requires_ocr`：`bool`；默认 `False`。
- `text_block_ids`：`list[str]`；默认 `Field(default_factory=list)`。
- `media_asset_ids`：`list[str]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# VisualObservation ⭐⭐⭐

**位置与等级**：[documents.py:102](../../../src/domain/documents.py#L102)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `media_asset_id`：`str`。
- `label`：`str`。
- `description`：`str`；默认 `''`。
- `bbox`：`BBox | None`；默认 `None`。
- `confidence`：`float`；默认 `Field(ge=0.0, le=1.0)`。
- `evidence_id`：`str`。
- `attributes`：`dict[str, Any]`；默认 `Field(default_factory=dict)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# EvidenceRef ⭐⭐⭐

**位置与等级**：[documents.py:113](../../../src/domain/documents.py#L113)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `kind`：`EvidenceKind`。
- `document_id`：`str`。
- `source_hash`：`str`。
- `modality`：`Modality`。
- `page_number`：`int | None`；默认 `None`。
- `char_start`：`int | None`；默认 `None`。
- `char_end`：`int | None`；默认 `None`。
- `bbox`：`BBox | None`；默认 `None`。
- `media_asset_id`：`str | None`；默认 `None`。
- `model_name`：`str | None`；默认 `None`。
- `prompt_version`：`str | None`；默认 `None`。
- `coordinate_space`：`CoordinateSpace | None`；默认 `None`。
- `canvas_width`：`float | None`；默认 `Field(default=None, gt=0)`。
- `canvas_height`：`float | None`；默认 `Field(default=None, gt=0)`。
- `localization_level`：`LocalizationLevel | None`；默认 `None`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---

# DocumentIR ⭐⭐⭐

**位置与等级**：[documents.py:132](../../../src/domain/documents.py#L132)；关键支撑逻辑，影响候选、证据或接口的正确传递。

**职责**：Pydantic 领域/接口模型；实例创建时按字段类型和验证器约束数据。基类：`BaseModel`。

**字段与类级约束**：
- `id`：`str`。
- `source_path`：`str`。
- `source_filename`：`str | None`；默认 `None`。
- `source_hash`：`str`。
- `media_type`：`str`。
- `pages`：`list[DocumentPage]`；默认 `Field(default_factory=list)`。
- `text_blocks`：`list[TextBlock]`；默认 `Field(default_factory=list)`。
- `media_assets`：`list[MediaAsset]`；默认 `Field(default_factory=list)`。
- `visual_observations`：`list[VisualObservation]`；默认 `Field(default_factory=list)`。
- `evidence`：`list[EvidenceRef]`；默认 `Field(default_factory=list)`。
- `warnings`：`list[str]`；默认 `Field(default_factory=list)`。

**内部成员**：此类未直接定义方法；字段/继承行为见源码。


---
