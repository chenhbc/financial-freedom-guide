# 最终财富自由

根据公开仓库 [codeman008/Financial_freedom](https://github.com/codeman008/Financial_freedom) 中的 PDF 整理的一份简体中文报告。讨论个人理财与投资原则，**不是**持牌金融建议。

本仓库不收录、也不转载那些 PDF。

## 本地预览

```bash
python3 -m pip install -r requirements.txt
python3 site/build.py
python3 -m http.server 8765 -d public
```

构建时用 fontTools 按页面实际用到的楷体字，从霞鹜文楷 v1.522 切出 woff2。来源和版本见 `site/fonts/SOURCE.md`。

浏览器打开 `http://127.0.0.1:8765/`。

## 页面

- `public/index.html`：《最终财富自由》
- `public/report.html`：转到首页

## 部署

`.github/workflows/pages.yml` 在推送到 `main` 时用 `actions/deploy-pages` 发布 `public/`。仓库若为私有，GitHub Pages 需要付费计划；启用失败时见该次提交说明。
