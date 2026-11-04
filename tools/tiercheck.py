#!/usr/bin/env python3
"""学时依赖检查：找出低档内容引用高档内容的地方.

档位：0 = 无标记（48 学时起），1 = \\hB（72 学时起），2 = \\hC（仅 96 学时），3 = *（选读）.
一节（小节）的档位取它自己的标记；没有标记时继承上一级. 章标题带 * 的整章为选读.
\\label 记录所在位置的档位；\\ref、\\eqref、\\pageref 若指向档位更高的标签就报告.
整章不在 48 学时方案中的（\\chapterhours 第一项为“—”），章首部分按该章最低的档位计.
行末注释含“% tier-ok”的行视为作者已确认，不再报告. 章末习题与习题答案不检查（未讲授的题目可以跳过）. 栏目（历史回响、建模实验、计算实践）中的引用单独标出，供作者判断.

用法：python3 tools/tiercheck.py [document.tex]
"""
import re, sys, os

TIERS = ['无标记', '†', '‡', '*']
SIDE_BOXES = ('historybox', 'modelbox', 'codebox')

def expand(path):
    base = os.path.dirname(path)
    src = open(path, encoding='utf-8').read()
    def sub(m):
        p = os.path.join(base, m.group(1) + ('' if m.group(1).endswith('.tex') else '.tex'))
        return expand(p) if os.path.exists(p) else m.group(0)
    return re.sub(r'^[^%\n]*?\\input\{([^}]+)\}', lambda m: m.group(0).split('\\input')[0] + sub(m), src, flags=re.M)

def marker(title):
    t = title.strip()
    if t.startswith('\\hC'): return 2
    if t.startswith('\\hB'): return 1
    if t.startswith('*'): return 3
    return None

def clean(t):
    t = re.sub(r'\\label\{[^}]*\}.*', '', t)
    t = re.sub(r'\\texorpdfstring\{[^}]*\}\{([^}]*)\}', r'\1', t)
    return t.rstrip('} ')[:28]

def main():
    doc = sys.argv[1] if len(sys.argv) > 1 else 'document.tex'
    lines = expand(doc).split('\n')
    chap = sec = sub = 0
    chapname = secname = ''
    skip = False
    labels, refs = {}, []
    boxes = []
    for no, line in enumerate(lines, 1):
        code = re.sub(r'(?<!\\)%.*', '', line)
        m = re.search(r'\\chapter\*?\{(.*)', code)
        if m:
            chap = 3 if m.group(1).lstrip().startswith('*') else 0
            sec = sub = chap; chapname = clean(m.group(1)); secname = ''
            skip = '习题答案' in chapname
        m = re.search(r'\\chapterhours\{([^}]*)\}\{([^}]*)\}', code)
        if m and chap == 0:
            chap = 2 if m.group(2).strip() == '—' else 1 if m.group(1).strip() == '—' else 0
            sec = sub = chap
        m = re.search(r'\\section\*?\{(.*)', code)
        if m:
            k = marker(m.group(1)); sec = sub = chap if k is None else max(chap, k); secname = clean(m.group(1))
        m = re.search(r'\\subsection\*?\{(.*)', code)
        if m:
            k = marker(m.group(1)); sub = sec if k is None else max(sec, k)
        for b in re.findall(r'\\begin\{(\w+)\}', code):
            if b in SIDE_BOXES: boxes.append(b)
        for b in re.findall(r'\\end\{(\w+)\}', code):
            if b in SIDE_BOXES and boxes: boxes.pop()
        for lab in re.findall(r'\\label\{([^}]+)\}', code):
            labels[lab] = (sub, chapname, secname)
        if skip or secname.startswith('章末习题') or '% tier-ok' in line: continue
        for cmd, lab in re.findall(r'\\(ref|eqref|pageref)\{([^}]+)\}', code):
            refs.append((no, sub, lab, boxes[-1] if boxes else '', chapname, secname))
    out = []
    for no, tier, lab, box, cn, sn in refs:
        if lab not in labels or lab.startswith('ex:'): continue
        t = labels[lab][0]
        bad = (t == 3 and tier != 3) or (t < 3 and tier < 3 and t > tier)
        if bad:
            out.append(f'[{TIERS[tier]} → {TIERS[t]}] {lab}  在「{cn} / {sn}」{"（"+box+"）" if box else ""}  →  目标在「{labels[lab][1]} / {labels[lab][2]}」')
    print('\n'.join(out) if out else '没有发现低档引用高档的地方.')
    print(f'\n共 {len(out)} 处.')

if __name__ == '__main__':
    main()
