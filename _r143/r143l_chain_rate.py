#!/usr/bin/env python3
"""R143 L：链式判据的比率化 + 分母修正（这是本轮唯一可当「独立证」用的判据）。

链：construct_store(base, disp) -> load(reg2, base, disp) -> disp_instr [reg2+4k]
判据分两层：
  L1 结构层：命中数与「分母 = 同 disp 的 store_imm 站点数」之比
  L2 语义层：命中的槽值 dword[vt+4k] 是否落 .text，且 dword[vt-4] 是否回指 COL
     在这两层都成立时，「对象偏移 0 = vptr」不再依赖对象模型预设。

反控按分母对齐（关键修正）：
  C-a 换 disp = 4 / 8 / 0xc，命中数与分母都要报
  C-b 用「imm 不属于虚表集合」的站点作对照，报命中数与同分母比
  C-c 把命中链的 vt 换成随机 .data dword 值，L2 的 text 命中率应塌
  C-d 随机 .text 起点当装表点，报命中数与分母
"""
import sys, json, collections, random, hashlib
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

P = [parse(*x) for x in ins]
N = len(P)

def sites(disp, immclass):
    out = []
    for i, (k, d) in enumerate(P):
        if k != 'store_imm': continue
        base, ds, imm = d
        if base not in L.GEN or ds != disp: continue
        if immclass == 'vts' and imm not in VTS: continue
        if immclass == 'nonvts' and imm in VTS: continue
        out.append(i)
    return out

def follow(i, disp, window=200):
    base = P[i][1][0]
    j = i + 1; end = min(N, i + 1 + window); loaded = None
    while j < end:
        k, d = P[j]
        if k == 'ret': return None
        if k in ('write', 'store', 'store_imm') and d[0] == base: return None
        if k == 'load' and d[1] == base and d[2] == disp:
            loaded = d[0]
        elif k == 'disp' and loaded and d[0] == loaded:
            return (ins[j][0], d[1], d[2])  # (disp_va, slot_disp, mn)
        j += 1
    return None

def run(disp, immclass):
    S = sites(disp, immclass)
    hits = []
    for i in S:
        f = follow(i, disp)
        if f: hits.append((ins[i][0], P[i][1][2], f[0], f[1]))
    return S, hits

def l2(hits):
    n_t = n_c = 0
    for (iva, vt, dva, sd) in hits:
        t = B.dw(vt + sd)
        if t is not None and B.sec_of(t) == '.text': n_t += 1
        if B.dw(vt - 4) in COL: n_c += 1
    return n_t, n_c

S0, H0 = run(0, 'vts')
S4, H4 = run(4, 'vts')
S8, H8 = run(8, 'vts')
S12, H12 = run(12, 'vts')
SN, HN = run(0, 'nonvts')
t0, c0 = l2(H0)
tN, cN = l2(HN)

# C-c：随机 .data dword 替换 vt，看 L2 是否塌
random.seed(143)
pool = []
for nm, ava, vs, raw, rs in B.secs:
    if nm in ('.data', '.rdata'):
        blob = B.data[raw:raw + rs]
        for i in range(len(blob) // 4):
            pool.append(__import__('struct').unpack_from('<I', blob, i * 4)[0])
g_text = g_col = 0
for (iva, vt, dva, sd) in H0:
    fake = random.choice(pool)
    t = B.dw(fake + sd)
    if t is not None and B.sec_of(t) == '.text': g_text += 1
    if B.dw(fake - 4) in COL: g_col += 1

# C-d：随机起点作装表点
random.seed(7)
pool_i = random.sample(range(N), min(60000, N))
rh = 0; rs_den = 0
for i in pool_i:
    if P[i][0] != 'store_imm': continue
    if P[i][1][0] not in L.GEN or P[i][1][1] != 0: continue
    rs_den += 1
    if follow(i, 0): rh += 1

def rate(a, b): return round(a / b, 5) if b else None
res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'td': len(TDs), 'col': len(COL), 'vt_distinct': len(VTS),
 'L1_disp0_vts_sites': len(S0), 'L1_disp0_vts_hits': len(H0), 'L1_disp0_vts_rate': rate(len(H0), len(S0)),
 'L1_disp0_vts_distinct_vt': len({h[1] for h in H0}),
 'L2_disp0_hits_text_target': t0, 'L2_disp0_hits_col_backref': c0,
 'L2_disp0_text_rate': rate(t0, len(H0)), 'L2_disp0_col_rate': rate(c0, len(H0)),
 'Ca_disp4_sites': len(S4), 'Ca_disp4_hits': len(H4), 'Ca_disp4_rate': rate(len(H4), len(S4)),
 'Ca_disp8_sites': len(S8), 'Ca_disp8_hits': len(H8), 'Ca_disp8_rate': rate(len(H8), len(S8)),
 'Ca_disp12_sites': len(S12), 'Ca_disp12_hits': len(H12), 'Ca_disp12_rate': rate(len(H12), len(S12)),
 'Cb_nonvts_sites': len(SN), 'Cb_nonvts_hits': len(HN), 'Cb_nonvts_rate': rate(len(HN), len(SN)),
 'Cb_nonvts_text_targets': tN, 'Cb_nonvts_col_backrefs': cN,
 'Cc_fakevt_text_targets': g_text, 'Cc_fakevt_col_backrefs': g_col, 'Cc_n': len(H0),
 'Cd_random_sites_den': rs_den, 'Cd_random_sites_hits': rh, 'Cd_random_rate': rate(rh, rs_den),
 'L1_disp0_vts_slot_top': collections.Counter(h[3] // 4 for h in H0).most_common(10),
 'hits_sample': [[hex(a), hex(v), hex(d), s] for a, v, d, s in H0[:25]],
}
print(json.dumps(res, ensure_ascii=False, indent=1))
json.dump(res, open('_r143/r143l_chain_rate.json', 'w'), ensure_ascii=False, indent=1)
