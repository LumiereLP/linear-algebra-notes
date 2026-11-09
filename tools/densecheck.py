#!/usr/bin/env python3
"""排版宽松化检查：按章列出
  (1) 行内公式过密的段落（每百个汉字超过 8 个行内公式）；
  (2) 含“高”结构的行内公式（分式、求和、求积、积分、矩阵、组合数、极限）；
  (3) 源码过长的单行行间公式（\\[...\\] 或 equation 中不含 aligned/align/cases 且超过 90 个字符）.
脚注、tikz 图、栏目（historybox/modelbox/codebox/linkbox/motivebox/pitfallbox）中的内容单独标出.

用法：python3 tools/densecheck.py 章标签     例如 python3 tools/densecheck.py ch:elimination
"""
import re, sys, os

HIGH = re.compile(r'\\(d?frac|tfrac|sum|prod|int|binom|lim|begin\{(p|b|v|V)?matrix\}|sqrt\{[^}]{4,})')
BOXES = ('historybox', 'modelbox', 'codebox', 'linkbox', 'motivebox', 'pitfallbox', 'tikzpicture')

def expand(path):
    src = open(path, encoding='utf-8').read()
    return re.sub(r'\\input\{(chapters/\w+)\}', lambda m: open(m.group(1) + '.tex', encoding='utf-8').read(), src)

def chapter_lines(label):
    lines = expand('document.tex').split('\n')
    start = next(i for i, l in enumerate(lines) if '\\label{%s}' % label in l and '\\chapter' in l)
    end = next((i for i in range(start + 1, len(lines)) if re.search(r'\\chapter\*?\{', lines[i])), len(lines))
    return start, lines[start:end]

def where(stack):
    return '（' + '/'.join(stack) + '）' if stack else ''

def main():
    label = sys.argv[1]
    start, lines = chapter_lines(label)
    stack = []
    dense, high, longd = [], [], []
    para, pstart = [], None
    def flush():
        nonlocal para, pstart
        if para:
            text = ' '.join(para)
            n_inline = len(re.findall(r'(?<!\\)\$[^$]+\$', text))
            n_cjk = len(re.findall(r'[\u4e00-\u9fff]', re.sub(r'\$[^$]*\$', '', text)))
            if n_cjk >= 40 and n_inline * 100 / n_cjk > 8:
                dense.append((pstart, n_inline, n_cjk, where(stack)))
        para, pstart = [], None
    i = 0
    while i < len(lines):
        raw = lines[i]; no = start + i + 1
        code = re.sub(r'(?<!\\)%.*', '', raw)
        for b in re.findall(r'\\begin\{(\w+)\}', code):
            if b in BOXES: stack.append(b)
        # 行间公式
        m = re.search(r'\\\[|\\begin\{equation\*?\}', code)
        if m:
            j = i; body = code[m.end():]
            endpat = r'\\\]' if code[m.start():m.start()+2] == '\\[' else r'\\end\{equation\*?\}'
            while not re.search(endpat, body) and j + 1 < len(lines):
                j += 1; body += '\n' + re.sub(r'(?<!\\)%.*', '', lines[j])
            body = re.split(endpat, body)[0]
            flat = re.sub(r'\s+', ' ', body).strip()
            if '\\\\' not in body and not re.search(r'aligned|align|cases|array|matrix|NiceArray', body) and len(flat) > 90:
                longd.append((no, len(flat), where(stack), flat[:70]))
            flush(); i = j + 1
            continue
        if not code.strip():
            flush()
        else:
            if pstart is None: pstart = no
            para.append(code)
            for f in re.findall(r'(?<!\\)\$([^$]+)\$', code):
                if HIGH.search(f):
                    high.append((no, where(stack), f[:60]))
        for b in re.findall(r'\\end\{(\w+)\}', code):
            if b in BOXES and stack: stack.pop()
        i += 1
    flush()
    print('== 行内公式过密的段落（行号 / 行内公式数 / 汉字数）')
    for x in dense: print('  %d  %d/%d %s' % x)
    print('== 高结构的行内公式')
    for x in high: print('  %d %s  $%s$' % x)
    print('== 过长的单行行间公式（行号 / 字符数）')
    for x in longd: print('  %d  %d %s  %s' % x)
    print('合计：过密段落 %d，高结构行内公式 %d，过长行间公式 %d' % (len(dense), len(high), len(longd)))

if __name__ == '__main__':
    main()
