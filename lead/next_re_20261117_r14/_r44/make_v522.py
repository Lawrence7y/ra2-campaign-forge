# -*- coding: utf-8 -*-
"""FACT_INDEX v5.22：C′ 改述为「未被排除集合」并补下边界限定 + 两处已定位缺陷。
复算依据：P0=14,548/548,531,103（77.7% 件数）; P1a=3,786/714,228,639; P1b=378/100,948,978;
files_scale_today.tsv(2,308,725) 与 _hits_primary.tsv(80,580,525) 均以 why=P1b 留在 C′。
"""
import io, os, re, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R82_FACTINDEX_V521')
DST  = os.path.join(R14, 'R17_R83_FACTINDEX_V522')
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

OLD = ('**语义重分类值 · C′** = 18,712 文件 / 1,363,708,720 B = 1.363709 GB = 1.270053 GiB'
       '（「被测对象优先」口径：内容第一顺位、名字只作嫌疑；逐文件清单 `files_tier_Cprime.tsv` 含 why 列），')
NEW = ('**语义重分类值 · C′** = 18,712 文件 / 1,363,708,720 B = 1.363709 GB = 1.270053 GiB'
       '（逐文件清单 `files_tier_Cprime.tsv` 含 why 列）。'
       '**但 C′ 是「未被排除集合」，不是「已证明对象集合」**：按清单自身 why 列统计，'
       '**P0 兜底（未被任何排除判据命中）= 14,548 件 / 548,531,103 B，占件数 77.7%**；'
       'P1a（内容含行首 VA ≥60%）= 3,786 件 / 714,228,639 B；P1b（≥70% 行含 ≥2 TAB，纯形态判据）= 378 件 / 100,948,978 B。'
       '⇒ 只有 P1a 那一档是「有内容证据说它是对象」，其余 81.1% 的件数是**未被排除**而非**被证明**。')
assert OLD in f24[1], 'C-prime fragment not found'
new_stmt = f24[1].replace(OLD, NEW)
assert new_stmt != f24[1]

ADD = ('**C′ 的下边界同样要守（v5.21 只守了上边界）**：⑥它含 **P0 兜底 14,548 件 / 548,531,103 B（77.7%）**，'
       '其中约 **4,471 件 / 210,142,479 B（15.4%）**前 8 KiB 有 ≥25% 非空行是中文叙述（判词/草稿体与对象抄本同落兜底、口径未区分）；'
       '**⑦已知两类确定缺陷**：（a）`files_scale_today.tsv`（2,308,725 B，规模清单本身）因 E5「命中即排」在代码中实为 P1b 之下的低优先级而**误留 C′，应排除**；'
       '（b）`_hits_primary.tsv`（80,580,525 B，占 C′ 字节 5.9%，是 C′ 最大单件）同样以 `why=P1b` 留在 C′，'
       '而执行员报告 `REPORT.md:299` 逐字称该件「**本卡同判**」（即已排除）⇒ **报告与清单直接冲突，以清单为准**；'
       '**⑧P1a 的 60% 阈值是任意断点**：改 50% 翻转 127 件 / +1,580,709 B，改 70% 翻转 130 件 / −1,369,750 B（±0.12%），'
       '量级稳但断点无自然依据；**⑨有 592 件 / 3,406,272 B 首行为 `[cmd] …` 的跑批包装日志因 E1/E2 名字判据不覆盖而落进 C′**。'
       '⇒ **C′ 只可作为量级引用，不可作为「干净语料」引用**。')
assert '\n' not in ADD
new_lim = f24[4].rstrip() + ADD
assert 'C′ 的下边界同样要守' in new_lim

f24[1] = new_stmt
f24[4] = new_lim
ADDS = [r'lead\next_re_20261117_r14\R17_R81_T1_AUDITCP\REPORT_AUDITCP.md']
for a in ADDS:
    assert a not in f24[3]
    assert os.path.isfile(os.path.join(ROOT, a.replace('\\', '/'))), a
    f24[3] = f24[3] + ';' + a

out = '\n'.join([lines[0]] + ['\t'.join(r) for r in rows]) + '\n'
assert '\r' not in out
for ch in ('\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0'):
    assert ch not in out, 'invisible U+%04X' % ord(ch)
assert new_stmt.count('（') == new_stmt.count('）'), (new_stmt.count('（'), new_stmt.count('）'))
assert 14548 + 3786 + 378 == 18712, 14548 + 3786 + 378
assert 548531103 + 714228639 + 100948978 == 1363708720, 548531103 + 714228639 + 100948978

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
