# -*- coding: utf-8 -*-
"""FACT_INDEX v5.21：修 T4 审计查出的三处 F24 缺陷。
① statement「被排 6,011」把 UNDECIDED 混进 EXCL ⇒ 拆回 4,769 + 1,242（与 limitation② 一致）；
② limitations 缺「C′ 分类含内容级判据、换人重跑可能不一致、本轮未复算逐件分类理由」；
③ 补一句「恒等式只证三桶构成档 A 的划分、不证逐件归类正确」。
"""
import io, os, re, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R80_FACTINDEX_V520')
DST  = os.path.join(R14, 'R17_R82_FACTINDEX_V521')
os.makedirs(DST, exist_ok=True)

raw = io.open(os.path.join(SRC, 'FACT_INDEX.tsv'), encoding='utf-8', newline='').read()
assert '\r' not in raw
lines = raw.split('\n')
data = [l for l in lines[1:] if l.strip()]
assert len(data) == 54
rows = [l.split('\t') for l in data]
for r in rows:
    assert len(r) == 5, (r[0], len(r))
f24 = {r[0]: r for r in rows}['F24']

OLD_FRAG = ('**我独立复算：C′ + 被排 6,011 / 226,255,638 B = 24,723 / 1,589,964,358 B，与档 A 精确闭合**。')
NEW_FRAG = ('**我独立复算：C′ + 被排（EXCL）4,769 / 179,570,859 B + 无法判定（UNDECIDED）1,242 / 46,684,779 B '
            '= 24,723 / 1,589,964,358 B，与档 A 精确闭合**；'
            '**但这个恒等式只证明三桶构成档 A 的一个划分（不重不漏），不证明逐件归类正确**——'
            '互换错（A 桶一件与 B 桶一件对调）既不产生漏项也不产生重项，照样通过恒等式；'
            '盘上等字节跨桶候选对实测上万对（最大一例两侧同为 237,273 B），构造互换错随手可得。')
assert OLD_FRAG in f24[1], 'fragment not found'
new_stmt = f24[1].replace(OLD_FRAG, NEW_FRAG)
assert new_stmt != f24[1]

ADD_LIM = ('**C′ 的三条限定之外还有两条必须同引**：④它的分类判据含**内容级判断**'
           '（前 8 KiB 取行首 VA 比例、横幅特征、判决顺序 L0→L4 等），**换人重跑可能不一致**；'
           '本轮我只复算了清单求和与三桶恒等式，**未复算它对每一件的分类理由**，故不得把 C′ 读作「分类已被核过」；'
           '⑤上述恒等式只证「三桶是档 A 的一个划分」，**不证逐件归对**（互换错可通过）。')
assert '\n' not in ADD_LIM
new_lim = f24[4].rstrip() + ADD_LIM
assert 'C′ 的三条限定之外还有两条' in new_lim

f24[1] = new_stmt
f24[4] = new_lim
ADDS = [r'lead\next_re_20261117_r14\R17_R81_T4_AUDIT32\REPORT.md']
for a in ADDS:
    assert a not in f24[3]
    assert os.path.isfile(os.path.join(ROOT, a.replace('\\', '/'))), a
    f24[3] = f24[3] + ';' + a

out = '\n'.join([lines[0]] + ['\t'.join(r) for r in rows]) + '\n'
assert '\r' not in out
for ch in ('\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0'):
    assert ch not in out, 'invisible U+%04X' % ord(ch)
assert new_stmt.count('（') == new_stmt.count('）'), (new_stmt.count('（'), new_stmt.count('）'))
assert 4769 + 1242 == 6011 and 179570859 + 46684779 == 226255638

dst = os.path.join(DST, 'FACT_INDEX.tsv')
assert not os.path.exists(dst)
with open(dst, 'x', encoding='utf-8', newline='') as f:
    f.write(out)

back = io.open(dst, encoding='utf-8', newline='').read()
assert back == out
assert back.count('\n') == 55 and back.count('\t') == 55 * 4
brows = [l.split('\t') for l in back.split('\n')[1:] if l.strip()]
assert len(brows) == 54
for a, b in zip(rows, brows):
    assert a[0] == b[0] and len(b) == 5
    if a[0] != 'F24':
        assert a == b, 'unexpected change ' + a[0]
dist = {}
for b in brows:
    dist[b[2]] = dist.get(b[2], 0) + 1
assert dist.get('[已证]') == 27 and dist.get('[静态推断]') == 1 and dist.get('未取得') == 2 and dist.get('[流程]') == 24

print('OK', dst, os.path.getsize(dst), 'bytes')
print('sha256 =', hashlib.sha256(back.encode()).hexdigest().upper())
print('grade dist =', dist, '; F24 evidence items =', len(f24[3].split(';')))
