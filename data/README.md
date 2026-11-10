# PrismKE 测试数据集

本目录提供两类互相隔离的数据：

- `synthetic/`：完全虚构、可提交 Git、可重复生成的完整研究报告式材料；同一篇连贯内容以多种格式呈现，并配套设备图、部署图、性能图表、扫描件和嵌套 JSON。
- `public/`：从官方来源下载的开放许可真实材料。原文件及派生二进制不进入 Git。
- `benchmarks/`：用户为论文评估准备的标准研究基准。数据本体不进入 Git，仅在本地与受控服务器保存；Git 只记录来源、数量、异常策略和逐文件 SHA-256。

公开材料不是生产数据，也不应包含 PrismKE 的运行数据库、模型请求、密钥或密码。

## 生成与准备

在项目根目录执行：

```powershell
uv run python -m data.tools.generate_synthetic
uv run python -m data.tools.fetch_public --accept-licenses
uv run python -m data.tools.sanitize_public --level research-safe
uv run python -m data.tools.verify_dataset --strict
```

数据准备本身不需要 GPU。只有使用真实 MinerU 或 VLM 执行解析和抽取时才建议使用 GPU 服务器。

## 目录边界

`public/originals/` 保存官方原文件，`public/sanitized/` 保存研究安全型副本，
`public/smoke/` 保存最多十二页的日常测试子集。三者都由 `.gitignore` 排除。
`manifests/public_sources.yaml` 描述来源与许可，`public/manifest.lock.json` 锁定源文件
SHA-256。上游文件变化时下载器会停止，必须人工复核后才能更新锁文件。

## 脱敏规则

研究安全型处理会移除文档元数据、嵌入附件、JavaScript、表单动作和链接，遮盖可识别的
邮箱、电话号码、通信地址、签名区域和二维码候选。公开作者姓名、机构名、正文、图表以及
许可覆盖的公开照片予以保留。带明确第三方版权标记且无法确认兼容许可的图片会被遮盖。

每个派生文件都有不含原值的变换报告。报告只记录规则、页码、数量、源哈希和派生哈希。

## 使用建议

- 日常功能验证优先使用 `public/smoke/`，避免完整年报产生过高解析和模型费用。
- 压力测试才使用 `public/sanitized/` 中的完整报告。
- 使用真实模型前单独确认调用预算；默认测试只使用 Mock Provider。
- 引用公开材料时遵守 `public/licenses/` 中记录的许可和署名要求。

## 用户自备、不可再分发的 HTML

带明确版权但没有开放许可的新闻网页，可以用于用户自己的内部研究测试，但不能加入 GitHub
公开数据清单。使用下面的命令会把原件放入被 Git 忽略的 `originals/local-user-provided/`，
并生成移除脚本、广告、追踪器、表单、远程图片和页面状态的文本型安全副本：

```powershell
uv run python -m data.tools.import_local_html "C:\path\article.html" `
  --id example-news --private-research-use --include-images
```

测试时优先上传 `data/public/smoke/local-user-provided/*-sanitized.html`。原件、安全副本及
本地来源记录都不得提交或对外分发；只有导入工具和操作说明进入 Git。如果页面图片来自
允许列表中的官方媒体域名，`--include-images` 会保存本地图片、保留说明和署名，并额外生成
一个可单文件上传的 `*-multimodal.pdf`。图片版权状态不会因下载或格式转换而改变。

## 论文评估基准

Twitter-2017 与 MNRE-V2 保存在 `data/benchmarks/`，其规范相对路径、数据来源、划分数量和
校验清单记录在 `manifests/evaluation_benchmarks.yaml`。原始数据受数据集提供方及 Twitter/X
相关条款约束，不随 PrismKE 仓库分发。

Twitter-2017 的公开图片包包含已知失效图片。原文件必须原样保留，文件名和失败类型记录在
`manifests/benchmarks/twitter2017.invalid-images.json`；加载失败时应统一回退到明确的占位图，
不得静默删除对应样本或改变训练、验证、测试划分。

MNRE-V2 的关系抽取评测使用独立案例库，不写入生产 `runtime/cases.sqlite`。Schema 将数据集
标签映射到规范实体与关系名称，原始标签仅作为评测别名。训练和验证中的测试文本重复项及
同文本、同有向实体对的跨划分冲突项不得进入案例库；固定排除清单记录在
`manifests/benchmarks/mnre-v2.case-library-exclusions.json`。执行顺序为：

```powershell
uv run prismke mnre-v2 prepare
uv run prismke mnre-v2 caption --smoke
uv run prismke mnre-v2 caption
uv run prismke mnre-v2 embed
uv run prismke mnre-v2 run-dev
uv run prismke mnre-v2 run-holdout
uv run prismke mnre-v2 finalize-library
uv run prismke mnre-v2 run-test
```

验证阶段只从训练案例检索；提示词冻结并完成验证复核后，才允许将清理后的完整验证集加入
最终案例库。测试集不得用于提示词选择、案例检索库构建或配置调整。

准备或搬迁数据后执行以下命令重新验证数量、引用、可解码性并生成逐文件校验清单：

```powershell
py data/tools/prepare_evaluation_benchmarks.py `
  --twitter-root data/benchmarks/twitter2017 `
  --mnre-root data/benchmarks/mnre-v2 `
  --manifest-dir data/manifests/benchmarks
```
