# -*- coding: utf-8 -*-
"""生成 FACT_INDEX v5.14：
 1) F29 limitations：把「导入布局非原版」这句从含糊改为**实测三件**（ILT/IBN 在 .detour、IAT 在 .rdata、槽内容在 .text），
    并写明「不得用 IAT 槽值反推真实函数体」；同时更正我 R37 自己的错误说法来源。
 2) F14 evidence_paths：加 T2 的直接计数产物（383/377 由推导值升为直接计数）。
纪律：读 v5.13 → 逐行断言只有目标行变化 → wx 独占创建 → 回读校验 → 禁零宽字符。
"""
import io, os, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R69_FACTINDEX_V513')
DST  = os.path.join(R14, 'R17_R71_FACTINDEX_V514')
os.makedirs(DST, exist_ok=True)

raw = io.open(os.path.join(SRC, 'FACT_INDEX.tsv'), encoding='utf-8', newline='').read()
assert '\r' not in raw
lines = raw.split('\n')
assert lines[0].split('\t') == ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations']
data = [l for l in lines[1:] if l.strip()]
assert len(data) == 54

F29_OLD = ('引用时不必再写「未经字节证实」，但须同时声明本镜像多出非标准 `.detour` 节、导入布局非原版')
F29_NEW = ('引用时不必再写「未经字节证实」，但须同时声明本镜像导入布局非原版——实测三件：'
           '① ILT 与 IMAGE_IMPORT_BY_NAME 名字区在 `.detour` 节（339/339）；'
           '② IAT 数组本身在 `.rdata`（339/339）；'
           '③ IAT 槽内容（绑定的 0x40F9xx 类地址）落在 `.text`（339/339）——'
           '故**不得用 IAT 槽值反推真实函数体地址**，导入名只能从 `.detour` 的明文 IBN 读')

F14_EV_ADD = r'lead\next_re_20261117_r14\R17_R70_T2_RTTIONLY\REPORT.md'

out_rows, changed = [], []
for l in data:
    c = l.split('\t')
    assert len(c) == 5
    if c[0] == 'F29':
        assert F29_OLD in c[4], 'F29 limitation anchor text not found'
        new = c[4].replace(F29_OLD, F29_NEW)
        assert new != c[4]
        changed.append(('F29', 'limitations', new))
        c[4] = new
    elif c[0] == 'F14':
        assert 'R17_R70_T2_RTTIONLY' not in c[3]
        c[3] = c[3] + ';' + F14_EV_ADD
        changed.append(('F14', 'evidence_paths', '(加 T2 直接计数产物)'))
    out_rows.append('\t'.join(c))

assert len(changed) == 2, len(changed)

out = '\n'.join([lines[0]] + out_rows) + '\n'
assert '\r' not in out
for ch in ('\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0'):
    assert ch not in out, 'invisible char U+%04X' % ord(ch)

dst = os.path.join(DST, 'FACT_INDEX.tsv')
assert not os.path.exists(dst)
with open(dst, 'x', encoding='utf-8', newline='') as f:
    f.write(out)

back = io.open(dst, encoding='utf-8', newline='').read()
assert back == out
assert back.count('\n') == 55 and back.count('\t') == 55 * 4
backrows = [l for l in back.split('\n')[1:] if l.strip()]
assert len(backrows) == 54
for a, b in zip(data, backrows):
    fa = a.split('\t')[0]
    assert fa == b.split('\t')[0]
    if fa not in ('F29', 'F14'):
        assert a == b, 'unexpected change ' + fa
dist = {}
for b in backrows:
    g = b.split('\t')[2]
    dist[g] = dist.get(g, 0) + 1
assert dist.get('[已证]') == 27 and dist.get('[静态推断]') == 1 and dist.get('未取得') == 2 and dist.get('[流程]') == 24

print('OK', dst, 'bytes =', os.path.getsize(dst))
print('sha256 =', hashlib.sha256(back.encode()).hexdigest().upper())
print('grade dist =', dist, '; changed =', len(changed))
