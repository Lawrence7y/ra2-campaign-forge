# -*- coding: utf-8 -*-
"""FACT_INDEX v5.23：按 T4 审计全量整改。
① C′ 降级为「仅量级」、必引 why 三档；
② limitations 重构：④⑤合并、①降为口径注脚，目标 7 条；补 D5②（selfkind≠C′判据、不可换算）、D5③（375/333 本身不当可引数）、E6 两件新冲突（共 4 件确定缺陷）。
复算：4 件确定缺陷 = 2,308,725 + 80,580,525 + 42,273 + 673 = 82,932,196 B（占 C′ 6.08%）。
"""
import io, os, re, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R83_FACTINDEX_V522')
DST  = os.path.join(R14, 'R17_R85_FACTINDEX_V523')
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

# ---- statement：C′ 降级为「仅量级」 ----
OLD = ('**语义重分类值 · C′** = 18,712 文件 / 1,363,708,720 B = 1.363709 GB = 1.270053 GiB')
NEW = ('**语义重分类值 · C′（仅可作量级引用，不得当作对象集结论）** = 18,712 文件 / 1,363,708,720 B = 1.363709 GB = 1.270053 GiB')
assert OLD in f24[1]
new_stmt = f24[1].replace(OLD, NEW)
assert new_stmt != f24[1]

# ---- limitations：整段重写为 7 条 ----
NEW_LIM = (
 '『改指针无解、不再投卡』是 Lead 行动裁决（台账 §1054），不入本条证据、不随数字一并作已证；'
 '数字与负结论；归因见 §16.1；R_OK 863 是「至少一个路径解析到真实文件」，不等于「逐 entry 专属证据」。'
 '【限定①·引用口径】规模数一律须标「测量时刻 + 脚本 + 遍历根 + 扩展名集合 + 排除项 + 正则 flags」，缺任一项即不可引用；'
 '引 §16.1 只能引其「判据」，其表内数字是旧快照（478/374/802），数字须取现盘。'
 '【限定②·主引用值】**只以档 A 为主引用值**（24,723 / 1,589,964,358 B）；'
 '档 A 是唯一「判据机械、不依赖人看名字」的档，有逐文件清单可 sum(bytes) 复核。'
 '【限定③·C′ 只能当量级】C′ 是「**未被排除集合**」不是「已证明对象集合」：按清单 `why` 列，'
 '**P0 兜底 14,548 件 / 548,531,103 B（77.7% 件数）**、P1a 3,786 / 714,228,639、P1b 378 / 100,948,978；'
 '**引用 C′ 必须同引这三档分布并写明「仅量级、非干净语料」**，禁止单引 18,712 / 1,363,708,720 B 当对象集结论。'
 '【限定④·分类理由未复算 + 恒等式只证划分】C′ 判据含**内容级判断**（前 8 KiB 行首 VA 比例、横幅、判决顺序 L0→L4），'
 '**换人重跑可能不一致**；我只复算了清单求和与三桶恒等式，**未复算逐件分类理由**；'
 '且该恒等式只证「三桶是档 A 的一个划分」，**不证逐件归对**——互换错（两桶各取一件对调）不产生漏项/重项，照样通过。'
 '【限定⑤·四件已定位的确定缺陷】C′ 里已知**应有而留在其中**的测量产物共 4 件 / **82,932,196 B（占 C′ 6.08%）**：'
 '（a）`_hits_primary.tsv` 80,580,525 B（C′ 最大单件；执行员报告 `REPORT.md:299` 称「本卡同判」已排除，**与清单冲突，以清单为准**）；'
 '（b）`files_scale_today.tsv` 2,308,725 B（规模清单本身）；'
 '（c）`_hits_gframe.txt` 42,273 B（basename 命中 E5 `_hits_*` 却因内容判据 P1a 优先而留）；'
 '（d）`scale_vs_baseline.log` 673 B（同 stem 的 `.json` 已按 `E5_自测量meta` 排除，`.log` 因正则只认 `.json` 而漏排）。'
 '同族风险面另记：P0 中约 4,471 件 / 210,142,479 B（15.4%）前 8 KiB ≥25% 非空行为中文叙述；'
 '592 件 / 3,406,272 B 首行 `[cmd] …` 的跑批日志因 E1/E2 名字判据不覆盖而落 C′；'
 'P1a 的 60% 阈值是**任意断点**（改 50% 翻转 127 件 / 改 70% 翻转 130 件，±0.12%）。'
 '【限定⑥·旧档 C 及其两数】旧档 C（23,347 / 1,300,742,927 B）已被 C′ 取代、**不得再引用**；'
 '其 375 / 333 两数（按 re.I / 无 re.I）只是「说明旧脚注为何错标」，**本身也不得当作可引数**；'
 '且**旧档 C 的 `selfkind` 判据与 C′ 的内容判据是两套不同尺子、不可换算**——'
 '下述漂移分解用前者，C′ 用后者，两者数字不可互相推导。'
 '【限定⑦·漂移分解的边界】漂移分解只成立于 11:55→12:31 这一对快照、沿用旧档 C 的 `selfkind` 口径，**不可移用于历史漂移**；'
 '三个旧数（23,791 / 24,693 / 24,692）一律不得再引用（理由分别是：11-21「无产物」口径不可比；总量与自身清单差 17 文件 / 186,721 B；由虚高「总量−1」推出）；'
 '「1.29」按 `mev675.py:281` 的 /1024³ 实为 **GiB** 而非 GB；「58 倍」只对体积成立（文件数比 2.86 倍）。')

assert '\n' not in NEW_LIM
f24[1] = new_stmt
f24[4] = NEW_LIM
ADDS = [r'lead\next_re_20261117_r14\R17_R84_T4_AUDIT34\REPORT.md']
for a in ADDS:
    assert a not in f24[3]
    assert os.path.isfile(os.path.join(ROOT, a.replace('\\', '/'))), a
    f24[3] = f24[3] + ';' + a

out = '\n'.join([lines[0]] + ['\t'.join(r) for r in rows]) + '\n'
assert '\r' not in out
for ch in ('\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0'):
    assert ch not in out, 'invisible U+%04X' % ord(ch)
assert new_stmt.count('（') == new_stmt.count('）'), (new_stmt.count('（'), new_stmt.count('）'))
# 数字自洽
assert 2308725 + 80580525 + 42273 + 673 == 82932196, 2308725 + 80580525 + 42273 + 673
assert 14548 + 3786 + 378 == 18712
assert 548531103 + 714228639 + 100948978 == 1363708720
# 限定条数
assert len(re.findall(r'【限定[①②③④⑤⑥⑦]', NEW_LIM)) == 7, len(re.findall(r'【限定[①②③④⑤⑥⑦]', NEW_LIM))

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
print('limitations segments =', len(NEW_LIM.split('；')), '; 限定条数 = 7')
