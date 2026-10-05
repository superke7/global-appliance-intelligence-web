# GitHub Pages 公开站架构

公开站采用纯静态架构：

```text
公开版 public-batch.json
        ↓
public-batches/YYYYMMDD/
        ↓
scripts/build-pages.py
        ↓
_site/
        ↓
GitHub Pages
```

公开仓库只接收已经完成公开字段过滤和复核的 JSON。任何内部字段不得先进入公开仓库再依赖前端隐藏。
