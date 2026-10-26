# 公开真实材料

本目录只在 Git 中保存来源、许可、锁定哈希和脱敏规则。运行下载与脱敏工具后，实际文件会
出现在 `originals/`、`sanitized/` 和 `smoke/`，这些目录不会提交到 GitHub。

`manifest.lock.json` 中的哈希是安全边界。若官方站点替换文件，下载器会报告
`SOURCE_HASH_CHANGED`，不得用新文件覆盖旧锁而不做许可和内容复核。
