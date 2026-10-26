# 本地来源与变换记录

`fetch_public.py` 和 `sanitize_public.py` 会在本目录的 `local/` 子目录中写入下载、
脱敏、页面选择和哈希记录。记录不包含被遮盖的原值，也不包含服务器绝对路径。

`local/` 与公开二进制文件一样不进入 Git；可提交的来源、许可与锁定哈希位于：

- `../../manifests/public_sources.yaml`
- `../manifest.lock.json`
- `../licenses/README.md`
