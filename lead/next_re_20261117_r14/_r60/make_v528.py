# -*- coding: utf-8 -*-
"""FACT_INDEX v5.28：
- 落盘 4,413 件清单（§2.53 那个值此前只存在于算式里）→ 现在有逐文件清单支撑
- 按 §2.61 裁定剔除 a2_sites.json 的 bounds 段 16,711,118 B（纯地址清单、86.19% 无字节对应）
- 语料值：4,413 件 / 744,172,839 B → 4,413 件 / 727,461,721 B
"""
import io, os, re, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R93_FACTINDEX_V527')
DST  = os.path.join(R14, 'R17_R98_FACTINDEX_V528')
os.makedirs(DST, exist_ok=True)

raw = io.open(os.path.join(SRC, 'FACT_INDEX.tsv'), encoding='utf-8', newline='').read()
assert '\r' not in raw
lines = raw.split('\n')
data = [l for l in lines[1:] if l.strip()]
assert len(data) == 54
rows = [l.split('\t') for l in data]
for r in rows:
    assert len(r) == 5
f24 = {r[0]: r for r in rows}['F24']

OLD = ('**对象证据集合（tier_final，本项唯一可引用的「语料」值）** = **4,413 文件 / 744,172,839 B '
       '= 0.744173 GB(10^9) = 0.693058 GiB(2^30)**')
NEW = ('**对象证据集合（tier_final，本项唯一可引用的「语料」值）** = **4,413 文件 / 727,461,721 B '
       '= 0.727462 GB(10^9) = 0.677502 GiB(2^30)**（逐文件清单 `tier_final_4413b.tsv`，回读 sum(bytes) 校验）')
assert OLD in f24[1], 'tier_final fragment not found'
new_stmt = f24[1].replace(OLD, NEW)
assert new_stmt != f24[1]

# 更新方向说明块（补 bounds 剔除这一步）
OLD2 = ('**本值已于 R53 按新口径重判后更新**（旧值 4,518 件 / 724,479,859 B）：'
        '构成 = P1a 3,786 件 / 714,228,639 B ∪ 逐件判为对象者 **627 件 / 29,944,200 B**（旧为 732 / 10,251,220 B）。')
NEW2 = ('**本值经 R53 重判、R54 落清单、R60 剔段三步**（溯源：4,518 件 / 724,479,859 B → 4,413 件 / 744,172,839 B → '
        '**4,413 件 / 727,461,721 B**）：构成 = P1a 3,786 件 / 714,228,639 B ∪ 逐件判为对象者 **627 件** '
        '（`tier_final_4413.tsv`，29,944,200 B）；再剔 `a2_sites.json` 的 **`bounds` 段 16,711,118 B**'
        '（纯指令起始 VA 清单、**86.19% 盘上无任何字节对应**、不满足「可回原址复核」）⇒ 该件 17,624,355 → 913,237 B，'
        '总量 −16,711,118 B。')
assert OLD2 in new_stmt, 'direction block not found'
new_stmt = new_stmt.replace(OLD2, NEW2)
assert new_stmt != f24[1]

ADD = ('**限定向附二·语料值已落盘并剔段（v5.28）**：`tier_final` 现有逐文件清单两份 —— '
       '`R17_R96_TIER_FINAL_4413\\tier_final_4413.tsv`（4,413 行 / 744,172,839 B，回读校验）与 '
       '`R17_R97_TIER_FINAL_4413B\\tier_final_4413b.tsv`（4,413 行 / **727,461,721 B**，回读校验）；'
       '**引用值取后者**。剔段依据：`a2_sites.json`（17,624,355 B）第二方法实测结构为 '
       '`calls`（地址↔地址关系，913,237 B，68,253/68,253 调用点**全部真回原址命中**）'
       '+ `bounds`（1,392,592 条纯指令起始 VA，16,711,118 B，**86.19% 无字节对应**）；'
       '按本项口径「记『地址里是什么字节/值』**且可回原址复核**」，`bounds` 不满足该「且」故剔除，`calls` 保留。'
       '**另记一次方法缺陷**：R53 那次重判的 `q2_rejudge.py:41,53` **只读前 1 MiB**（`rejudge1242.tsv:361` 的 '
       '`truncated=Y` 自证），对该件的「对象抄本」判定**实际样本仅 1/17**；`truncated=Y` 全表 **5 件**，'
       '其中判为对象抄本**仅 1 件**（即本件），故 627 件其余未受此缺陷影响。')
assert '\n' not in ADD
new_lim = f24[4].rstrip() + ADD
assert '语料值已落盘并剔段' in new_lim

f24[1] = new_stmt
f24[4] = new_lim
ADDS = [r'lead\next_re_20261117_r14\R17_R96_TIER_FINAL_4413\tier_final_4413.tsv',
        r'lead\next_re_20261117_r14\R17_R97_TIER_FINAL_4413B\tier_final_4413b.tsv',
        r'lead\next_re_20261117_r14\R17_R95_T1_A2SITES\REPORT.md']
for a in ADDS:
    assert a not in f24[3]
    assert os.path.isfile(os.path.join(ROOT, a.replace('\\', '/'))), a
    f24[3] = f24[3] + ';' + a

out = '\n'.join([lines[0]] + ['\t'.join(r) for r in rows]) + '\n'
assert '\r' not in out
for ch in ('\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0'):
    assert ch not in out
assert new_stmt.count('（') == new_stmt.count('）')
assert new_lim.count('（') == new_lim.count('）')
# 数字断言
assert 4413 == 3786 + 627
assert 714228639 + 29944200 == 744172839
assert 744172839 - 16711118 == 727461721
assert 17624355 - 16711118 == 913237

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
