# -*- coding: utf-8 -*-
"""FACT_INDEX v5.26：C′ 的定义定案——改为「对象证据集合」4,518 件 / 724,479,859 B。
依据：F24 是否定命题（791 行没有四环证据），故语料必须「纯」而非「大」；
      18,712 里 P0 兜底 14,548（零内容证据）+ P1b 378（仅形态证据）都不支撑否定命题。
我复算：主式 18,712−378−14,548+732=4,518；对偶式 24,723−20,205=4,518；字节两式均 724,479,859。
作废：18,712 / 19,444 / 17,244 三个数。
"""
import io, os, re, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R87_FACTINDEX_V525')
DST  = os.path.join(R14, 'R17_R89_FACTINDEX_V526')
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

# ---- statement：C′ 段整体替换 ----
OLD = ('**语义重分类值 · C′（仅可作量级引用，不得当作对象集结论）** = 18,712 文件 / 1,363,708,720 B = 1.363709 GB = 1.270053 GiB')
NEW = ('**对象证据集合（tier_final，本项唯一可引用的「语料」值）** = **4,518 文件 / 724,479,859 B = 0.724480 GB(10^9) = 0.674724 GiB(2^30)**；'
       '口径 = **只收「有内容证据断定为对象抄本」的件**（各卡 `why=P1a`（前 8 KiB ≥60% 行首 VA）3,786 件 ∪ '
       '`EVIDENCE\\` 冲突件中逐件内容判为对象抄本的 732 件），**形态证据（P1b 378）、兜底（P0 14,548）、平票（tie 266）一律不留**；'
       '其所以取「纯」不取「大」：`F24` 是**否定命题**（「791 行属事实层面没有四环证据」），'
       '语料里混进一件不含证据的文件，就是在替被否定的那 791 行说话。'
       '**另列规模参考值（不得用于否定命题）**：24,478 件 / 1,558,495,337 B = 1.558495 GB / 1.451461 GiB（档 A 基底，含过程与兜底）。')
assert OLD in f24[1], 'C-prime prime fragment not found'
new_stmt = f24[1].replace(OLD, NEW)
assert new_stmt != f24[1]

# 把紧随其后的「但 C′ 是未被排除集合…」整段改写为定案说明
OLD2 = ('**但 C′ 是「未被排除集合」，不是「已证明对象集合」**：按清单自身 why 列统计，'
        '**P0 兜底（未被任何排除判据命中）= 14,548 件 / 548,531,103 B，占件数 77.7%**；'
        'P1a（内容含行首 VA ≥60%）= 3,786 件 / 714,228,639 B；P1b（≥70% 行含 ≥2 TAB，纯形态判据）= 378 件 / 100,948,978 B。'
        '⇒ 只有 P1a 那一档是「有内容证据说它是对象」，其余 81.1% 的件数是**未被排除**而非**被证明**。')
NEW2 = ('**为什么不能再叫「C′ / 未被排除集合」**：旧 C′ 的 18,712 件按 `why` 列分三档——'
        'P0 兜底（未被任何排除判据命中）**14,548 件 / 548,531,103 B（占 77.7%）**、'
        'P1a（内容含行首 VA ≥60%）3,786 / 714,228,639、P1b（≥70% 行含 ≥2 TAB，纯形态）378 / 100,948,978。'
        '**其中 81.1% 只是「未被排除」，不是「被证明含证据」**，故三档里只有 P1a 能进本项语料。'
        '**逐件算式（两式双算、我复算一致）**：主式 `18,712 − 378(P1b) − 14,548(P0) + 732(逐件判为对象) = 4,518`；'
        '对偶式 `24,723(档 A) − 20,205(20,205 = 15,192 半证据 + 4,769 无裁定 + 244 已判过程) = 4,518`。')
assert OLD2 in new_stmt, 'second fragment not found'
new_stmt = new_stmt.replace(OLD2, NEW2)
assert new_stmt != f24[1]

# 作废旧三数（替换残留的候选数表述）
OLD3 = '若把 732 件对象并入 C′ 则得 19,444 件 / 1,373,959,940 B，再加余 152 件得上界 19,596 件 / 1,376,929,189 B'
if OLD3 in new_stmt:
    new_stmt = new_stmt.replace(OLD3, '（旧候选数 19,444 / 19,596 已作废，见限定⑥）')

# ---- limitations：加限定⑥「三旧数作废」并保留 7 条结构 ----
ADD = ('【限定⑥附·C′ 三旧数作废（v5.26）】**18,712 / 19,444 / 17,244 三个数一律不得再引用**：'
       '18,712 是「未被排除集合」（77.7% 为零内容证据的兜底）；19,444 是「只加不减」（把 14,548 件兜底留着）；'
       '17,244 只剔到应剔量的 9.5%、未触及真正的分界 14,926 件（P1b 378 + P0 14,548）。'
       '**本项语料值只有两个**：对象证据集合 **4,518 件 / 724,479,859 B**（唯一可用于否定命题者）'
       '与规模参考值 **24,478 件 / 1,558,495,337 B**（不得用于否定命题）。'
       '另记：`EVIDENCE\\` 冲突件 1,242 件的应剔清单 `should_exclude.tsv`（1,468 件 / 149,493,508 B）'
       '执行员本轮报「未在盘上找到」，**实测该文件存在且行数/字节与该数完全一致**——该「未取得」为误报。')
assert '\n' not in ADD
new_lim = f24[4].rstrip() + ADD
assert 'C′ 三旧数作废' in new_lim

f24[1] = new_stmt
f24[4] = new_lim
ADDS = [r'lead\next_re_20261117_r14\R17_R88_T1_SEMDEF\REPORT.md',
        r'lead\next_re_20261117_r14\R17_R88_T1_SEMDEF\tier_final.tsv']
for a in ADDS:
    assert a not in f24[3]
    assert os.path.isfile(os.path.join(ROOT, a.replace('\\', '/'))), a
    f24[3] = f24[3] + ';' + a

out = '\n'.join([lines[0]] + ['\t'.join(r) for r in rows]) + '\n'
assert '\r' not in out
for ch in ('\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0'):
    assert ch not in out, 'invisible U+%04X' % ord(ch)
assert new_stmt.count('（') == new_stmt.count('）'), (new_stmt.count('（'), new_stmt.count('）'))
assert new_lim.count('（') == new_lim.count('）')
# 数字断言
assert 18712 - 378 - 14548 + 732 == 4518
assert 24723 - 20205 == 4518
assert 714228639 + 10251220 == 724479859
assert 1363708720 - 100948978 - 548531103 + 10251220 == 724479859
assert 15192 + 4769 + 244 == 20205
assert 378 + 14548 == 14926

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
