#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R164-B · FACT_INDEX V543 → V544：把「86.19% 是口径滑移」这层定性写进 F24 正文

R137 看板第九节遗留项 ② 与 ③ 合并成一张卡（内容变更必须单独一卡 + 门禁回归）：
  ② F24 正文里 86.19% 的 5 处出现全在撤回语境，但没有一处写「它测的是盘上语料覆盖率、
     主语被写成二进制」；
  ③ 语料值的失效期与三作用域数字（0 / 1,556 / 1,704）应写进正文。

本轮新增（R164 取证产物）：`a2_sites.json` 的**生成器不再「未复原」**——
R163 待办第 1 条（「口径已复原、代码未复原」）由 r164a 结掉：整个文件是
一次 skipdata 线性扫描的两个投影，序列化逐字节闭合。
这条属**新增事实**，必须写进 F24 的 limitations 末尾（纯后缀追加），
否则正文与盘上已完成的工作脱节。

写入纪律（逐条断言，任一失败即整体放弃，先全部校验再一次性写）：
  1. V544 是新目录新文件（不覆盖 V543；V543 一字未改）
  2. V544 与 V543 的差异**只允许** F24 第 5 列（limitations）末尾追加
     —— 其余 53 行逐字节相同、F24 前四列逐字节相同、F24 limitations 是 V543 的纯前缀扩展
  3. V544 全 LF（CR=0）、55 行、54 数据行、每行 5 列
  4. 改 facts_floors.py 的四个 pin（EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / FLOORS['F24']）
     与 MASTER_SHA256 重算；改 gate_runner.py 的 LEDGER 路径
  5. 改 FACT_INDEX_CURRENT.md 指针（先写新版本目录，再改指针 —— 顺序不能反）
  6. 三个被改文件先 wx 独占备份到 R17_LEAD_BASELINE/，再断言旧 sha256 与 CR

幂等：重跑时若 V544 已存在且内容相同则只做终态校验。
"""
import hashlib
import io
import os
import re
import sys
import time

R = '/home/t628/projects/ra2-campaign-forge'
T = R + '/lead/next_re_20261117_r14'
V543 = T + '/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv'
V544DIR = T + '/R17_R116_FACTINDEX_V544'
V544 = V544DIR + '/FACT_INDEX.tsv'
CURMD = T + '/FACT_INDEX_CURRENT.md'
FLOORS_PY = R + '/_r160/facts_floors.py'
RUNNER = R + '/_r161/gate_runner.py'
BD = T + '/R17_LEAD_BASELINE'

V543_SHA = '6b00f95581fa938d40252c213d741a69f3e849b7fc903a9bb0ae709ba80d538f'
V543_BYTES = 96765

# R95 §5.3 的原文 sha256（本轮实测）
R95_SHA = 'be6d4d0f20ca18be87fd444f1ca962d1bf800302845f3c195dec33fcc07d6cd9'

ADD = (
    ' **【R164 补·「86.19%」的口径滑移已定性，且它的语料与生成器现状一并钉住】** '
    '① 该数的**主语是盘上语料、不是二进制**：`R17_R95_T1_A2SITES/REPORT.md` §5.3'
    '（26,976 B / sha256 `be6d4d0f20ca18be87fd444f1ca962d1bf800302845f3c195dec33fcc07d6cd9`）'
    '逐字写「用 4,743 份文本 EVIDENCE 扫『VA 指令字节 助记符』行」，与 `bounds` 相交得 '
    '**192,341 / 1,392,592 = 13.81%**，其余 **1,200,251（86.19%）「只以地址形式存在，'
    '盘上没有任何字节与之对应」**；三数自洽 `1,392,592 − 192,341 = 1,200,251`。'
    '⇒ 它是**「盘上语料未覆盖」的补集**，不是「二进制里没有字节」；同一批地址的二进制判据是 '
    '**100.000000%**（弱判据：落在某节 `SizeOfRawData` 覆盖内）与 **99.992%**（强判据：落在指令起始集），'
    '两者测的不是同一命题 ⇒ R136 与 R95 从来不矛盾，是本条正文把两个命题缝成了一句。'
    '**引用 86.19% 必须同时写明「它是语料覆盖率的补集」并声明其语料当前不可重算**'
    '（`_r163/r163c_f24_scope_slip.py` 34 断言 0 FAIL；`_r164/r164a_a2_rule.py` 复算同向）。'
    '② **该数的语料当前已不在盘，三个作用域并列报**：`lead/next_re_20261117_r14` 下大写 `EVIDENCE` '
    '目录 **5** / 文件 **5** / 含行 **0** / 覆盖 **0** 条；全库大写 `EVIDENCE` 目录 **6** / 文件 **52** / '
    '含行 **35** / 覆盖 **1,556** 条；全库大小写不敏感 `evidence` 目录 **8** / 文件 **217** / 覆盖 **1,704** 条'
    ' —— 三者都够不到 192,341（差 1~3 个数量级）。**R163 曾把「覆盖 0 条」写进正文，那是只走了 '
    '`lead/` 子树的作用域错（自错 S-495），已按全库真值改写**；`q4_covering.py` / '
    '`q4_covering_verify.py`（R95 §7 清单所载）现盘均不存在。'
    '③ **`a2_sites.json` 的生成器不再是「未复原」**：整件 17,624,355 B 已复原成一条确定规则 —— '
    '`bounds` **逐位等于** capstone `skipdata=True` 对 VirtualSize blob（4,060,045 B）**一次线性扫描**的起点序列'
    '（1,392,592 条，条数/顺序/值全同；raw blob 口径会多 1,594 条，全在尾填充区）；'
    '`calls` **逐键逐值含顺序**等于同一次扫描里「助记符 `call` 且操作数为立即数地址」的（目标 → 站点）反向索引'
    '（6,728 键 / 68,253 对：键按目标**首次出现序**插入、键内按扫描序追加，**无排序、无去重、无后处理**）；'
    '序列化逐字节闭合 `913,238`（`{"calls": …}`）+ `13`（`, "bounds": [`）+ `16,711,104`'
    '（= 12 B × 1,392,592）= **17,624,355 B**。⇒ 本项语料**可由 `.text` 重扫再生**，不再是不可复核的黑箱；'
    '`_r164/r164a_a2_rule.py` 38 断言 0 FAIL（反控：`bounds[0]` 改 +4 逐位相等必失败、注入一对伪造必失败、'
    '把寄存器/内存操作数也算进来得 94,786 ≠ 68,253、raw blob 起点 1,394,186 = bounds + 1,594）。'
    '④ **R95 §6 那条「本件漏了 1 条直接调用」的机制已定**：`(target=007C8B3D, site=0074836A)` 的站点字节确为 '
    '`E8` 且 rel32 指向 0x7C8B3D，但该站点**落在一条 skip 块的内部**（块起点 0x748368 / 长 3 B / 位移 2）'
    '⇒ 按 ③ 的规则它**本来就不会被产出**（不是生成器漏写）；同一对在 '
    '`C01_census/EVIDENCE/callgraph.json`（不跳数据块的扫描）里**确实存在** ⇒ 两件互不矛盾，'
    '差异根因是扫描口径而非缺陷。'
)

fails = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:260]) if d else ''))
    if not ok:
        fails.append(n)
    return ok


def rb(p):
    with open(p, 'rb') as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def bak(path, tag):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r164_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(path))
    ck('bak %s wx 独占创建' % os.path.basename(out), os.path.exists(out), out)
    return out


# ================================================================ 0 · 旧态
print('== 0 · 旧态断言 ==')
o543 = rb(V543)
print('  V543 %d B sha=%s' % (len(o543), sha(o543)))
ck('0.1 V543 sha256 仍是 6b00f955…', sha(o543) == V543_SHA, sha(o543)[:16])
ck('0.2 V543 字节 96,765 / CR=0 / 55 行',
   len(o543) == V543_BYTES and o543.count(b'\r') == 0 and o543.count(b'\n') == 55,
   (len(o543), o543.count(b'\r'), o543.count(b'\n')))

o_floors, o_runner, o_cur = rb(FLOORS_PY), rb(RUNNER), rb(CURMD)
print('  facts_floors %d B sha=%s' % (len(o_floors), sha(o_floors)[:16]))
print('  gate_runner  %d B sha=%s' % (len(o_runner), sha(o_runner)[:16]))
print('  CURRENT.md   %d B sha=%s' % (len(o_cur), sha(o_cur)[:16]))
ck('0.3 facts_floors.py 指向 V543', b"R17_R115_FACTINDEX_V543" in o_floors)
ck('0.3b gate_runner.py 指向 V543', b"R17_R115_FACTINDEX_V543" in o_runner)
ck('0.3c FACT_INDEX_CURRENT.md 声明 V543 并给出同一 sha256',
   b'R17_R115_FACTINDEX_V543' in o_cur and V543_SHA.encode() in o_cur)

# ================================================================ 1 · 构造 V544 内容
print('== 1 · 构造 V544 ==')
t543 = o543.decode('utf-8')
lines = t543.split('\n')
ck('1.1 split 后 56 段（55 行 + 末尾空）', len(lines) == 56, len(lines))
hdr, data = lines[0], [l for l in lines[1:] if l]
ck('1.2 表头 5 列 / 数据 54 行',
   len(hdr.split('\t')) == 5 and len(data) == 54, (len(hdr.split('\t')), len(data)))

new = []
hit = 0
for l in data:
    f = l.split('\t')
    if f[0] == 'F24':
        ck('1.3 F24 行恰 5 列', len(f) == 5, len(f))
        ck('1.4 F24 grade 仍是 [已证]（本轮不改 grade）', f[2] == '[已证]', f[2])
        ck('1.5 F24 limitations 尚未含 R164 补（未写过的旧态）', '【R164 补' not in f[4])
        f[4] = f[4] + ADD
        hit += 1
        new.append('\t'.join(f))
    else:
        new.append(l)
ck('1.6 命中 F24 恰 1 行', hit == 1, hit)
new_txt = hdr + '\n' + '\n'.join(new) + '\n'
new_b = new_txt.encode('utf-8')
print('  V544 预构造 %d B sha=%s' % (len(new_b), sha(new_b)))

ck('2.1 V544 CR=0 / 55 行 / 54 数据行',
   new_b.count(b'\r') == 0 and new_b.count(b'\n') == 55, (new_b.count(b'\r'), new_b.count(b'\n')))
n543 = [l.split('\t') for l in data]
n544 = [l.split('\t') for l in new]
ck('2.2 逐行逐列比：只有 F24 的 limitations 变（其余 53 行 × 5 列全同）',
   all(a == b for a, b in zip(n543, n544) if a[0] != 'F24')
   and sum(1 for a, b in zip(n543, n544) if a != b) == 1,
   sum(1 for a, b in zip(n543, n544) if a != b))
f543 = next(f for f in n543 if f[0] == 'F24')
f544 = next(f for f in n544 if f[0] == 'F24')
ck('2.3 F24 前四列逐字节相同', f543[:4] == f544[:4])
ck('2.4 F24 limitations 是纯后缀扩展（V543 全文是 V544 的前缀）',
   f544[4].startswith(f543[4]),
   (len(f543[4].encode()), len(f544[4].encode())))
ck('2.5 limitations 字节增长 = 追加段字节数',
   len(f544[4].encode()) - len(f543[4].encode()) == len(ADD.encode()),
   (len(f543[4].encode()), len(f544[4].encode()), len(ADD.encode())))
ck('2.6 V544 正文含「重扫再生」与「口径滑移」两条定性',
   '语料未覆盖」的补集' in new_txt and '可由 `.text` 重扫再生' in new_txt)
print('  F24 limitations: %d → %d B' % (len(f543[4].encode()), len(f544[4].encode())))

# ================================================================ 3 · 写 V544（幂等）
print('== 3 · 落盘 V544 ==')
if os.path.exists(V544):
    cur = rb(V544)
    if cur == new_b:
        print('  [idempotent] V544 已是本轮内容')
    else:
        ck('3.0 V544 已存在但内容不同 ⇒ 拒绝覆盖', False, sha(cur)[:16])
else:
    os.makedirs(V544DIR, exist_ok=True)
    fd = os.open(V544, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(new_b)
back = rb(V544)
ck('3.1 回读逐字节相同', back == new_b, sha(back)[:16])
ck('3.2 回读 CR=0 / 55 行 / 54 数据行 / 全 5 列',
   back.count(b'\r') == 0 and back.count(b'\n') == 55
   and len([l for l in back.decode().split('\n')[1:] if l]) == 54
   and all(len(l.split('\t')) == 5 for l in back.decode().split('\n') if l))
ck('3.3 V543 一字未改（写后复测 sha）', sha(rb(V543)) == V543_SHA, sha(rb(V543))[:16])
NEW_SHA, NEW_BYTES = sha(back), len(back)
print('  V544 %d B sha=%s' % (NEW_BYTES, NEW_SHA))

# ================================================================ 4 · facts_floors 重钉
print('== 4 · facts_floors.py 重钉 ==')


def canon_g(d):
    return '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))


def canon_f(d):
    return '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))


def canon_e(d):
    return '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))


def canon_n(d):
    return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))


ft = o_floors.decode('utf-8')


def blk(name):
    m = re.search(r'^%s = \{\n(.*?)\n\}' % name, ft, re.S | re.M)
    return m.group(1)


def parse_tuples(t):
    return dict((a, (int(b), int(c))) for a, b, c in
                re.findall(r"'([^']+)': \((\d+), (\d+)\),", t))


def parse_pairs(t):
    return dict((a, int(b)) for a, b in re.findall(r"'([^']+)': (\d+),", t))


def parse_lists(t):
    return dict((a, re.findall(r"'([^']*)'", b)) for a, b in re.findall(r"'([^']+)': \[(.*?)\],", t, re.S))


G = dict((a, b) for a, b in re.findall(r"'([^']+)': '([^']*)',", blk('GRADES')))
F = parse_tuples(blk('FLOORS'))
E = parse_lists(blk('EVID'))
EB = parse_pairs(blk('EVIDB'))
L = parse_pairs(blk('LOST'))
ck('4.1 五个常量块都能解析（GRADES %d / FLOORS %d / EVID %d / EVIDB %d / LOST %d）'
   % (len(G), len(F), len(E), len(EB), len(L)),
   (len(G), len(F), len(E), len(EB), len(L)) == (54, 54, 54, 54, 16),
   (len(G), len(F), len(E), len(EB), len(L)))

NEW_LIM = len(f544[4].encode())
old_f24 = F['F24']
ck('4.2 F24 旧下界 == V543 实测（首次实测口径）',
   old_f24 == (len(f543[1].encode()), len(f543[4].encode())), (old_f24, len(f543[4].encode())))
F['F24'] = (len(f544[1].encode()), NEW_LIM)
print('  FLOORS[F24]: %s → %s' % (old_f24, F['F24']))

nf = ft
if "R17_R115_FACTINDEX_V543" in nf:
    nf = nf.replace("R17_R115_FACTINDEX_V543", "R17_R116_FACTINDEX_V544")
nf = re.sub(r"^CUR_SHA256 = '[0-9a-f]{64}'$", "CUR_SHA256 = '%s'" % NEW_SHA, nf, count=1, flags=re.M)
nf = re.sub(r"^TOTAL_BYTES = \d+$", "TOTAL_BYTES = %d" % NEW_BYTES, nf, count=1, flags=re.M)

# FLOORS 里 F24 那一行
old_line = "    'F24': (%d, %d)," % old_f24
new_line = "    'F24': (%d, %d)," % F['F24']
ck('4.3 FLOORS 里 F24 旧行能唯一定位', nf.count(old_line) == 1, nf.count(old_line))
nf = nf.replace(old_line, new_line, 1)

ITEMS = int(re.search(r'^ITEMS = (\d+)$', ft, re.M).group(1))
UNIQ = int(re.search(r'^UNIQ = (\d+)$', ft, re.M).group(1))
LOST_ITEMS = int(re.search(r'^LOST_ITEMS = (\d+)$', ft, re.M).group(1))
LOST_UNIQ = int(re.search(r'^LOST_UNIQ = (\d+)$', ft, re.M).group(1))
master = hashlib.sha256(('\n'.join([NEW_SHA, str(NEW_BYTES), canon_g(G), canon_f(F), canon_e(E),
                                    canon_n(EB), canon_n(L), str(ITEMS), str(UNIQ),
                                    str(LOST_ITEMS), str(LOST_UNIQ)])).encode()).hexdigest()
nf = re.sub(r"^MASTER_SHA256 = '[0-9a-f]{64}'$", "MASTER_SHA256 = '%s'" % master, nf, count=1, flags=re.M)
print('  MASTER_SHA256 = %s' % master[:16])
ck('4.4 新文本仍含五个块与四个标量',
   all(('%s = {' % k) in nf for k in ('GRADES', 'FLOORS', 'EVID', 'EVIDB', 'LOST')))
ck('4.5 EVID/EVIDB/LOST/GRADES 一字未动（除 FLOORS.F24 外）',
   parse_lists(blk('EVID')) == E and parse_pairs(blk('EVIDB')) == EB
   and parse_pairs(blk('LOST')) == L
   and dict((a, b) for a, b in re.findall(r"'([^']+)': '([^']*)',", blk('GRADES'))) == G)

# ================================================================ 5 · gate_runner 与指针
print('== 5 · gate_runner / 指针 ==')
nr = o_runner.decode('utf-8')
ck('5.1 gate_runner 里 V543 目录名出现 1 次（只有 LEDGER 常量；docstring 写的是 V543 裸版本号）',
   nr.count('R17_R115_FACTINDEX_V543') == 1, nr.count('R17_R115_FACTINDEX_V543'))
nr = nr.replace('R17_R115_FACTINDEX_V543', 'R17_R116_FACTINDEX_V544')
nr = nr.replace('sha256(V543/FACT_INDEX.tsv)', 'sha256(V544/FACT_INDEX.tsv)')
nr = nr.replace('len(V543/FACT_INDEX.tsv)', 'len(V544/FACT_INDEX.tsv)')
nr = nr.replace('现盘 V543 sha256', '现盘 V544 sha256').replace('现盘 V543 字节数', '现盘 V544 字节数')
nc = o_cur.decode('utf-8')
ck('5.2 指针文件里 V543 目录名出现 2 次（表格两行）', nc.count('R17_R115_FACTINDEX_V543') == 2,
   nc.count('R17_R115_FACTINDEX_V543'))
nc = nc.replace('R17_R115_FACTINDEX_V543', 'R17_R116_FACTINDEX_V544')
nc = nc.replace('（D0 已钉 V543 的 sha256）', '（D0 已钉 V544 的 sha256）')
nc = nc.replace(
    '| 声明依据 | 版本号 530..543 连续无缺，V543 同时是「版本号最大」且「其目录序号 R115 为最大」，'
    '且 R115 下只有这一个 FACT_INDEX 目录（三项同时成立才写本文件） |',
    '| 声明依据 | 版本号 530..544 连续无缺，V544 同时是「版本号最大」且「其目录序号 R116 为最大」，'
    '且 R116 下只有这一个 FACT_INDEX 目录（三项同时成立才写本文件） |')
nc = nc.replace('补一个 V544 草稿就会静默指错。', '补一个 V545 草稿就会静默指错。')
nc = nc.replace(V543_SHA, NEW_SHA)
nc = re.sub(r'\| 字节数 \| \d+ \|', '| 字节数 | %d |' % NEW_BYTES, nc)
nc = nc.replace('| 声明轮次 | R160 |', '| 声明轮次 | R164 |')
nc = nc.replace('V530..V542 是 14 个可独立复核的快照', 'V530..V543 是 15 个可独立复核的快照')
ck('5.3 指针已改到 V544 且 sha/字节/声明依据/历史条数同步', 'R17_R116_FACTINDEX_V544' in nc
   and NEW_SHA in nc and str(NEW_BYTES) in nc and '| 声明轮次 | R164 |' in nc
   and '530..544 连续无缺' in nc and 'V530..V543 是 15 个' in nc
   and 'V543' not in nc.replace('V530..V543', ''), 
   (nc.count('V543'), nc.count('V544')))

# ================================================================ 6 · 落盘三件（幂等）
print('== 6 · 落盘三件 ==')
for path, new_text, tag in ((FLOORS_PY, nf, 'floors'), (RUNNER, nr, 'runner'), (CURMD, nc, 'curmd')):
    cur = rb(path).decode('utf-8')
    if cur == new_text:
        print('  [idempotent] %s 已更新' % os.path.basename(path))
        continue
    bak(path, tag)
    ck('6.0 备份后旧 sha256 与读入一致', sha(rb(path)) == sha(cur.encode('utf-8')))
    fd = os.open(path + '.tmp_r164', os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(new_text.encode('utf-8'))
    os.replace(path + '.tmp_r164', path)
    ck('6.1 %s 回读逐字节相同' % os.path.basename(path),
       rb(path).decode('utf-8') == new_text)

# ================================================================ 7 · 终态校验
print('== 7 · 终态校验 ==')
ck('7.1 facts_floors 指向 V544 且四 pin 同步',
   "R17_R116_FACTINDEX_V544" in rb(FLOORS_PY).decode()
   and "CUR_SHA256 = '%s'" % NEW_SHA in rb(FLOORS_PY).decode()
   and 'TOTAL_BYTES = %d' % NEW_BYTES in rb(FLOORS_PY).decode()
   and "    'F24': (%d, %d)," % F['F24'] in rb(FLOORS_PY).decode())
_run_txt = rb(RUNNER).decode()
ck('7.2 gate_runner LEDGER 指向 V544 且 docstring 的 V543 字样已同步',
   "'R17_R116_FACTINDEX_V544'" in _run_txt and 'V543' not in _run_txt,
   _run_txt.count('V543'))
ck('7.3 指针指向 V544', 'R17_R116_FACTINDEX_V544' in rb(CURMD).decode())
ck('7.4 V543 一字未改', sha(rb(V543)) == V543_SHA)
ck('7.5 V544 sha256 == 新 pin', sha(rb(V544)) == NEW_SHA)

print('\n== 结果 ==')
print('FAIL = %d ; V544 = %d B / sha %s' % (len(fails), NEW_BYTES, NEW_SHA))
if fails:
    for f in fails:
        print('  FAILED: ' + f)
    sys.exit(1)
print('[exit 0]')
sys.exit(0)
