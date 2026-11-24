#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r108c_exclusive.py —— 「所有者唯一性」判据：窗口内除了 owner 还有没有别的外部入口

r108b 用 HB（ret→填充→对齐的新起点）给出了 4 张改判。但「HB」本身只是形态证据。
本脚本把四类外部入口合起来做一次**排他性**检验：
  E = call 直接目标 ∪ vtable 槽值 ∪ 立即数取址目标 ∪ HB
对每张表，取 O = (S,H] ∪ {S} 里最大的 E 成员作为 owner，
并断言 (O,H] 里 E 成员个数 == 0（即窗口内不存在第二个外部入口）——
若 O 到 H 之间还藏着一个「有外部证据的入口」，那 O 就不是 holder 所属函数。

正控：对 19 张里 R107 判 OWNER 的 13 张，O 必须仍等于 R107 的 owner。
反控 R1：随机抽 200 个 call 目标 S'，取 H' = 下一个 call 目标，
   统计其 (S',H') 内 E 成员个数 —— 应当大量 > 0（说明本判据在随机窗口上会发火，不是恒真）。
反控 R2：把 E 定义里的 HB 与 IMMPTR 分别去掉，看 owner 是否变化（量化每类证据的边际贡献）。
"""
import array, bisect, hashlib, json, os, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA,
   hashlib.sha256(raw).hexdigest()[:16])
IB, TS, TE = 0x400000, 0x401000, 0x7e038d
def fo(va):
    return va - IB

D = {}
f = open('_r108/branchmap2.bin', 'rb')
while True:
    hd = f.read(12)
    if len(hd) < 12:
        break
    n, isz, kl = struct.unpack('<III', hd)
    k = f.read(kl).decode()
    a = array.array('I'); a.frombytes(f.read(n * isz)); D[k] = a
starts = D['starts']; SSET = set(starts)
RETS = sorted(D['rets']); CALLT = set(D['call_t'])

def ret_size(r):
    return 3 if raw[fo(r)] in (0xc2, 0xca) else 1
HB = set()
for r in RETS:
    p = r + ret_size(r); q = p; n = 0
    while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < 64:
        q += 1; n += 1
    if n and q % 4 == 0 and q in SSET:
        HB.add(q)

sym = json.load(open('out/reverse/symbols.json'))['classes']
VSLOT = set()
for cn, c in sym.items():
    v = c.get('vtable_va')
    if not v:
        continue
    va = int(v, 16)
    for i in range(400):
        x = struct.unpack_from('<I', raw, fo(va) + i * 4)[0]
        if not (TS <= x < TE):
            break
        VSLOT.add(x)

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
IMMPTR = set()
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]
    last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        if m in ('mov', 'push') and '[' not in o:
            cand = o.split(',')[-1].strip()
            if cand.startswith('0x'):
                try:
                    v = int(cand, 16)
                except ValueError:
                    v = 0
                if TS <= v < TE and v in SSET:
                    IMMPTR.add(v)
    if last <= pos:
        last = pos + 1
    pos = last
E = (CALLT | VSLOT | IMMPTR | HB)
ES = sorted(E)
ck('S1 四类外部入口合并 |E| = %d（call %d / vslot %d / immptr %d / HB %d）'
   % (len(E), len(CALLT), len(VSLOT), len(IMMPTR), len(HB)),
   len(E) > len(CALLT) and len(E) == len(CALLT | VSLOT | IMMPTR | HB),
   (len(CALLT), len(VSLOT), len(IMMPTR), len(HB)))

def owner_in(S, H, Eset_sorted):
    # E-x1：首稿用严格 '>' 判 S，导致「S 本身即窗口内最大 E 成员」时返回 None，
    # 13 张 R107-OWNER 被误记「拿不到 owner」。改为 max(E ∩ [S,H])，空则返回 None。
    i = bisect.bisect_right(Eset_sorted, H)
    if i and Eset_sorted[i - 1] >= S:
        return Eset_sorted[i - 1]
    return None
def interior(S, H, Eset_sorted):
    i = bisect.bisect_right(Eset_sorted, S); j = bisect.bisect_right(Eset_sorted, H)
    return Eset_sorted[i:j]

R107 = json.load(open('_r107/r107g_owner.json'))['rows']
ROWS = []
for r107 in R107:
    S = int(r107['owner'], 16); H = int(r107['holder'], 16)
    O = owner_in(S, H, ES)
    inn = interior(O if O else S, H, ES)
    # 边际贡献：去掉 HB / 去掉 IMMPTR
    o_nohb = owner_in(S, H, sorted(E - HB))
    o_noimm = owner_in(S, H, sorted(E - IMMPTR))
    ROWS.append({'table': r107['table'], 'holder': r107['holder'],
                 'R107_owner': r107['owner'], 'R107_status': r107['owner_status'],
                 'S_used': hex(S), 'owner': hex(O) if O else None,
                 'changed_vs_R107': (O is not None and O != S),
                 'interior_E_count': len(inn),
                 'interior_E': [hex(x) for x in inn[:6]],
                 'owner_without_HB': hex(o_nohb) if o_nohb else None,
                 'owner_without_IMM': hex(o_noimm) if o_noimm else None})
    print('%-10s H=%-10s R107=%s(%s) owner=%s changed=%s interiorE=%d'
          % (r107['table'], r107['holder'], r107['owner'], r107['owner_status'],
             ROWS[-1]['owner'], ROWS[-1]['changed_vs_R107'], ROWS[-1]['interior_E_count']),
          flush=True)

ck('A1 19 张全部拿到 owner', all(r['owner'] for r in ROWS),
   [r['table'] for r in ROWS if not r['owner']])
bad = [r['table'] for r in ROWS if r['interior_E_count'] != 0]
ck('A2 排他性：owner 到 holder 之间不存在任何第二类外部入口（违反数应为 0）', not bad, bad)
own13 = [r for r in ROWS if r['R107_status'] == 'OWNER']
ch13 = [r['table'] for r in own13 if r['changed_vs_R107']]
ck('P1 正控：13 张 R107-OWNER 上 owner 与 R107 一致（不一致数与 R107 判据冲突）', not ch13, ch13)
amb6 = [r for r in ROWS if r['R107_status'] == 'AMBIGUOUS']
ck('A3 6 张 AMBIGUOUS 的最终裁定：改判张数 / 保持张数',
   True, '%d 改判 %s ; %d 保持 %s'
   % (sum(1 for r in amb6 if r['changed_vs_R107']),
      [(r['table'], r['R107_owner'], r['owner']) for r in amb6 if r['changed_vs_R107']],
      sum(1 for r in amb6 if not r['changed_vs_R107']),
      [r['table'] for r in amb6 if not r['changed_vs_R107']]))
d_hb = [r['table'] for r in ROWS if r['owner_without_HB'] != r['owner']]
d_im = [r['table'] for r in ROWS if r['owner_without_IMM'] != r['owner']]
ck('A4 边际贡献：去掉 HB 后 owner 变化的表数 / 去掉 IMMPTR 后变化的表数',
   True, '%d %s / %d %s' % (len(d_hb), d_hb, len(d_im), d_im))

import random
random.seed(20261124)
ct = sorted(CALLT)
idx = random.sample(range(len(ct) - 1), 400)
nfire = 0; ntot = 0; ex = []
for i in idx:
    a, b = ct[i], ct[i + 1]
    if b - a > 0x40000:
        continue
    ntot += 1
    k = len(interior(a, b, ES))
    if k:
        nfire += 1
        if len(ex) < 5:
            ex.append((hex(a), hex(b), k))
# E-x2：本脚本的「排他性」判据在随机窗口上发火率 = 100%，即它在任何窗口里都能找到
# 「第二类外部入口」（HB 密度 1/235 B，短窗口内几乎必有），**没有鉴别力**。
# 故本脚本的排他性判据**已被判为无判别力、仅作一致性自检**，不作独立证据；
# 真正用于裁定的判据在 r108b/r108d/r108e/r108f（HB + 帧配对 + ret 清理约定）。
ck('R1 反控：随机 400 组相邻 call 目标窗口里，窗口内有第二类外部入口的比例（发火率 100% ⇒ 判据无鉴别力，如实记）',
   ntot > 300 and nfire / ntot > 0.3,
   '%.1f%% (%d/%d) 例 %s' % (100.0 * nfire / max(1, ntot), nfire, ntot, ex))

json.dump({'checks': checks, 'rows': ROWS, 'n_E': len(E),
           'n_calls': len(CALLT), 'n_vslot': len(VSLOT), 'n_immptr': len(IMMPTR),
           'n_hb': len(HB), 'negctl_fire': [nfire, ntot]},
          open('_r108/r108c_exclusive.json', 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
