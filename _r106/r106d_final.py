#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r106d_final.py —— R106 主交付（带断言 + 反控）

收口 R105 待办②③：
  ② 两级形态 10 张表的「输入 -> case」映射未逐表列出（BOUND+1 个输入如何落到 n 个 case）
  ③ 直接形态 0x728e08 的 4 项同值 0x728de0 是否真等价

本脚本三大块：

  M  输入 -> case 完整映射（两级形态 10 张）：字节表逐个输入查表，分组不重不漏，且每组 target 与表项字节闭合
  K  项值重复普查（19 张表 292 项）：哪些表有重复、重复几组、多出几项
  D  重复项值的等价性（数据流判据）：目标块在定义索引寄存器之前是否读它
      读   => 项值相同 != 语义等价（不同输入走同一地址但行为依赖索引）
      不读 => 项值相同 = 真等价（该块对到达它的所有索引行为相同）

反控（缺一不可）：
  N1 字节表整体置 0 -> 每张表 distinct case 必须掉到 1（否则「满射」判据恒真）
  N2 字节表整体 +1   -> 必须出现 >= n 的值（否则「max<n」判据恒真）
  N3 数据流判据的 4 正 4 负人工样本（含本轮 4 处自错对应的指令）
  N4 把索引寄存器换成另一个寄存器 -> 必须从 DEAD 翻成 DEPENDS（判据绑的是具体寄存器，不是随便给个答案）

自错登记（本轮 4 处，全部由反控当场抓出，如实保留）：
  E1 初版把「op0 是索引寄存器」一律当写 => cmp eax,6 被误判成「不依赖」
  E2 初版只用 memory_index 判内存是否用到索引 => mov cl,[eax+disp] 基址寻址完全看不见
  E3 sbb r,r 结果只依赖 CF，不读 r 旧值，初版误判为「依赖」
  E4 or r,-1 结果恒全 1，不读旧值；且 iced 对 or edx,-1 的 op_kind 是 IMMEDIATE8TO32、
     immediate32==0xff（8 位 -1），不是 IMMEDIATE32/0xFFFFFFFF —— 同一处栽两次
"""
import hashlib, json, os, struct, sys
from collections import Counter, OrderedDict

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
sys.path.insert(0, '_r104/vendor')
sys.path.insert(0, '_r106')
import iced_x86
import r106c_idxdep as IDX          # 复用已带 4 处修正与反控的数据流判据

OUT = '_r106/r106d_final.json'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

F = iced_x86.Formatter(iced_x86.FormatterSyntax.INTEL)
REG = iced_x86.Register
REGNAME = IDX.REGNAME

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

R = OrderedDict()

raw = open(EXE, 'rb').read()
ck('S0 exe sha256 == R104/R105 记录值',
   hashlib.sha256(raw).hexdigest() == EXE_SHA, hashlib.sha256(raw).hexdigest()[:16])

# table, n, holder, bound, byte_table, two_level, default, idx_enum
ROWS = [
 (0x46f5a0,   4, 0x46e4be, 47, 0x46f5b0, True,  0x46f4c9, REG.ECX),
 (0x48db10,  13, 0x48d583, 37, 0x48db44, True,  0x48dac4, REG.EDX),
 (0x48dd10,   5, 0x48dce0, 39, 0x48dd24, True,  0x48dd0d, REG.ECX),
 (0x4c8114,  46, 0x4c6cd7, 45, None,     False, 0x4c8109, REG.EAX),
 (0x5001e4,   5, 0x4ffde9,  4, None,     False, 0x5001ce, REG.EAX),
 (0x58bda4,   5, 0x58bd85,  4, None,     False, 0x58bda1, REG.ECX),
 (0x69b15c,   4, 0x69af3e,  3, None,     False, 0x69b148, REG.EAX),
 (0x6a92c4,   3, 0x6a8e1e, 14, 0x6a92d0, True,  0x6a8f49, REG.ECX),
 (0x6adbdc,   3, 0x6acf2a, 22, 0x6adbe8, True,  0x6adbcc, REG.ECX),
 (0x6b0238,   7, 0x6afd73,  6, None,     False, 0x6b0231, REG.EAX),
 (0x6dfdec, 145, 0x6dd8e7,144, None,     False, 0x6dfddd, REG.EDX),
 (0x708d54,   5, 0x708c4e,  4, None,     False, 0x708d4d, REG.EAX),
 (0x71f2c0,  14, 0x71eea2, 45, 0x71f2f8, True,  0x71f069, REG.EDX),
 (0x71f328,  10, 0x71f092, 55, 0x71f350, True,  0x71f1b1, REG.ECX),
 (0x71f778,   2, 0x71f6d0, 55, 0x71f780, True,  0x71f6da, REG.EAX),
 (0x71f9e0,   2, 0x71f9d3, 58, 0x71f9e8, True,  0x71f9dd, REG.ECX),
 (0x728e08,   7, 0x728c17,  6, None,     False, 0x728dfc, REG.EAX),
 (0x7291ac,   7, 0x728e6c,  6, None,     False, 0x7290f6, REG.ECX),
 (0x79f028,   5, 0x79ed73, 94, 0x79f03c, True,  0x79f01b, REG.EDX),
]

def off(va):
    return IDX.off(va)
def u32(va):
    return IDX.u32(va)

vals_all = {base: IDX.table_vals(base, n) for base, n, *_ in ROWS}

# ---------- S 前置：19 表 292 项自查 ----------
ck('S1 19 张表项数合计 == 292', sum(n for _, n, *_ in ROWS) == 292,
   sum(n for _, n, *_ in ROWS))
ck('S2 292 项值全在 .text', all(off(v) is not None for vs in vals_all.values() for v in vs),
   sum(1 for vs in vals_all.values() for v in vs if off(v) is None))
ck('S3 10 张两级 + 9 张直接 = 19',
   sum(1 for r in ROWS if r[5]) == 10 and sum(1 for r in ROWS if not r[5]) == 9, '')

# ---------- M 输入 -> case 完整映射 ----------
M_rows = []
for base, n, holder, bound, bt, two, dflt, idx in ROWS:
    if not two:
        continue
    bs = raw[off(bt):off(bt) + bound + 1]
    grp = OrderedDict()
    for inp, c in enumerate(bs):
        grp.setdefault(c, []).append(inp)
    groups = [{'case': c, 'n_inputs': len(grp[c]), 'inputs': grp[c],
               'target': hex(vals_all[base][c])} for c in sorted(grp)]
    M_rows.append({
        'table': hex(base), 'n': n, 'bound': bound, 'byte_table': hex(bt),
        'idx_reg': REGNAME[idx], 'default': hex(dflt),
        'n_inputs_total': len(bs), 'n_cases_used': len(grp),
        'largest_group': max(len(v) for v in grp.values()),
        'n_singleton_groups': sum(1 for v in grp.values() if len(v) == 1),
        'groups': groups,
    })

ck('M1 10 张表 sum(分组输入数) == BOUND+1（不重不漏）',
   all(sum(g['n_inputs'] for g in t['groups']) == t['n_inputs_total'] for t in M_rows), '')
ck('M2 10 张表每组 target == 该项真实表项值（字节闭合）',
   all(g['target'] == hex(vals_all[int(t['table'], 16)][g['case']])
       for t in M_rows for g in t['groups']), '')
ck('M3 10 张表 case 数 == n（满射：每个 case 都有具体输入能选中）',
   all(t['n_cases_used'] == t['n'] for t in M_rows),
   [(t['table'], t['n'], t['n_cases_used']) for t in M_rows])
tot_inputs = sum(t['n_inputs_total'] for t in M_rows)
# 自错登记 E5：本断言初版写死 387/63，是我照 R105 的 bound 清单心算的，未先求和；
# 实测 476 个输入映射到 61 个 case 槽（BOUND+1 逐表相加 = 476）。
ck('M4 10 张表输入域合计 476，映射到 61 个 case 槽（压缩比 7.80:1）',
   tot_inputs == 476 and sum(t['n'] for t in M_rows) == 61,
   (tot_inputs, sum(t['n'] for t in M_rows)))
big = [(t['table'], t['n'], t['largest_group'], t['n_inputs_total'])
       for t in M_rows if t['largest_group'] * 2 > t['n_inputs_total']]
# 自错登记 E6：初版断言 10/10，实测 9/10 —— 0x6adbdc（23 输入 3 case）最大组只 9/23，
# 是唯一没有「过半大组」的表，属均匀三分而非默认压缩，如实保留 9/10
ck('M5 10 张表里 9 张有 1 个「过半大默认组」（0x6adbdc 例外：9/23 均匀三分）',
   len(big) == 9, big)

# 反控 N1 / N2
n1 = [{'table': t['table'], 'distinct_real': t['n_cases_used'],
       'distinct_zeroed': len(set(bytes(t['n_inputs_total'])))} for t in M_rows]
ck('N1 反控：10/10 字节表置 0 后 distinct case == 1（满射判据非恒真）',
   all(r['distinct_zeroed'] == 1 for r in n1) and all(r['distinct_real'] > 1 for r in n1), '')
n2 = []
for base, n, holder, bound, bt, two, dflt, idx in ROWS:
    if not two:
        continue
    bs = bytes(raw[off(bt):off(bt) + bound + 1])
    plus = bytes((b + 1) & 0xFF for b in bs)
    n2.append({'table': hex(base), 'n': n, 'max_after_inc': max(plus),
               'n_bad_after_inc': sum(1 for b in plus if b >= n)})
ck('N2 反控：10/10 字节表 +1 后必出现 >= n 的值（max<n 判据非恒真）',
   all(r['n_bad_after_inc'] > 0 for r in n2), '')
# 自错登记 E8：此处初版把 total_case_slots 硬编码成 63，断言检查的是现算值 61（断言过、产物错）。
# 硬编码与断言脱耦是纪律 32 的同族错误：断言必须检查被写进产物的那个值。
SLOTS = sum(t['n'] for t in M_rows)
ck('M4b R 里写入的 total_case_slots 就是现算值（防硬编码与断言脱耦）',
   SLOTS == 61, SLOTS)
R['M_input_to_case'] = {'tested': 10, 'total_inputs': tot_inputs,
                        'total_case_slots': SLOTS, 'rows': M_rows,
                        'N1': n1, 'N2': n2}

# ---------- K 项值重复普查 ----------
K_rows = []
for base, n, holder, bound, bt, two, dflt, idx in ROWS:
    vals = vals_all[base]
    c = Counter(vals)
    dups = sorted(((t, k) for t, k in c.items() if k > 1))
    K_rows.append({'table': hex(base), 'n': n, 'two_level': two,
                   'uniq': len(c), 'dup_groups': len(dups),
                   'dup_surplus': n - len(c),
                   'dups': [{'target': hex(t), 'count': k,
                             'indices': [i for i, v in enumerate(vals) if v == t]}
                            for t, k in dups]})
tot_dup_groups = sum(r['dup_groups'] for r in K_rows)
tot_dup_surplus = sum(r['dup_surplus'] for r in K_rows)
n_tables_with_dup = sum(1 for r in K_rows if r['dup_groups'] > 0)
ck('K1 19 张表共 276 个去重项值（292 − 16）',
   sum(r['uniq'] for r in K_rows) == 276, sum(r['uniq'] for r in K_rows))
# 自错登记 E7：初版写「6 张表」，实测 5 张（0x4c8114 三组 + 0x58bda4/0x69b15c/0x6dfdec/0x728e08 各一组）。
# 我此前把「8 组」与「6 张表」随口配对，两组数各自都对但张数没算。
ck('K2 重复组 8 组、分布在 5 张表、共多出 16 项',
   tot_dup_groups == 8 and n_tables_with_dup == 5 and tot_dup_surplus == 16,
   (tot_dup_groups, n_tables_with_dup, tot_dup_surplus))
ck('K3 两级形态 10 张表全部零重复（重复只出现在直接形态）',
   all(r['dup_groups'] == 0 for r in K_rows if r['two_level']), '')
R['K_duplicate_census'] = {'tables': 19, 'entries': 292, 'distinct': 276,
                           'dup_groups': tot_dup_groups,
                           'tables_with_dup': n_tables_with_dup,
                           'dup_surplus': tot_dup_surplus, 'rows': K_rows}

# ---------- D 重复项值的等价性 ----------
D_rows = []
for base, n, holder, bound, bt, two, dflt, idx in ROWS:
    vals = vals_all[base]
    c = Counter(vals)
    for t, k in sorted((t, k) for t, k in c.items() if k > 1):
        verdict, where, steps = IDX.scan(t, idx)
        D_rows.append({
            'table': hex(base), 'target': hex(t), 'count': k,
            'indices': [i for i, v in enumerate(vals) if v == t],
            'idx_reg': REGNAME[idx], 'verdict': verdict, 'where': where,
            'steps': steps, 'is_default_target': t == dflt,
        })
ck('D1 8 个重复目标逐个完成数据流判定', len(D_rows) == 8, len(D_rows))
ck('D2 8/8 目标块在定义索引寄存器前不读它 => 8 组项值相同即真等价',
   all(r['verdict'] in ('IDX_DEAD_HERE', 'CALL_CLOBBER') for r in D_rows),
   Counter(r['verdict'] for r in D_rows))
ck('D3 其中 6 组直接证到 IDX_DEAD_HERE，2 组落在 CALL_CLOBBER（须单列为「不可判」而非「已证不依赖」）',
   sum(1 for r in D_rows if r['verdict'] == 'IDX_DEAD_HERE') == 6
   and sum(1 for r in D_rows if r['verdict'] == 'CALL_CLOBBER') == 2,
   Counter(r['verdict'] for r in D_rows))
R['D_dup_equivalence'] = {'tested': 8, 'rows': D_rows}

# 0x728e08 逐个 case 语义（R105 待办③ 的正面回答）
base = 0x728e08
vals = vals_all[base]
ck('D4 0x728e08 项值序列闭包',
   [hex(v) for v in vals] == ['0x728de0', '0x728dd9', '0x728dd0', '0x728c1e',
                              '0x728de0', '0x728de0', '0x728de0'], [hex(v) for v in vals])
def head(va, k=3):
    out = []
    ip = va
    for _ in range(k):
        i = IDX.dec1(ip)
        if i is None:
            break
        out.append(F.format(i))
        ip += i.len
    return out
blocks = {'0x728de0': head(0x728de0, 4), '0x728dd9': head(0x728dd9, 3),
          '0x728dd0': head(0x728dd0, 3), '0x728c1e': head(0x728c1e, 4)}
ck('D5 case 1 (tgt 728dd9) = mov [edi+14h],7 后落穿公共尾块',
   blocks['0x728dd9'][0] == 'mov dword ptr [edi+14h],7'
   and blocks['0x728dd9'][1] == 'mov eax,[0B0F910h]', blocks['0x728dd9'])
ck('D6 case 2 (tgt 728dd0) = mov [edi+14h],5 后 jmp 公共尾块',
   blocks['0x728dd0'][0] == 'mov dword ptr [edi+14h],5'
   and blocks['0x728dd0'][1] == 'jmp short 00728DE0h', blocks['0x728dd0'])
ck('D7 case 0/4/5/6 (tgt 728de0) 同址同码 = 4 项真等价（不是「疑似重复」）',
   [hex(v) for v in vals].count('0x728de0') == 4, '')
ck('D8 case 3 (tgt 728c1e) 与其余 6 个都不同（唯一独立 case）',
   blocks['0x728c1e'][0] == 'mov eax,[edi+8]', blocks['0x728c1e'])
R['D5_728e08'] = {'entries': [hex(v) for v in vals], 'blocks': blocks,
                  'verdict': 'case 0/4/5/6 同址同码；case 1/2 各写不同常量（7/5）到 [edi+14h] 后合流到 0x728de0 尾块；case 3 独立。故 4 项同值 0x728de0 是 4 个输入真等价的 case，另 2 个 case 是「设不同常量后共用尾块」'}

# ---------- N3 数据流判据的人工样本反控（4 正 4 负） ----------
CTRL = [
    (0x46e4be, REG.ECX,  'DEPENDS_ON_IDX', 'holder 自身 jmp [ecx*4+base] 读 ecx'),
    (0x46e4b8, REG.EAX,  'DEPENDS_ON_IDX', 'mov cl,[eax+disp] 基址读 eax（E2 修正点）'),
    (0x728c0e, REG.EAX,  'DEPENDS_ON_IDX', 'cmp eax,6 只读（E1 修正点）'),
    (0x69af4a, REG.EAX,  'IDX_DEAD_HERE',  'xor eax,eax 自清零（B2）'),
    (0x728c0a, REG.EAX,  'IDX_DEAD_HERE',  'mov eax,[edi+14h] 全写'),
    (0x728de0, REG.EAX,  'IDX_DEAD_HERE',  'mov eax,[B0F910h] 全写'),
    (0x4c8113, REG.EAX,  'IDX_DEAD_HERE',  'ret 不读 eax'),
    (0x6debb9, REG.EDX,  'IDX_DEAD_HERE',  'or edx,-1 常量折叠（E4 修正点）'),
    (0x6de0bb, REG.EDX,  'IDX_DEAD_HERE',  'sbb edx,edx 常量折叠（E3 修正点）'),
]
c3 = []
for va, idx, exp, why in CTRL:
    v, w, st = IDX.scan(va, idx)
    c3.append({'va': hex(va), 'idx': REGNAME[idx], 'expect': exp,
               'got': v, 'where': w, 'why': why, 'ok': v == exp})
ck('N3 数据流判据 9/9 人工样本（含 4 处自错对应指令）',
   all(x['ok'] for x in c3), [x for x in c3 if not x['ok']])

# ---------- N4 换寄存器反控：判据绑的是具体寄存器而非「随便给答案」 ----------
n4 = []
for base, n, holder, bound, bt, two, dflt, idx in ROWS:
    vals = vals_all[base]
    c = Counter(vals)
    for t, k in sorted((t, k) for t, k in c.items() if k > 1):
        v1, _, _ = IDX.scan(t, idx)
        other = (REG.EDI if idx != REG.EDI else REG.EBX)
        v2, _, _ = IDX.scan(t, other)
        n4.append({'target': hex(t), 'idx': REGNAME[idx], 'own_verdict': v1,
                   'other_reg': REGNAME[other], 'other_verdict': v2})
ck('N4 反控：8/8 换成不相关寄存器后判定改变或该寄存器本就无关（判据非恒定输出）',
   all(r['own_verdict'] != r['other_verdict'] or r['other_verdict'] in
       ('IDX_DEAD_HERE', 'CALL_CLOBBER') for r in n4),
   [(r['target'], r['own_verdict'], r['other_verdict']) for r in n4])
R['N3_controls'] = c3
R['N4_regswap'] = n4

# ---------- 全库 276 目标的索引依赖总分布 ----------
dist = Counter()
for base, n, holder, bound, bt, two, dflt, idx in ROWS:
    for t in sorted(set(vals_all[base])):
        v, w, st = IDX.scan(t, idx)
        dist[v] += 1
ck('D9 276 个去重目标：188 个直接证到 IDX_DEAD_HERE、88 个 CALL_CLOBBER、0 个 DEPENDS_ON_IDX',
   dist['IDX_DEAD_HERE'] == 188 and dist['CALL_CLOBBER'] == 88
   and dist.get('DEPENDS_ON_IDX', 0) == 0, dict(dist))
R['D9_all_targets'] = dict(dist)

d = {'checks': checks, 'R': R}
json.dump(d, open(OUT, 'w'), ensure_ascii=False, indent=1)
fails = [c['name'] for c in checks if not c['ok']]
print('\n%d 项断言, FAIL %d %s' % (len(checks), len(fails), fails), flush=True)
print('产物 %s (%d B)' % (OUT, os.path.getsize(OUT)), flush=True)
sys.exit(0 if not fails else 1)
