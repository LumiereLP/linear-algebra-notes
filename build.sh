#!/usr/bin/env bash
# 编译流程：XeLaTeX -> biber -> makeindex -> XeLaTeX ×2（与本地编辑器的编译链一致）
# 本地也可直接运行：bash build.sh
set -euo pipefail

doc=document
tex() { xelatex -synctex=1 -interaction=nonstopmode -halt-on-error -file-line-error "$doc.tex"; }

tex
biber "$doc"
makeindex -l "$doc.idx"   # -l 与 imakeidx 的 options=-l 一致（按字母排序，忽略空格）
tex
tex
