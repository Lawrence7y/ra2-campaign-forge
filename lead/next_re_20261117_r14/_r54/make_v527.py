# -*- coding: utf-8 -*-
"""FACT_INDEX v5.27：F24 的语料值按重判结果更新。
传导链（已用集合运算核实）：
  tier_final = P1a(3,786 件/714,228,639 B，全在 C′ 内) ∪ 逐件判为对象者(全在 C′ 外，与 P1a 无交集)
  旧: 3,786 + 732 = 4,518 / 724,479,859 B
  新: 3,786 + 627 = 4,413 / 744,172,839 B   (732→627 来自重判：505 留 + 89 无法判定转 + 33 过程转)
件数 −105 而字节 +19,692,980（+2.7%）——必须双报。
"""
import io, os, re, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R89_FACTINDEX_V526')
DST  = os.path.join(R14, 'R17_R93_FACTINDEX_V527')
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

OLD = ('**对象证据集合（tier_final，本项唯一可引用的「语料」值）** = **4,518 文件 / 724,479,859 B '
       '= 0.724480 GB(10^9) = 0.674724 GiB(2^30)**')
NEW = ('**对象证据集合（tier_final，本项唯一可引用的「语料」值）** = **4,413 文件 / 744,172,839 B '
       '= 0.744173 GB(10^9) = 0.693058 GiB(2^30)**')
assert OLD in f24[1], 'tier_final fragment not found'
new_stmt = f24[1].replace(OLD, NEW)
assert new_stmt != f24[1]

# 在口径描述后补一句「件数与字节方向相反」
OLD2 = ('**形态证据（P1b 378）、兜底（P0 14,548）、平票（tie 266）一律不留**；')
NEW2 = ('**形态证据（P1b 378）、兜底（P0 14,548）、平票（tie 266）一律不留**；'
        '**本值已于 R53 按新口径重判后更新**（旧值 4,518 件 / 724,479,859 B）：'
        '构成 = P1a 3,786 件 / 714,228,639 B ∪ 逐件判为对象者 **627 件 / 29,944,200 B**（旧为 732 / 10,251,220 B）。'
        '**注意件数与字节方向相反**：件数 4,518→4,413（**−105**）而字节 724,479,859→744,172,839（**+19,692,980，+2.7%**）——'
        '因为旧判据把**体量最大的几件**误判为过程，件数等权的统计会**系统性低估大件误判的后果**；'
        '**引用本值必须件数与字节同时给出，单报件数会得出「语料变少」的相反结论**。')
assert OLD2 in new_stmt, 'caliber fragment not found'
new_stmt = new_stmt.replace(OLD2, NEW2)
assert new_stmt != f24[1]

ADD = ('**限定向附·语料值已按新口径重判（v5.27）**：`EVIDENCE\\` 1,242 件在 R53 被逐件重判（转移矩阵六式闭合），'
       '旧判据**误判 260 件 / 21,609,436 B**（对象→过程 227、过程→对象 33）；**266 件「无法判定」全部落边、清零**，'
       '另 2 件属**证据不完整**判永久不可判。新口径分布：对象 627 / 29,944,200 B、过程 613 / 16,739,809 B、永久判不了 2 / 770 B。'
       '旧判据盲区已定位并可复核：①地址正则只认 `0x` 前缀、漏裸十六进制（`ROW_00524D70` 旧法命中 2/24 行、新法 13/24 行）；'
       '②「行首 VA 占比」对**单行大文件**分母恒为 1（`q3_cfg.json` 旧法分母 1 行、新法 34,729 段）。'
       '**引用语料值时件数与字节必须同时给出**（见 statement 的方向相反说明）。'
       '正控残留：两套实现仍差 **2 件 / 6,558 B**（`ROW_006E6410.txt`、`probe12_stdout.txt`），未收敛，未称「完全一致」。')
assert '\n' not in ADD
new_lim = f24[4].rstrip() + ADD
assert '语料值已按新口径重判' in new_lim

f24[1] = new_stmt
f24[4] = new_lim
ADDS = [r'lead\next_re_20261117_r14\R17_R92_T1_REJUDGE\REPORT.md',
        r'lead\next_re_20261117_r14\R17_R92_T1_REJUDGE\rejudge1242.tsv',
        r'lead\next_re_20261117_r14\R17_R92_T1_REJUDGE\q3_matrix.tsv']
for a in ADDS:
    assert a not in f24[3]
    assert os.path.isfile(os.path.join(ROOT, a.replace('\\', '/'))), a
    f24[3] = f24[3] + ';' + a

out = '\n'.join([lines[0]] + ['\t'.join(r) for r in rows]) + '\n'
assert '\r' not in out
for ch in ('\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0'):
    assert ch not in out
assert new_stmt.count('（') == new_stmt.count('）'), (new_stmt.count('（'), new_stmt.count('）'))
assert new_lim.count('（') == new_lim.count('）')
# 数字断言
assert 3786 + 627 == 4413
assert 714228639 + 29944200 == 744172839
assert 4518 - 732 + 627 == 4413
assert 724479859 - 10251220 + 29944200 == 744172839
assert 744172839 - 724479859 == 19692980

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
