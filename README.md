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
bash build.sh            # 屏幕彩色（默认）-> document.pdf
bash build.sh print      # 印刷彩色（含出血）-> document-print.pdf
bash build.sh printbw    # 印刷黑白 -> document-bw.pdf
```

在编辑器中编译时，默认得到屏幕彩色版；要切换模式，可在 `document.tex` 第一行之前临时写 `\def\notemode{printbw}`。

## 颜色

全书颜色统一在 `colors.tex` 中定义（主色、图中的类别色、建模案例标记、六类栏目框）。
正文和图中只使用其中的语义色名以及中性色 `black`、`white`、`gray!N`，不要直接写 `red!4` 之类的具体颜色；
改配色、调整黑白版的灰度，都只改 `colors.tex`。
