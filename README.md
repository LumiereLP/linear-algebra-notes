# linear-algebra-notes
高等代数讲义

- 在线阅读 / 下载：<https://lumierelp.github.io/notes/>
- PDF 直链：<https://lumierelp.github.io/linear-algebra-notes/linear-algebra.pdf>

## 自动编译

推送后，GitHub Actions 运行 `build.sh` 编译 `document.tex`（模板 ElegantBook），
流程为 XeLaTeX → biber → makeindex → XeLaTeX ×2：

- 任意分支：编译结果在该次 Actions 运行的 Artifacts 里，可下载检查。
- `main` 分支：同时发布到 GitHub Pages，主页讲义页自动更新。

首次使用需在仓库 Settings → Pages → Source 选择 **GitHub Actions**。

## 版本与日期

- 版本号：改 `document.tex` 顶部的 `\noteversion`。
- 日期：`\notedate`，由 CI 设为**最后一次提交的日期**，不需要手写；本地编译时为当天日期。
- 封面：`cover.pdf`（Illustrator 导出）不写版本和日期；编译时由 LaTeX 把「版本 \noteversion / 编译日期 \notedate」
  叠加到右下角蓝色色块上，位置在 `document.tex` 封面部分的坐标里微调。

## 本地编译

```bash
bash build.sh     # 或在编辑器中按同样顺序编译
```
