# PrismKE 测试数据集

本目录提供两类互相隔离的数据：

- `synthetic/`：完全虚构、可提交 Git、可重复生成的完整研究报告式材料；同一篇连贯内容以多种格式呈现，并配套设备图、部署图、性能图表、扫描件和嵌套 JSON。
- `public/`：从官方来源下载的开放许可真实材料。原文件及派生二进制不进入 Git。

公开材料不是生产数据，也不应包含 PrismKE 的运行数据库、模型请求、密钥或密码。

## 生成与准备

在项目根目录执行：

```powershell
uv run python data/tools/generate_synthetic.py
uv run python data/tools/fetch_public.py --accept-licenses
uv run python data/tools/sanitize_public.py --level research-safe
uv run python data/tools/verify_dataset.py --strict
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
uv run python data/tools/import_local_html.py "C:\path\article.html" `
  --id example-news --private-research-use
```

测试时优先上传 `data/public/smoke/local-user-provided/*-sanitized.html`。原件、安全副本及
本地来源记录都不得提交或对外分发；只有导入工具和操作说明进入 Git。
