# -*- coding: utf-8 -*-
"""FACT_INDEX v5.30：语料值第五次演进 + 写入「同一批 68,253 对出现在 4 个文件」的口径限定
4,416 / 736,151,921 B → 4,417 / 737,517,286 B（+ scan_mine 1,365,365）
"""
import io, os, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R100_FACTINDEX_V529')
DST  = os.path.join(R14, 'R17_R102_FACTINDEX_V530')
os.makedirs(DST, exist_ok=True)

raw = io.open(os.path.join(SRC, 'FACT_INDEX.tsv'), encoding='utf-8', newline='').read()
assert '\r' not in raw
lines = raw.split('\n')
data = [l for l in lines[1:] if l.strip()]
assert len(data) == 54
rows = [l.split('\t') for l in data]
f24 = {r[0]: r for r in rows}['F24']

OLD = ('**对象证据集合（tier_final，本项唯一可引用的「语料」值）** = **4,416 文件 / 736,151,921 B '
       '= 0.736152 GB(10^9) = 0.685595 GiB(2^30)**（逐文件清单 `tier_final_4416.tsv`，回读 sum(bytes) 校验）')
NEW = ('**对象证据集合（tier_final，本项唯一可引用的「语料」值）** = **4,417 文件 / 737,517,286 B '
       '= 0.737517 GB(10^9) = 0.686866 GiB(2^30)**（逐文件清单 `tier_final_4417.tsv`，回读 sum(bytes) 校验）；'
       '**此值测的是「磁盘体量」，不是「证据独立性」** —— 二者口径不同，详见 `limitations`')
assert OLD in f24[1]
new_stmt = f24[1].replace(OLD, NEW)
assert new_stmt != f24[1]

OLD2 = '**R62/R63 再翻三件为对象侧**'
NEW2 = '**R62/R63/R64 再翻四件为对象侧**'
assert OLD2 in new_stmt
new_stmt = new_stmt.replace(OLD2, NEW2, 1)

OLD3 = '`e8_sites_audit.json` 1,365,087 B（68,253 地址对，已验 `E8` 调用）⇒ 合计 **+8,690,200 B**。'
NEW3 = ('`e8_sites_audit.json` 1,365,087 B（68,253 地址对，已验 `E8` 调用）、'
        '`scan_mine.json` 1,365,365 B（同 68,253 对 + 11 个元数据/计数键）⇒ 合计 **+10,055,565 B**。')
assert OLD3 in new_stmt
new_stmt = new_stmt.replace(OLD3, NEW3, 1)

ADD = ('**限定向附四·重复产出与两个口径（v5.30）**：**同一批 68,253 个调用点对出现在 4 个文件里** —— '
       '`a2_sites.json` 的 `calls`（十六进制字符串编码，序列化 838,248 B、占该件 4.8%）、'
       '`scan_mine.json` 的 `calls`（十进制整数，**1,228,582 B / 90.0%**）、'
       '`e8_sites_audit.json`（顶层 list，**1,228,582 B / 100%**）、'
       '`sweep.json` 的 `e8`（**1,228,582 B / 75.3%**，另有 `installs` 6,226 条 / 248,114 B 属独有内容）；'
       '三份 `calls` 的序列化长度**逐字节相同**，`a2_sites` 那份归一化后集合亦完全相同。'
       '⇒ **「磁盘体量」计 4 份、「证据独立性」只算 1 份**，本值取前者（它测的就是磁盘体量）；'
       '**引用时必须说明取哪个口径**；`e8_sites_audit.json` **100% 是这份重复内容、无独有对象内容**，'
       '**只能作为「磁盘体量」计入，不能作为独立证据**。'
       '**归因要点**：这是**三张不同的卡各自做了同一次扫描、各落一份盘**（重复产出），'
       '不是 `LEDGER.before_*` 那类「同一份台账被我备份 N 次」（滚动备份）；'
       '两者处置相同（声明重复量）但归因不同，混为一谈会得出「应禁止跨卡重复扫描」这种错误结论。')
assert '\n' not in ADD
new_lim = f24[4].rstrip() + ADD
assert '重复产出与两个口径' in new_lim

f24[1] = new_stmt
f24[4] = new_lim
ADDS = [r'lead\next_re_20261117_r14\R17_R101_TIER_FINAL_4417\tier_final_4417.tsv']
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
assert 4416 + 1 == 4417
assert 736151921 + 1365365 == 737517286
assert 5693169 + 1631944 + 1365087 + 1365365 == 10055565

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
