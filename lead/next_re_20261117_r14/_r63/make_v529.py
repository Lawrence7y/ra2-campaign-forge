# -*- coding: utf-8 -*-
"""FACT_INDEX v5.29：语料值按 R62/R63 重判更新
4,413 / 727,461,721 B → 4,416 / 736,151,921 B
+ mesh_imm32.json 5,693,169（双控可回原址）
+ sweep.json 1,631,944（e8 地址对 + installs 寻址模式+值；§2.68 改正了文件混淆）
+ e8_sites_audit.json 1,365,087（68,253 地址对，已验）
"""
import io, os, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R98_FACTINDEX_V528')
DST  = os.path.join(R14, 'R17_R100_FACTINDEX_V529')
os.makedirs(DST, exist_ok=True)

raw = io.open(os.path.join(SRC, 'FACT_INDEX.tsv'), encoding='utf-8', newline='').read()
assert '\r' not in raw
lines = raw.split('\n')
data = [l for l in lines[1:] if l.strip()]
assert len(data) == 54
rows = [l.split('\t') for l in data]
f24 = {r[0]: r for r in rows}['F24']

OLD = ('**对象证据集合（tier_final，本项唯一可引用的「语料」值）** = **4,413 文件 / 727,461,721 B '
       '= 0.727462 GB(10^9) = 0.677502 GiB(2^30)**（逐文件清单 `tier_final_4413b.tsv`，回读 sum(bytes) 校验）')
NEW = ('**对象证据集合（tier_final，本项唯一可引用的「语料」值）** = **4,416 文件 / 736,151,921 B '
       '= 0.736152 GB(10^9) = 0.685595 GiB(2^30)**（逐文件清单 `tier_final_4416.tsv`，回读 sum(bytes) 校验）')
assert OLD in f24[1]
new_stmt = f24[1].replace(OLD, NEW)
assert new_stmt != f24[1]

OLD2 = '**本值经 R53 重判、R54 落清单、R60 剔段三步**'
NEW2 = '**本值经 R53 重判、R54 落清单、R60 剔段、R62/R63 三件翻对象侧四步**'
assert OLD2 in new_stmt
new_stmt = new_stmt.replace(OLD2, NEW2, 1)

OLD3 = ('⇒ 该件 17,624,355 → 913,237 B，'
        '总量 −16,711,118 B。')
NEW3 = ('⇒ 该件 17,624,355 → 913,237 B，总量 −16,711,118 B。'
        '**R62/R63 再翻三件为对象侧**（此前均因 R53 只读前 1 MiB 而误判为过程）：'
        '`mesh_imm32.json` 5,693,169 B（`imm` 107,857 键 + `abs` 14,342 键，值→使用点，**正控 50/50、负控 0/50 可回原址**）、'
        '`sweep.json` 1,631,944 B（`e8` 68,253 地址对 + `installs` 6,226 条含寻址模式与值）、'
        '`e8_sites_audit.json` 1,365,087 B（68,253 地址对，已验 `E8` 调用）⇒ 合计 **+8,690,200 B**。')
assert OLD3 in new_stmt, 'step3 fragment not found'
new_stmt = new_stmt.replace(OLD3, NEW3, 1)

ADD = ('**限定向附三·语料值四次演进（v5.29）**：4,518 / 724,479,859 →（R53 重判）4,413 / 744,172,839 →'
       '（R60 剔 `bounds` 16,711,118）4,413 / 727,461,721 →（R62/R63 三件翻对象侧 +8,690,200）'
       '**4,416 / 736,151,921 B**；逐文件清单 `R17_R99_TIER_FINAL_4416\\tier_final_4416.tsv`（回读 sum 校验）。'
       '**「地址清单」与「地址关系」的分界**：单列地址且无法回原址（`a2_sites` 的 `bounds`，86.19% 无字节对应）**剔除**；'
       '两列以上且能回原址复核（`calls`/`imm`/`abs`/`e8`）**计入** —— 判据是「有没有可回原址复核的第二列」，'
       '不是「含不含地址」。**R53 那次 `q2_rejudge.py:41,53` 只读前 1 MiB**，'
       '`truncated=Y` 全表 **5 件**（`a2_sites` 17.6 MB、`mesh_imm32` 5,693,169、`sweep` 1,631,944、'
       '`e8_sites_audit` 1,365,087、`scan_mine` 1,365,365）；前四件已重判（3 翻对象侧、`a2_sites` 剔 `bounds`），'
       '`scan_mine.json` 维持过程（元数据+哈希）。'
       '**一处方法错误已更正**：`sweep.json` 盘上有 **5 个同名文件**，R62 曾按 basename 误取 `S08-K1\\work\\` 那份（3,892,273 B）；'
       '正确对象是 `S08_KPROVED2\\_audit\\EVIDENCE\\sweep.json`（1,631,944 B），与 `rejudge` 记录一致。')
assert '\n' not in ADD
new_lim = f24[4].rstrip() + ADD
assert '语料值四次演进' in new_lim

f24[1] = new_stmt
f24[4] = new_lim
ADDS = [r'lead\next_re_20261117_r14\R17_R99_TIER_FINAL_4416\tier_final_4416.tsv']
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
assert 4413 + 3 == 4416
assert 727461721 + 5693169 + 1631944 + 1365087 == 736151921
assert 5693169 + 1631944 + 1365087 == 8690200

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
