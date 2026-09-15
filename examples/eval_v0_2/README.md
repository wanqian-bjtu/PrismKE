# PrismKE v0.2 公开多模态评测集

该目录包含 12 份由项目自行生成的中英文合成样例，不包含第三方版权材料或私人数据。
样例覆盖图文支持、图文冲突、图片独有事实、扫描 PDF、OCR 重复、证据定位和跨文档别名。

重新生成样例：

```bash
python examples/eval_v0_2/generate.py
```

使用 Mock 验证评测入口：

```bash
prismke evaluate examples/eval_v0_2/manifest.json \
  --output runtime/evaluation/mock-report.json \
  --provider mock
```

使用百炼真实模型：

```bash
prismke evaluate examples/eval_v0_2/manifest.json \
  --output runtime/evaluation/qwen3.7-flash-report.json \
  --provider openai-compatible \
  --ocr-provider paddle \
  --vlm-provider openai-compatible
```

真实报告默认写入已忽略的 `runtime/`。经过脱敏和人工核验的汇总结果再单独写入文档。
