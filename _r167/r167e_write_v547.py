#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r167e_write_v547.py —— FACT_INDEX V546 -> V547（F24 limitations 追加 R167 段）

本轮只做一件事：把 R166 留下的「那 65 条语义未定」补成**已定**，并如实声明其中哪一条是同义反复。
只改 F24 第 5 列（纯追加）；其余 53 行 × 5 列逐字节不变；前四列不动；计数一字不改。
写入纪律：wx 独占备份 -> 断言旧 sha256/CR/行数 -> 一次性写 -> 回读 sha/行数/列数/逐行差分。
"""
import hashlib, io, json, os, sys, time

R = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(R, 'lead/next_re_20261117_r14')
V546 = os.path.join(T, 'R17_R118_FACTINDEX_V546/FACT_INDEX.tsv')
V547D = os.path.join(T, 'R17_R119_FACTINDEX_V547')
V547 = os.path.join(V547D, 'FACT_INDEX.tsv')
BD = os.path.join(T, 'R17_LEAD_BASELINE')
OUT = os.path.join(R, '_r167/r167e_write_v547.json')

V546_SHA = '7c671a4f10a1f131eddc3652d5e6baba153a593d217dddb24841fe9f5393bf6a'
V546_BYTES = 106216
FAILS, RES = [], []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:300]) if d else ''))
    RES.append({'n': n, 'ok': ok, 'd': str(d)[:300]})
    if not ok: FAILS.append(n)

def rb(p):
    with open(p, 'rb') as f: return f.read()

APPEND = (
    '**【R167 补·那 65 条的语义已定：代码指针表内的不可解码字节，不是「指令内部地址」也不是对齐填充】** '
    'R166 段末把它们的语义留成未取得（数据／跳转表／对齐填充三选一），本轮用三条判据定死，'
    '并把其中**一条是同义反复**这一点如实标出（`_r167/r167d_holes_semantics_final.py` **19 断言 0 FAIL**、'
    '`_r167/r167b_undecodable_census.py` 11 断言 0 FAIL，两者独立跑同一普查）：'
    '① **不可解码位普查**：对 `.text` VirtualSize 内**每一个字节位置**用 capstone 解 **count=1**（15 B 窗口、'
    '四进程分片、56.5 s）得「一条指令都解不出来」的位置 **U = 58,017**（占 `.text` 的 **1.4290%**）；'
    '那 65 条**全部**落在 U 内（`only_hole = 0`），而 U 里 **57,952 条（99.89%）从未被线性扫描踩到**。'
    '⇒ 65 不是「不可解码位的全集」，只是**被游标踩到的那一小撮**。'
    '② **同义反复的如实声明**：65 == U ∩ (起点 ∪ 洞) 这一等式**是定义性的**（扫描只把起点记为起点；'
    '某位置成为洞当且仅当游标恰好停在它上面且它不可解码），**不得**当作发现引用；'
    '它的用处只是把「洞」的生成规则写死并配反控（去掉洞集合则 U ∩ 起点 ≠ 洞，等式不是恒真）。'
    '③ **非定义性的实证（富集）**：按节内 4 字节网格＋3 字节条目＋phase 0..3 全试，'
    '65 条里 **56 条（86.15%）**落在「≥3 条、每条都是 `.text` 内地址」的**代码指针表**里，涉及 **35 张表**；'
    '同一 U 内「从未被踩到」的 2,000 抽样命中率仅 **3.50%**、2,000 个随机 `.text` 字节仅 **9.15%** '
    '⇒ 富集倍率对同一 U 的对照是 **24.6 倍**、对随机字节是 **9.4 倍**。'
    '④ **表的身份不是猜的**：这 35 张表共 **1,616** 个槽值，其中 **1,600（99.01%）是指令起点**；'
    '对照 4,767 个「孤立指针型 dword」（值是 `.text` 地址但不成表）抽样 2,000 个只有 **34.10%** 是指令起点 '
    '⇒ 这些是跳转表／case 表，不是数据表也不是地址堆。'
    '⑤ **不在表内的 9 条也有归属**：`0x71f77c`／`0x723e27`／`0x7c5d92`／`0x7c5d9c`／`0x7c80f2`／`0x7c80fc` '
    '**6 条**的邻域是**字节查找表**（相邻字节严格递增成对 ≥4 次，典型 `fe ff 00 01 f7 f8 fa fb fc fd fe ff 00 01 02 03…`）；'
    '余 3 条（`0x71f9e0`／`0x71f9e4`／`0x793455`）邻域既非指针表也非递增表，**仍未归类**（如实保留）。'
    '⇒ 正确措辞：**那 65 条是「线性解码穿过 `bounds` 所指代码指针表（56/65）或字节查找表（6/65）时，'
    '踩到不可解码字节后只能前进 1 字节」的位置**；**不得**写成「指令内部地址」（R162/R163），'
    '**也不得**写成「对齐填充」（U 里 99.89% 从未被踩到，与填充无关）。'
    '本条**计数一字未改**（1,392,592 / 1,392,527 / 65 / 1,593 全部原值）；`U = 58,017` 是**本轮新测**的独立量，'
    '不进入本条任何既有计数。'
)

print('== 0 前置 ==')
b546 = rb(V546)
ck('A0 V546 sha256 == 7c671a4f…', hashlib.sha256(b546).hexdigest() == V546_SHA,
   hashlib.sha256(b546).hexdigest()[:16])
ck('A1 V546 字节 == 106,216', len(b546) == V546_BYTES, len(b546))
ck('A2 V546 CR == 0', b546.count(b'\r') == 0, b546.count(b'\r'))
txt = b546.decode('utf-8')
lines = txt.split('\n')
if lines and lines[-1] == '': lines = lines[:-1]
ck('A3 行数 55', len(lines) == 55, len(lines))
rows = [l.split('\t') for l in lines]
rows_base = [list(r) for r in rows]
ck('A4 每行 5 列', all(len(r) == 5 for r in rows), {len(r) for r in rows})
d = {r[0]: r for r in rows[1:]}
ck('A5 F24 尚无 R167 补段（幂等前提）', 'R167 补·那 65 条的语义已定' not in d['F24'][4],
   d['F24'][4].count('R167 补'))

print('\n== 1 追加 ==')
new = [list(r) for r in rows]
for r in new:
    if r[0] == 'F24': r[4] = r[4] + APPEND
out_txt = '\n'.join('\t'.join(r) for r in new) + '\n'
out_b = out_txt.encode('utf-8')
h = hashlib.sha256(out_b).hexdigest()
print('  V547 = %d B / sha256 %s（追加 %d B / %d 字符）'
      % (len(out_b), h, len(APPEND.encode('utf-8')), len(APPEND)))
ck('B0 纯追加（字节变多）', len(out_b) > len(b546), (len(out_b), len(b546)))
ck('B1 CR == 0', out_b.count(b'\r') == 0, out_b.count(b'\r'))
ck('B2 行数仍 55', len(out_txt.rstrip('\n').split('\n')) == 55)
drift = [a[0] for a, b in zip(rows_base, new) if a != b]
ck('B3 差分行恰 F24', drift == ['F24'], drift)
cell = [(a[0], i) for a, b in zip(rows_base, new) for i in range(5) if a[i] != b[i]]
ck('B4 变化单元恰 1 个且是 F24 第 5 列', cell == [('F24', 4)], cell)
# 反控：计数串逐字不变
import re
cnt_pat = ['1,392,592', '1,392,527', '1,593']
# S-537（自错，本条当场抓出）：首版拿 out_txt.count(p) 与 txt.count(p) 比 —— 但 APPEND 自己就写着
# 「1,392,592 / 1,392,527 / 65 / 1,593 全部原值」，必然各 +1，判据恒 FAIL。正确做法是先把 APPEND
# 从新文本里剥掉再比（剥掉后必须逐字节等于旧文本）。
stripped = out_txt.replace(APPEND, '')
ck('B5 剥掉 APPEND 后与 V546 逐字节相同（这才是「未改正文」的严格判据）', stripped == txt,
   (len(stripped), len(txt)))
oldc = {p: txt.count(p) for p in cnt_pat}
newc = {p: out_txt.count(p) for p in cnt_pat}
ck('B5b 每个计数串在 APPEND 内被引用 1 次（故总出现次数各 +1，不是改写）',
   all(newc[p] - oldc[p] == APPEND.count(p) for p in cnt_pat), (oldc, newc))
ck('B6 APPEND 内无反引号外的控制字符', all(ord(c) >= 32 or c == '\t' for c in APPEND))

print('\n== 2 落盘 ==')
if os.path.exists(V547) and rb(V547) == out_b:
    ck('C0 幂等：V547 已终态', True)
else:
    if not os.path.isdir(V547D): os.makedirs(V547D)
    stamp = time.strftime('%Y%m%d_%H%M%S')
    bakp = os.path.join(BD, 'FACT_INDEX_V546.before_r167e_%s.bak' % stamp)
    fd = os.open(bakp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(b546)
    ck('C1 备份 wx 独占创建且逐字节等于 V546', rb(bakp) == b546, os.path.basename(bakp))
    with open(V547, 'wb') as f: f.write(out_b)
    ck('C2 回读 sha 与内存一致', hashlib.sha256(rb(V547)).hexdigest() == h)
ck('C3 V546 一字未改', hashlib.sha256(rb(V546)).hexdigest() == V546_SHA,
   hashlib.sha256(rb(V546)).hexdigest()[:16])
ck('C4 V547 落盘字节 == %d' % len(out_b), len(rb(V547)) == len(out_b), len(rb(V547)))

f24 = [r for r in new if r[0] == 'F24'][0]
json.dump({'v546_sha': V546_SHA, 'v546_bytes': V546_BYTES, 'v547_sha': h, 'v547_bytes': len(out_b),
           'append_bytes': len(APPEND.encode('utf-8')), 'append_chars': len(APPEND),
           'f24_stmt_bytes': len(f24[1].encode('utf-8')), 'f24_lim_bytes': len(f24[4].encode('utf-8')),
           'drift': drift, 'cells': cell, 'asserts': RES, 'fails': FAILS},
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n断言 %d 条，FAIL %d' % (len(RES), len(FAILS)))
if FAILS: print('FAILS', FAILS)
sys.exit(1 if FAILS else 0)
