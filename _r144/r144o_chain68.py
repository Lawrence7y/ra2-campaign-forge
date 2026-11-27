#!/usr/bin/env python3
"""R144 O：R143 的「68 条链」与「35 条链」是两个不同判据 —— 定位差异根因。

R143 自己在两份产物里给了两个数：
  _r143/r143k_chain.json        chain_disp0_vts_hits = 35
  _r143/r143l_chain_rate.json   L1_disp0_vts_hits    = 68
R143 看板 §一 引用的是 **68**（并配 67/68 = 98.53%）。

假说 H：r143l 的 follow() 里那行「基址被改写则作废」写成
        if k in ('write','store','store_imm') and d[0] == base: return None
     其中 'write' 分支的 d 是**字符串**（操作数左半，如 'eax'），d[0] 取到的是首字符 'e'，
     永远不等于 base（'eax'）⇒ 「寄存器被改写」这一终止条件对该分支**完全失效**。
       r143k 的 chain() 用 `k2 == 'write' and d2 == base`（整串比较）⇒ 生效。
本脚本把两种变体都实现，并给出：严格 / 宽松（复刻字符串下标）/ 各自 + STK 基址的结果。
"""
import sys, json, hashlib, collections
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
ins = list(B.sweep(md))

def parse(a, sz, mn, op):
    if not op: return ('nop', None)
    if mn in ('call', 'jmp'):
        m = L.RE_CALL.match(op)
        if m and m.group(1) in L.GEN:
            return ('disp', (m.group(1), L.disp_of(m.group(2)), mn))
        return ('nop', None)
    ms = L.RE_STORE.match(op)
    if ms and mn in ('mov', 'movl'):
        tgt = ms.group(3)
        base, ds = ms.group(1), L.disp_of(ms.group(2))
        if tgt is not None and L.RE_IMM.match(tgt):
            return ('store_imm', (base, ds, L.immval(tgt)))
        return ('store', (base, ds, tgt))
    m = L.RE_LOAD.match(op)
    if m and mn == 'mov':
        return ('load', (m.group(1), m.group(2), L.disp_of(m.group(3))))
    if mn in L.W_MN:
        return ('write', op.partition(',')[0])
    if mn in ('ret', 'retn'):
        return ('ret', None)
    return ('other', None)

P = [parse(*x) for x in ins]; N = len(P)

def follow(i, disp, bases, buggy_write, first_only, window=200):
    """S-310：R143K 的 chain() 不「首个命中即返回」，而是同一装表站点窗口内
    所有派发都计入（一站点可产多条链）——这才是 35 而非 30 的来源。这里照抄该行为。"""
    base = P[i][1][0]
    j = i + 1; end = min(N, i + 1 + window); loaded = None; hits = []
    while j < end:
        k, d = P[j]
        if k == 'ret': break
        if k in ('store', 'store_imm') and d[0] == base: break
        if k == 'write':
            if buggy_write:
                if d[0] == base: break                # 复刻 R143L 的字符串下标比较（恒不成立）
            else:
                if d == base: break                   # 严格：整串比较
        if k == 'load' and d[1] == base and d[2] == disp: loaded = d[0]
        elif k == 'disp' and loaded and d[0] == loaded:
            hits.append((ins[j][0], d[1], d[2]))
            if first_only: break
        j += 1
    return hits or None

def run(disp, immclass, bases, buggy_write, first_only=False):
    S = []
    for i, (k, d) in enumerate(P):
        if k != 'store_imm': continue
        base, ds, imm = d
        if base not in bases or ds != disp: continue
        if immclass == 'vts' and imm not in VTS: continue
        if immclass == 'nonvts' and imm in VTS: continue
        S.append(i)
    H = []
    for i in S:
        f = follow(i, disp, bases, buggy_write, first_only)
        if f:
            for one in f: H.append((ins[i][0], P[i][1][2], one[0], one[1]))
    return S, H

def l2(H):
    nt = nc = 0
    for iva, vt, dva, sd in H:
        t = B.dw(vt + sd)
        if t is not None and B.sec_of(t) == '.text': nt += 1
        if B.dw(vt - 4) in COL: nc += 1
    return nt, nc

STK_BASES = tuple(L.GEN) + tuple(L.STK)
out = {}
for tag, bases, bug, first in (('K_strict_multi', L.GEN, False, False), ('L_lenient_first', L.GEN, True, True),
                               ('strict_first', L.GEN, False, True), ('lenient_multi', L.GEN, True, False),
                               ('K_strict_multi_STK', STK_BASES, False, False)):
    S, H = run(0, 'vts', bases, bug, first)
    nt, nc = l2(H)
    out[tag] = {'sites': len(S), 'hits': len(H), 'rate': round(len(H) / len(S), 5) if S else None,
                'distinct_vt': len({h[1] for h in H}), 'text': nt, 'col': nc,
                'text_rate': round(nt / len(H), 4) if H else None}
S4, H4 = run(4, 'vts', L.GEN, False, False)
S8, H8 = run(8, 'vts', L.GEN, False, False)
SN, HN = run(0, 'nonvts', L.GEN, False, False)
res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'instructions': N, 'vt_distinct': len(VTS), 'td': len(TDs), 'col': len(COL),
 'variants': out,
 'disp4': [len(S4), len(H4)], 'disp8': [len(S8), len(H8)], 'nonvts': [len(SN), len(HN)],
 'nonvts_text': l2(HN)[0],
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('K 变体（严格+多命中）复现 r143k 的 35 条', out['K_strict_multi']['hits'] == 35, out['K_strict_multi']['hits'])
chk('L 变体（宽松+首命中）复现 r143l 的 68 条', out['L_lenient_first']['hits'] == 68, out['L_lenient_first']['hits'])
chk('两个变体的 .text 率分别复现 100% 与 98.53%（67/68）', out['K_strict_multi']['text_rate'] == 1.0 and out['L_lenient_first']['text_rate'] == 0.9853, [out['K_strict_multi']['text_rate'], out['L_lenient_first']['text_rate']])
chk('两个变体的 distinct 虚表分别是 24 与 40', out['K_strict_multi']['distinct_vt'] == 24 and out['L_lenient_first']['distinct_vt'] == 40, [out['K_strict_multi']['distinct_vt'], out['L_lenient_first']['distinct_vt']])
chk('偏移 4/8 与 nonvts 在严格变体下复现 r143k 的 0/0/8', len(H4) == 0 and len(H8) == 0 and len(HN) == 8, [len(H4), len(H8), len(HN)])
chk('加入 STK 基址后严格变体链数增加（修复后仍能从 35 提到更多）', out['K_strict_multi_STK']['hits'] > out['K_strict_multi']['hits'], [out['K_strict_multi']['hits'], out['K_strict_multi_STK']['hits']])
chk('单纯改宽松/多命中任一项都到不了 68（68 是两个缺陷叠加的产物）', out['strict_first']['hits'] != 68 and out['lenient_multi']['hits'] != 68, [out['strict_first']['hits'], out['lenient_multi']['hits']])
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r144/r144o_chain68.json', 'w'), indent=1)
print(json.dumps(res, indent=1, ensure_ascii=False)[:2600])
print('\n'.join('%-70s %s %s' % (p[0], p[1], p[2]) for p in POS))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
