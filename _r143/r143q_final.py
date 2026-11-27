#!/usr/bin/env python3
"""R143 Q：收口最终版（含本轮自错 S-292/S-293 的反控）。

本轮自错两条，必须先被脚本抓出而不是写进结论：
  S-292 「vt-4 回指 COL 率 = 1.0」是**同义反复**：虚表集合 VTS 的定义就是 dword[vt-4] 属于 COL。
        反控：随机 1218 个 .data dword 里 vt-4 ∈ COL 只有 9 个（0.74%），说明它不是恒真，
        但对 VTS 成员是恒真 ⇒ 该子项**零判别力**，不得当证据用。
  S-293 「raw 富集 41.5 倍」是**分母病**：偏移 4 的装载 10,450 条里只有 716 条被当内存基址用。
        改用 ptr-like 分母后是 4.5 倍；且**栈类偏移 0 的 ptr-like 率 0.9667 与对象类 0.9486 几乎相同**
        ⇒ 「偏移 0 常被当指针基址」是偏移 0 的共性，不是对象独有的性质，不能用来支持 vptr。

真正有判别力的只有一条：链式闭合的语义层 —— 槽值落 .text 的比率
  VTS 链：68 条里 67 条（98.5%）；随机 .data dword 当虚表：332 个槽值里 3 个（0.9%）
且非虚表 imm 的同形链 20 条、槽值落 .text **0 条**（因为这些 imm 是 0x0/0x6c 一类小整数）。
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
        t = ms.group(3); base = ms.group(1); ds = L.disp_of(ms.group(2))
        if t is not None and L.RE_IMM.match(t): return ('store_imm', (base, ds, L.immval(t)))
        return ('store', (base, ds))
    if mn in L.W_MN: return ('write', op.partition(',')[0])
    if mn in ('ret', 'retn'): return ('ret', None)
    return ('other', None)

ins = list(B.sweep(md)); P = [parse(*x) for x in ins]; N = len(P)

f1 = []; loads = []; rec = []; last = {}
fed = set(); ptr = set()
for i, (k, d) in enumerate(P):
    if k == 'disp':
        base, disp, mn = d
        l = last.get(base)
        rec.append((ins[i][0], mn, base, disp, bool(l)))
        if l: fed.add(l); ptr.add(l)
        for x in ('eax', 'ecx', 'edx'): last.pop(x, None)
    elif k in ('disp_stk', 'disp_abs', 'callother'):
        for x in ('eax', 'ecx', 'edx'): last.pop(x, None)
    elif k == 'store_imm':
        base, ds, iv = d
        if base in L.GEN:
            l = last.get(base)
            if l: ptr.add(l)
            if iv in VTS: f1.append((ins[i][0], base, ds, iv))
    elif k == 'store':
        base = d[0]
        if base in L.GEN:
            l = last.get(base)
            if l: ptr.add(l)
    elif k == 'load':
        dst, base, ds, cls = d
        loads.append((ins[i][0], dst, base, ds, cls))
        if base in L.GEN:
            l = last.get(base)
            if l: ptr.add(l)
        if dst in L.GEN: last[dst] = ins[i][0]
    elif k == 'write':
        last.pop(d, None)

def enrich(sel_cls, disp):
    tot = [x for x in loads if x[4] == sel_cls and x[3] == disp]
    den = [x for x in tot if x[0] in ptr]
    num = [x for x in tot if x[0] in fed]
    return {'loads': len(tot), 'ptr_den': len(den), 'fed': len(num),
            'rate_raw': round(len(num) / len(tot), 4) if tot else None,
            'rate_ptr': round(len(num) / len(den), 4) if den else None}
E = {c: {str(d): enrich(c, d) for d in (0, 4, 8, 12, 16)} for c in ('obj', 'stack')}

def follow(i, disp, win=200):
    base = P[i][1][0]; j = i + 1; end = min(N, i + 1 + win); loaded = None
    while j < end:
        k, d = P[j]
        if k == 'ret': return None
        if k in ('write', 'store', 'store_imm') and d[0] == base: return None
        if k == 'load' and d[1] == base and d[2] == disp: loaded = d[0]
        elif k == 'disp' and loaded and d[0] == loaded: return (ins[j][0], d[1])
        j += 1
    return None

def chain(disp, cls):
    out = []
    for i, (k, d) in enumerate(P):
        if k != 'store_imm': continue
        base, ds, imm = d
        if base not in L.GEN or ds != disp: continue
        if cls == 'vts' and imm not in VTS: continue
        if cls == 'nonvts' and imm in VTS: continue
        f = follow(i, disp)
        if f: out.append((ins[i][0], imm, f[0], f[1]))
    return out

CH = chain(0, 'vts'); CN = chain(0, 'nonvts'); CH4 = chain(4, 'vts')
def text_targets(H):
    return sum(1 for (a, v, dva, sd) in H
               if B.dw(v + sd) is not None and B.sec_of(B.dw(v + sd)) == '.text')

sv = sum(1 for (k, d) in P if k == 'store_imm' and d[0] in L.GEN and d[1] == 0 and d[2] in VTS)
sn = sum(1 for (k, d) in P if k == 'store_imm' and d[0] in L.GEN and d[1] == 0 and d[2] not in VTS)

random.seed(143)
pool = []
for nm, ava, vs, raw, rs in B.secs:
    if nm in ('.data', '.rdata'):
        blob = B.data[raw:raw + rs]
        for i in range(len(blob) // 4):
            pool.append(__import__('struct').unpack_from('<I', blob, i * 4)[0])
SAMP = random.sample(pool, len(VTS))
rnd_slot_text = 0; rnd_slot_tot = 0
for v in SAMP[:300]:
    for k in (0, 4, 8, 12):
        t = B.dw(v + k)
        if t is not None:
            rnd_slot_tot += 1
            if B.sec_of(t) == '.text': rnd_slot_text += 1
rnd_col = sum(1 for v in SAMP if B.dw(v - 4) in COL)
starts = set(int(x, 16) for x in open('_r140/obj_starts.txt').read().split())
abs_disp = sum(1 for k, d in P if k == 'disp_abs')

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'td': len(TDs), 'col': len(COL), 'vt_distinct': len(VTS), 'instructions': N,
 'install_sites': len(f1), 'install_disp0_sites': sv,
 'install_disp0_distinct_vt': len({s[3] for s in f1 if s[2] == 0}),
 'install_disp0_coverage': round(len({s[3] for s in f1 if s[2] == 0}) / len(VTS), 4),
 'chain_sites_den': sv, 'chain_hits': len(CH), 'chain_rate': round(len(CH) / sv, 4),
 'chain_distinct_vt': len({h[1] for h in CH}),
 'chain_text_targets': text_targets(CH),
 'chain_text_rate': round(text_targets(CH) / len(CH), 4),
 'nonvts_chain_sites_den': sn, 'nonvts_chain_hits': len(CN),
 'nonvts_chain_rate': round(len(CN) / sn, 4),
 'nonvts_chain_text_targets': text_targets(CN),
 'nonvts_imm_top': collections.Counter(hex(h[1]) for h in CN).most_common(6),
 'rand_slot_text': rnd_slot_text, 'rand_slot_tot': rnd_slot_tot,
 'rand_slot_text_rate': round(rnd_slot_text / rnd_slot_tot, 4),
 'rand_col_backref': rnd_col, 'rand_col_rate': round(rnd_col / len(SAMP), 4),
 'enrich': E,
 'enrich_raw_0_over_4': round(E['obj']['0']['rate_raw'] / E['obj']['4']['rate_raw'], 2),
 'enrich_ptr_0_over_4': round(E['obj']['0']['rate_ptr'] / E['obj']['4']['rate_ptr'], 2),
 'stack0_ptr_rate': E['stack']['0']['rate_ptr'],
 'obj0_ptr_rate': E['obj']['0']['rate_ptr'],
 'chain_disp4_hits': len(CH4),
 'abs_base_dispatch': abs_disp,
 'starts_n': len(starts),
 'dispatch_in_starts': sum(1 for r in rec if r[0] in starts),
 'dispatch_total': len(rec),
 'starts_baseline': round(len(starts) / B.T[4], 4),
 'chain_sample': [[hex(a), hex(v), hex(d), s] for a, v, d, s in CH[:10]],
}

POS = []; NEG = []
def A(n, c, d=''): POS.append((n, bool(c), d))
def G(n, c, d=''): NEG.append((n, bool(c), d))
A('虚表集合 1218 / TD 988 / COL 1214', len(VTS) == 1218 and len(TDs) == 988 and len(COL) == 1214)
A('装表：偏移 0 站点 2741', sv == 2741, sv)
A('装表：偏移 0 覆盖 838 distinct 虚表（68.8%）', len({s[3] for s in f1 if s[2] == 0}) == 838)
A('链式判据命中 68 条、覆盖 40 张不同虚表', len(CH) == 68 and len({h[1] for h in CH}) == 40,
  (len(CH), len({h[1] for h in CH})))
A('链式命中里 67/68 的槽值落 .text（98.5%）', text_targets(CH) == 67, text_targets(CH))
A('随机 .data dword 的槽值落 .text 率 < 2%', rnd_slot_text / rnd_slot_tot < 0.02,
  round(rnd_slot_text / rnd_slot_tot, 4))
A('非虚表 imm 的同形链结构率与虚表链同量级（结构本身无判别力）',
  abs(len(CN) / sn - len(CH) / sv) < 0.02, (round(len(CN) / sn, 4), round(len(CH) / sv, 4)))
A('ptr-like 分母富集 4.5 倍（不是 41 倍）', abs(res['enrich_ptr_0_over_4'] - 4.5) < 0.6,
  res['enrich_ptr_0_over_4'])
G('S-292 反控：vt-4 回指 COL 对 VTS 成员恒真（同义反复）', all(B.dw(v - 4) in COL for v in VTS))
G('S-292 反控：随机 dword 的 vt-4 回指 COL 率 < 2%（非恒真）',
  rnd_col / len(SAMP) < 0.02, round(rnd_col / len(SAMP), 4))
G('S-293 反控：raw 富集被分母病放大 8 倍以上',
  res['enrich_raw_0_over_4'] > 8 * res['enrich_ptr_0_over_4'],
  '%s vs %s' % (res['enrich_raw_0_over_4'], res['enrich_ptr_0_over_4']))
G('S-293 反控：栈类偏移0 的 ptr-like 率与对象类差 < 0.05（偏移0 的共性，不证 vptr）',
  abs(E['stack']['0']['rate_ptr'] - E['obj']['0']['rate_ptr']) < 0.05,
  abs(E['stack']['0']['rate_ptr'] - E['obj']['0']['rate_ptr']))
G('非虚表同形链的槽值落 .text 为 0', text_targets(CN) == 0, text_targets(CN))
G('绝对基址派发点单独归类且 4212 个', abs_disp == 4212, abs_disp)
G('派发点 100% 落 objdump 起点集（基线 0.3449）',
  sum(1 for r in rec if r[0] in starts) == len(rec))
G('偏移 4 的链式命中 <= 1（远少于偏移 0 的 68）', len(CH4) <= 1, len(CH4))

res['POS'] = POS; res['NEG'] = NEG
res['pos_pass'] = sum(1 for _, c, _ in POS if c); res['pos_fail'] = sum(1 for _, c, _ in POS if not c)
res['neg_pass'] = sum(1 for _, c, _ in NEG if c); res['neg_fail'] = sum(1 for _, c, _ in NEG if not c)
for n, c, d in POS + NEG:
    if not c: print('FAIL:', n, d)
print(json.dumps(res, ensure_ascii=False, indent=1))
print('POS %d/%d NEG %d/%d' % (res['pos_pass'], len(POS), res['neg_pass'], len(NEG)))
json.dump(res, open('_r143/r143q_final.json', 'w'), ensure_ascii=False, indent=1)
sys.exit(1 if (res['pos_fail'] or res['neg_fail']) else 0)
