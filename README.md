# 十五本书的投资笔记

根据公开仓库 [codeman008/Financial_freedom](https://github.com/codeman008/Financial_freedom) 中的 PDF 整理的简体中文静态网站。笔记讨论个人理财与投资原则，**不是**持牌金融建议。

本仓库不收录、也不转载那些 PDF。

## 本地预览

```bash
python3 -m unittest tests/test_build.py
python3 site/build.py
python3 -m http.server 8765 -d public
```

浏览器打开 `http://127.0.0.1:8765/`。测试会重新构建，并检查每本书的页面、站内链接、免责声明，以及图里出现的数字是否都在正文里。

## 页面

- `public/index.html`：十五本书的入口
- `public/books/`：分书笔记
- `public/synthesis.html`：共同原则、分歧和行动顺序

## 部署

`.github/workflows/pages.yml` 在推送到 `main` 时用 `actions/deploy-pages` 发布 `public/`。仓库若为私有，GitHub Pages 需要付费计划；启用失败时见该次提交说明。
