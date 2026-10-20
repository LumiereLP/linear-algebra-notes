#!/usr/bin/env python3
"""把 icon/ 下的 SVG 图标转换为 TikZ 代码，生成 icons.tex.

用法（在仓库根目录）：
    python3 tools/svg2tikz.py icon/*.svg > icons.tex

约定（Illustrator 导出时请遵守，否则脚本会报错退出）：
  * 只用填充图形：path、polygon、rect、circle、ellipse；描边先“轮廓化描边”，文字先“创建轮廓”；
  * 不用剪切路径、蒙版、渐变、图案、<use> 引用；
  * fill="none" 的辅助图形会被跳过；其余图形一律按奇偶规则填充为当前颜色
    （颜色在 LaTeX 中决定，SVG 里的颜色不起作用）；
  * 画板为正方形（如 24 × 24），viewBox 从 0 0 开始.

生成的宏：\\lnicon@<文件名>，坐标单位为 viewBox 单位、y 轴向下；
由 document.tex 中的 \\lnicon[<高度>]{<文件名>} 缩放并对齐到文字基线.
"""
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

SVG_NS = '{http://www.w3.org/2000/svg}'
FORBIDDEN = {'clipPath', 'mask', 'linearGradient', 'radialGradient', 'pattern', 'use', 'image', 'text', 'filter'}
NUM = r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?'


def fail(msg):
    sys.exit('svg2tikz: ' + msg)


def fmt(x):
    s = f'{x:.3f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def parse_transform(t):
    """返回仿射矩阵 (a, b, c, d, e, f)：x' = a x + c y + e，y' = b x + d y + f."""
    m = (1, 0, 0, 1, 0, 0)
    for name, args in re.findall(r'(\w+)\s*\(([^)]*)\)', t or ''):
        v = [float(x) for x in re.findall(NUM, args)]
        if name == 'translate':
            n = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == 'scale':
            n = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == 'rotate':
            r = math.radians(v[0])
            cx, cy = (v[1], v[2]) if len(v) == 3 else (0, 0)
            c, s = math.cos(r), math.sin(r)
            n = (c, s, -s, c, cx - c * cx + s * cy, cy - s * cx - c * cy)
        elif name == 'matrix':
            n = tuple(v)
        else:
            fail(f'不支持的变换 {name}')
        a, b, c, d, e, f = m
        A, B, C, D, E, F = n
        m = (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D, a * E + c * F + e, b * E + d * F + f)
    return m


def apply(m, x, y):
    a, b, c, d, e, f = m
    return a * x + c * y + e, b * x + d * y + f


def polygon(points, m):
    pts = [apply(m, x, y) for x, y in points]
    return 'M ' + ' L '.join(f'{fmt(x)} {fmt(y)}' for x, y in pts) + ' Z'


def ellipse(cx, cy, rx, ry, m):
    # 四段三次贝塞尔近似
    k = 0.5522847498
    segs = [((cx + rx, cy), (cx + rx, cy + k * ry), (cx + k * rx, cy + ry), (cx, cy + ry)),
            (None, (cx - k * rx, cy + ry), (cx - rx, cy + k * ry), (cx - rx, cy)),
            (None, (cx - rx, cy - k * ry), (cx - k * rx, cy - ry), (cx, cy - ry)),
            (None, (cx + k * rx, cy - ry), (cx + rx, cy - k * ry), (cx + rx, cy))]
    p = lambda pt: ' '.join(fmt(v) for v in apply(m, *pt))
    out = 'M ' + p(segs[0][0])
    for s in segs:
        out += ' C ' + ' '.join(p(q) for q in s[1:])
    return out + ' Z'


def is_identity(m):
    return all(abs(x - y) < 1e-9 for x, y in zip(m, (1, 0, 0, 1, 0, 0)))


def compose(p, q):
    a, b, c, d, e, f = p
    A, B, C, D, E, F = q
    return (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D, a * E + c * F + e, b * E + d * F + f)


def convert(el, parent, out, fname):
    tag = el.tag.replace(SVG_NS, '')
    if tag in FORBIDDEN:
        fail(f'{fname}：含有 <{tag}>，请在 Illustrator 中扩展或释放后再导出')
    if tag in ('defs', 'style', 'title', 'desc', 'metadata'):
        if tag == 'defs' and len(el):
            fail(f'{fname}：<defs> 中有内容（可能是剪切路径或渐变）')
        return
    if el.get('clip-path') or el.get('mask') or el.get('filter'):
        fail(f'{fname}：<{tag}> 使用了剪切路径、蒙版或滤镜')
    m = compose(parent, parse_transform(el.get('transform')))
    if tag in ('svg', 'g'):
        for ch in el:
            convert(ch, m, out, fname)
        return
    if el.get('fill') == 'none' or 'fill:none' in (el.get('style') or '').replace(' ', ''):
        return
    g = lambda k, dflt=0.0: float(el.get(k, dflt))
    if tag == 'path':
        if not is_identity(m):
            fail(f'{fname}：<path> 带有变换，请在 Illustrator 中重置变换或取消编组后再导出')
        out.append(' '.join(el.get('d').split()))
    elif tag == 'polygon':
        v = [float(x) for x in re.findall(NUM, el.get('points'))]
        out.append(polygon(list(zip(v[0::2], v[1::2])), m))
    elif tag == 'rect':
        if el.get('rx') or el.get('ry'):
            fail(f'{fname}：圆角矩形请先扩展为路径')
        x, y, w, h = g('x'), g('y'), g('width'), g('height')
        out.append(polygon([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], m))
    elif tag == 'circle':
        out.append(ellipse(g('cx'), g('cy'), g('r'), g('r'), m))
    elif tag == 'ellipse':
        out.append(ellipse(g('cx'), g('cy'), g('rx'), g('ry'), m))
    else:
        fail(f'{fname}：不支持的元素 <{tag}>')


def main(files):
    print('% 自动生成，请勿手动修改：python3 tools/svg2tikz.py icon/*.svg > icons.tex')
    print('% 每个图标一个宏 \\lnicon@<文件名>，坐标为 SVG 的 viewBox 单位（y 轴向下），奇偶规则填充为当前颜色.')
    print('\\makeatletter')
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        if not re.fullmatch(r'[a-z]+', name):
            fail(f'{f}：文件名只能由小写字母组成（作为宏名的一部分）')
        root = ET.parse(f).getroot()
        vb = [float(x) for x in re.findall(NUM, root.get('viewBox', ''))]
        if len(vb) != 4 or vb[0] or vb[1] or abs(vb[2] - vb[3]) > 1e-6:
            fail(f'{f}：viewBox 应为从 0 0 开始的正方形')
        out = []
        convert(root, (1, 0, 0, 1, 0, 0), out, f)
        print(f'\\def\\lnicon@size@{name}{{{fmt(vb[2])}}}')
        print(f'\\def\\lnicon@{name}{{%')
        for d in out:
            print(f'\t\\fill[even odd rule] svg {{{d}}};%')
        print('}')
    print('\\makeatother')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        fail('用法：python3 tools/svg2tikz.py icon/*.svg > icons.tex')
    main(sys.argv[1:])
