# -*- coding: utf-8 -*-
"""把 verify_out.json 里的 10 行体内自装明细渲染成 markdown 表，替换 VERDICT.md 的占位符。"""
import io, os, sys, json, bisect
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify as V

sizes = V.load_atlas()
ranges = V.body_ranges(sizes)
d = json.load(io.open(os.path.join(V.HERE, 'verify_out.json'), encoding='utf-8'))

lines = ['| entry | 行名 | 体内写点 | 体偏移 | 体内写点性质 | ④ 采用的 site（体外） | 坑② 处置 |',
         '|---|---|---|---:|---|---|---|']
n = 0
for r in d['rows']:
    if r['C2b']['n_in_entry_body'] == 0:
        continue
    e = int(r['entry'], 16)
    for w in r['C2b']['in_entry_body']:
        s = int(w['site'], 16)
        if w.get('delfree_sig'):
            kind = '**删除析构器体**（三特征齐备）'
        else:
            kind = '就地构造（无删除析构三特征）'
        lines.append('| `%s` | %s | `%s` | **+%d** | %s | `%s`（宿主 `%s`） | 已避开 ✓ |'
                     % (r['entry'], r['name'], w['site'], s - e, kind,
                        r['decl']['site'], r['site_func']))
        n += 1
print('rows rendered=%d' % n)

p = os.path.join(V.HERE, 'VERDICT.md')
txt = io.open(p, encoding='utf-8').read()
assert '<!--B4INBODY-->' in txt
txt = txt.replace('<!--B4INBODY-->', '\n'.join(lines))
io.open(p, 'w', encoding='utf-8', newline='\n').write(txt)
print('VERDICT.md patched, %d bytes' % len(txt.encode('utf-8')))
