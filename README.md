# 全球家电AI早报公开站

这是“全球家电AI早报”的公开网站仓库，仅保存面向公众发布的静态站构建代码和公开数据。

## 目录

- `public-batches/YYYYMMDD/public-batch.json`：按北京时间归档的公开资讯批次；
- `scripts/build-pages.py`：把公开 JSON 构建为静态网页、事件数据库和 RSS；
- `.github/workflows/deploy-pages.yml`：GitHub Pages 自动部署。

## 发布方式

当 `main` 分支中的 `public-batches/**` 或站点构建脚本发生变化时，GitHub Actions 自动构建并部署 GitHub Pages。

站点地址：

https://superke7.github.io/global-appliance-intelligence-web/

## 数据边界

本仓库只允许公开信息进入。不得提交内部分析、内部备注、凭据、服务器配置、私有数据或未公开字段。
