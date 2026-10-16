#!/usr/bin/env bash
# 编译流程：XeLaTeX -> biber -> makeindex -> XeLaTeX ×2（与本地编辑器的编译链一致）
# 用法：bash build.sh [screen|print|printbw]
#   screen   屏幕彩色（默认）  -> document.pdf
#   print    印刷彩色          -> document-print.pdf
#   printbw  印刷黑白          -> document-bw.pdf
# 输出模式的含义见 document.tex 开头的 \notemode.
set -euo pipefail

mode=${1:-screen}
case "$mode" in
	screen)  job=document ;;
	print)   job=document-print ;;
	printbw) job=document-bw ;;
	*) echo "用法：bash build.sh [screen|print|printbw]" >&2; exit 1 ;;
esac

opts=(-synctex=1 -interaction=nonstopmode -halt-on-error -file-line-error)
if [ "$mode" = screen ]; then
	tex() { xelatex "${opts[@]}" document.tex; }
else
	tex() { xelatex "${opts[@]}" -jobname="$job" "\\def\\notemode{$mode}\\input{document.tex}"; }
fi

tex
biber "$job"
makeindex -l "$job.idx"   # -l 与 imakeidx 的 options=-l 一致（按字母排序，忽略空格）
tex
tex
