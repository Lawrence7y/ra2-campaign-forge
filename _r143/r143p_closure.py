#!/usr/bin/env python3
"""R143 P：收口测量（唯一权威版本）。三条判据 + 三分母富集 + 链式判据 + 跨家族复算，一次跑完。

本轮结论的强度分三层，本脚本逐层给出可失败断言：
  S1 装表存在：.text 内 mov dword ptr [reg+0], imm 且 imm 是已知虚表地址 —— 2,741 站点 / 838 distinct 虚表
  S2 链式闭合：同一函数内「装表 -> 从同一对象偏移 0 读回 -> 经读回值 call [reg+4k]」，
     且 dword[vt+4k] 落 .text、dword[vt-4] 回指 COL —— 68 条，67/68 与 68/68
  S3 富集修正：raw 富集 41x 是分母病；改用 ptr-like 分母（该位移的装载确实被当内存基址用）
     后是 4.5x；且栈类偏移 0 的 ptr-like 富集与对象类几乎相同（0.962 vs 0.9486）
     => S3 只能支持「偏移 0 常被当指针用」，不能单独支持「偏移 0 是 vptr」
反控：
  N1 伪虚表集合：偏移 0 装表覆盖塌到 1 个
  N2 非虚表 imm 的结构同形链：20 条，但槽目标落 .text 0 条、vt-4 回指 COL 0 条
  N3 绝对基址派发点必须单独归类（4,212 个）
  N4 派发点 100% 落在 objdump 起点集（基线 0.3449）
"""
import sys, json, collections, random, hashlib
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()

def parse(a, sz, mn, op):
    if not op: return ('nop', None)
    if mn in ('call', 'jmp'):
        m = L.RE_CALL.match(op)
        if m:
            base = m.group(1)
            if base in L.GEN: return ('disp', (base, L.disp_of(m.group(2)), mn))
            if base in L.STK: return ('disp_stk', (base, L.disp_of(m.group(2))))
            if base.startswith('0x'): return ('disp_abs', (int(base, 16),))
        return ('callother', None)
    m = L.RE_LOAD.match(op)
    if m and mn == 'mov':
        base = m.group(2)
        cls = 'obj' if base in L.GEN else ('stack' if base in L.STK else 'other')
        return ('load', (m.group(1), base, L.disp_of(m.group(3)), cls))
    ms = L.RE_STORE.match(op)
    if ms and mn in ('mov', 'movl'):
        t = ms.group(3); base = ms.group(1)
        ds = L.disp_of(ms.group(2))
        if t is not None and L.RE_IMM.match(t):
            return ('store_imm', (base, ds, L.immval(t)))
        return ('store', (base, ds))
    if mn in L.W_MN: return ('write', op.partition(',')[0])
    if mn in ('ret', 'retn'): return ('ret', None)
    return ('other', None)

ins = list(B.sweep(md)); P = [parse(*x) for x in ins]; N = len(P)

# ---------- 一遍：装表 / 派发 / 装载 / ptr-like(A) ----------
f1 = []
rec = []
loads = []
last = {}
fedA = set(); ptrA = set()
for i, (k, d) in enumerate(P):
    if k == 'disp':
        base, disp, mn = d
        l = last.get(base)
        rec.append((ins[i][0], mn, base, disp, 'load' if l else 'unknown'))
        if l:
            fedA.add(l)      # 被用作虚派发基址
            ptrA.add(l)      # 同时也是「被当内存基址用」的一次装载（分母要含它）
        for x in ('eax', 'ecx', 'edx'): last.pop(x, None)
    elif k in ('disp_stk', 'disp_abs', 'callother'):
        for x in ('eax', 'ecx', 'edx'): last.pop(x, None)
    elif k == 'store_imm':
        base, ds, iv = d
        if base in L.GEN:
            l = last.get(base)
            if l: ptrA.add(l)
            if iv in VTS: f1.append((ins[i][0], base, ds, iv))
    elif k == 'store':
        base = d[0]
        if base in L.GEN:
            l = last.get(base)
            if l: ptrA.add(l)
    elif k == 'load':
        dst, base, ds, cls = d
        loads.append((ins[i][0], dst, base, ds, cls))
        if base in L.GEN:
            l = last.get(base)
            if l: ptrA.add(l)
        if dst in L.GEN: last[dst] = ins[i][0]
    elif k == 'write':
        last.pop(d, None)

disp0 = [s for s in f1 if s[2] == 0]
cov0 = {s[3] for s in disp0}
abs_disp = sum(1 for k, d in P if k == 'disp_abs')

# ---------- 三分母富集 ----------
obj_loads = [l for l in loads if l[4] == 'obj']
stk_loads = [l for l in loads if l[4] == 'stack']
fed_va = fedA
def enrich(sel, disp, den_kind):
    tot = [x for x in sel if x[3] == disp]
    if den_kind == 'all':
        den = tot
        num = [x for x in tot if x[0] in fed_va]
    else:
        den = [x for x in tot if x[0] in ptrA]
        num = [x for x in tot if x[0] in ptrA and x[0] in fed_va]
    return {'loads': len(tot), 'den': len(den), 'fed': len(num),
            'rate': (round(len(num) / len(den), 4) if den else None)}
E = {}
for cls, sel in (('obj', obj_loads), ('stack', stk_loads)):
    for dk in ('all', 'ptr'):
        E['%s_%s' % (cls, dk)] = {str(d): enrich(sel, d, dk) for d in (0, 4, 8, 12, 16)}

# ---------- 链式判据 ----------
def follow(i, disp, win=200):
    base = P[i][1][0]
    j = i + 1; end = min(N, i + 1 + win); loaded = None
    while j < end:
        k, d = P[j]
        if k == 'ret': return None
        if k in ('write', 'store', 'store_imm') and d[0] == base: return None
        if k == 'load' and d[1] == base and d[2] == disp: loaded = d[0]
        elif k == 'disp' and loaded and d[0] == loaded: return (ins[j][0], d[1])
        j += 1
    return None

def chain(disp, immclass):
    out = []
    for i, (k, d) in enumerate(P):
        if k != 'store_imm': continue
        base, ds, imm = d
        if base not in L.GEN or ds != disp: continue
        if immclass == 'vts' and imm not in VTS: continue
        if immclass == 'nonvts' and imm in VTS: continue
        f = follow(i, disp)
        if f: out.append((ins[i][0], imm, f[0], f[1]))
    return out

CH = chain(0, 'vts')
CHn = chain(0, 'nonvts')
CH4 = chain(4, 'vts')
def l2(H):
    t = c = 0
    for (a, v, dva, sd) in H:
        x = B.dw(v + sd)
        if x is not None and B.sec_of(x) == '.text': t += 1
        if B.dw(v - 4) in COL: c += 1
    return t, c
tT, tC = l2(CH)
nT, nC = l2(CHn)

# ---------- 反控 ----------
random.seed(143)
pool = []
for nm, ava, vs, raw, rs in B.secs:
    if nm in ('.data', '.rdata'):
        blob = B.data[raw:raw + rs]
        for i in range(len(blob) // 4):
            pool.append(__import__('struct').unpack_from('<I', blob, i * 4)[0])
FAKE = set(random.sample(pool, len(VTS)))
fake0 = [s for s in f1 if s[3] in FAKE and s[2] == 0]
starts = set(int(x, 16) for x in open('_r140/obj_starts.txt').read().split())

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'td': len(TDs), 'col': len(COL), 'vt_distinct': len(VTS), 'instructions': N,
 'S1_install_sites': len(f1), 'S1_disp0_sites': len(disp0),
 'S1_disp0_distinct_vt': len(cov0), 'S1_disp0_coverage': round(len(cov0) / len(VTS), 4),
 'S1_disp_hist': dict(sorted(collections.Counter(s[2] for s in f1).items())[:0] or
                     {str(k): v for k, v in sorted(collections.Counter(s[2] for s in f1).items())[:8]}),
 'S2_chain_sites': len(disp0), 'S2_chain_hits': len(CH),
 'S2_chain_rate': round(len(CH) / len(disp0), 4),
 'S2_chain_distinct_vt': len({h[1] for h in CH}),
 'S2_text_target': tT, 'S2_col_backref': tC,
 'S2_text_rate': round(tT / len(CH), 4), 'S2_col_rate': round(tC / len(CH), 4),
 'S2_chain_sample': [[hex(a), hex(v), hex(d), s] for a, v, d, s in CH[:12]],
 'S3_enrich': E,
 'S3_obj0_over_obj4_raw': round(E['obj_all']['0']['rate'] / max(1e-9, E['obj_all']['4']['rate']), 2),
 'S3_obj0_over_obj4_ptr': round(E['obj_ptr']['0']['rate'] / max(1e-9, E['obj_ptr']['4']['rate']), 2),
 'S3_stack0_ptr_rate': E['stack_ptr']['0']['rate'],
 'S3_obj0_ptr_rate': E['obj_ptr']['0']['rate'],
 'N1_fake_disp0_sites': len(fake0),
 'N1_fake_distinct': len({s[3] for s in fake0}),
 'N2_nonvts_chain_hits': len(CHn), 'N2_nonvts_text': nT, 'N2_nonvts_col': nC,
 'N3_abs_base_dispatch': abs_disp,
 'N4_starts_n': len(starts),
 'N4_dispatch_in_starts': sum(1 for r in rec if r[0] in starts),
 'N4_dispatch_total': len(rec),
 'N4_baseline': round(len(starts) / B.T[4], 4),
 'N5_disp4_chain_hits': len(CH4),
}

POS = []; NEG = []
def A(n, c, d=''): POS.append((n, bool(c), d))
def G(n, c, d=''): NEG.append((n, bool(c), d))
A('虚表集合 = 1218', len(VTS) == 1218, len(VTS))
A('S1 偏移0 装表站点 > 2500', len(disp0) > 2500, len(disp0))
A('S1 偏移0 覆盖 distinct 虚表 > 800', len(cov0) > 800, len(cov0))
A('S2 链式命中 >= 60', len(CH) >= 60, len(CH))
A('S2 链式命中槽目标落 .text 率 > 0.9', tT / len(CH) > 0.9, tT / len(CH))
A('S2 链式命中 vt-4 回指 COL 率 = 1.0', tC == len(CH), tC)
A('S3 对象类偏移0 的 ptr-like 率 > 0.9', E['obj_ptr']['0']['rate'] > 0.9, E['obj_ptr']['0']['rate'])
A('S3 raw 富集被分母病放大（>5 倍于 ptr 富集）',
  res['S3_obj0_over_obj4_raw'] > 5 * res['S3_obj0_over_obj4_ptr'],
  '%s vs %s' % (res['S3_obj0_over_obj4_raw'], res['S3_obj0_over_obj4_ptr']))
A('S3 栈类偏移0 ptr-like 率与对象类差 < 0.05（富集不是对象独有）',
  abs(E['stack_ptr']['0']['rate'] - E['obj_ptr']['0']['rate']) < 0.05,
  abs(E['stack_ptr']['0']['rate'] - E['obj_ptr']['0']['rate']))
G('N1 伪虚表偏移0 覆盖塌到 < 5', len({s[3] for s in fake0}) < 5, len({s[3] for s in fake0}))
G('N2 非虚表同形链的槽目标落 .text 为 0', nT == 0, nT)
G('N2 非虚表同形链的 vt-4 回指 COL 为 0', nC == 0, nC)
G('N3 绝对基址派发点单独归类且非零', abs_disp > 0, abs_disp)
G('N4 派发点全落在 objdump 起点集', sum(1 for r in rec if r[0] in starts) == len(rec))
G('N4 起点集基线 < 0.5', len(starts) / B.T[4] < 0.5)
G('N5 偏移4 的链式命中远少于偏移0', len(CH4) < 0.1 * len(CH), '%d vs %d' % (len(CH4), len(CH)))

res['POS'] = POS; res['NEG'] = NEG
res['pos_pass'] = sum(1 for _, c, _ in POS if c); res['pos_fail'] = sum(1 for _, c, _ in POS if not c)
res['neg_pass'] = sum(1 for _, c, _ in NEG if c); res['neg_fail'] = sum(1 for _, c, _ in NEG if not c)
for n, c, d in POS + NEG:
    if not c: print('FAIL:', n, d)
print(json.dumps({k: v for k, v in res.items() if k not in ('POS', 'NEG')}, ensure_ascii=False, indent=1)[:4000])
print('POS %d/%d NEG %d/%d' % (res['pos_pass'], len(POS), res['neg_pass'], len(NEG)))
json.dump(res, open('_r143/r143p_closure.json', 'w'), ensure_ascii=False, indent=1)
sys.exit(1 if (res['pos_fail'] or res['neg_fail']) else 0)
