# -*- coding: utf-8 -*-
"""FACT_INDEX v5.25：把 T1 的「应剔 1,468 件 / 149,493,508 B」登记进限定⑤附。
这是纪律 22（备份纪律产生语料污染）在 C′ 上的规模证据：516 件旧版副本 144,788,233 B，其中 LEDGER.before* 19 件 / 83,351,425 B。
不改区间（避免在「C′ 语义定义未定」时抢给数），只登记事实与剔除后值。
"""
import io, os, re, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R86_FACTINDEX_V524')
DST  = os.path.join(R14, 'R17_R87_FACTINDEX_V525')
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

ADD = ('【限定⑤附二·逐件核叙述体后的应剔清单（v5.25 补）】**应剔 1,468 件 / 149,493,508 B**'
       '（= C′ 字节的 11.0%）分三型：**旧版副本 516 件 / 144,788,233 B**（占应剔字节 96.9%；'
       '其中 `LEDGER.before*` 19 件 / 83,351,425 B、`GOAL*` 31 件 / 48,695,660 B——'
       '**这是纪律 22「备份纪律本身产生语料污染」在 C′ 上的规模证据**：C′ 把同几份台账的滚动副本按轮次重复计入"证据量"）、'
       '判词结论摘要 907 件 / 4,663,711 B、对象抄本的叙述式封装 45 件 / 41,564 B；另有 67 件 / 3,675,205 B 仍判不了单列。'
       '**若按此剔除，C′ = 17,244 件 / 1,214,215,212 B**——但同前述理由（C′ 语义定义未定）**本版不采用该值作引用值**，仅登记。'
       '另核：叙述体重算得 4,493 件 / 210,164,977 B，与上一轮 4,471 / 210,142,479 的差（+22 件 / +22,498 B）'
       '**全部来自 13:17:16 快照之后被重写的板面文件**（`STATUS_BOARD.md`/`BOARD_ARCHIVE.md`/`R14_COMMON.md`）——'
       '上一轮的做法是「用旧 rel 表、读当时盘上的文件」，故两次读数看到不同内容；本轮重录可复现。')
assert '\n' not in ADD
new_lim = f24[4].rstrip() + ADD
assert '应剔 1,468 件 / 149,493,508 B' in new_lim

f24[4] = new_lim
ADDS = [r'lead\next_re_20261117_r14\R17_R84_T1_NARRATIVE\REPORT.md']
for a in ADDS:
    assert a not in f24[3]
    assert os.path.isfile(os.path.join(ROOT, a.replace('\\', '/'))), a
    f24[3] = f24[3] + ';' + a

out = '\n'.join([lines[0]] + ['\t'.join(r) for r in rows]) + '\n'
assert '\r' not in out
for ch in ('\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0'):
    assert ch not in out, 'invisible U+%04X' % ord(ch)
assert new_lim.count('（') == new_lim.count('）'), (new_lim.count('（'), new_lim.count('）'))
# 数字断言
assert 516 + 907 + 45 == 1468
assert 144788233 + 4663711 + 41564 == 149493508
assert 18712 - 1468 == 17244 and 1363708720 - 149493508 == 1214215212
assert len(re.findall(r'【限定[①②③④⑤⑥⑦]·', new_lim)) == 7

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
