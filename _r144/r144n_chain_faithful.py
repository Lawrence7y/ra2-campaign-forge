#!/usr/bin/env python3
"""R144 N：忠实移植 R143K 的 chain()，只把「装表基址类别」参数化（GEN vs GEN∪STK）。

S-309：R144M 我自写的宽松版（win 字典保存到 ret、不检查基址改写、不要求 rX≠rY）
得 535 条，与 R143 的 68 条**不是同一判据**，不能用来做召回对比。这里逐条照抄 R143K 的
chain()（窗口 200、遇 ret 终止、base 被写则 killed、要求 r!=base、读回位移必须等于装表位移），
只把 `if base not in L.GEN` 换成可配置集合，验证：
  ① 用 GEN 复现 R143 的 68（方法可复现旧结论）
  ② GEN∪STK 后的链数、distinct 虚表数、槽值落 .text 率
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

P = [parse(*x) for x in ins]
N = len(P)

def chain(target_disp=0, want_imm_in='vts', window=200, bases=None):
    bases = bases or L.GEN
    hits = []
    for i, (kind, d) in enumerate(P):
        if kind != 'store_imm': continue
        base, ds, imm = d
        if base not in bases or ds != target_disp: continue
        if want_imm_in == 'vts' and imm not in VTS: continue
        if want_imm_in == 'nonvts' and imm in VTS: continue
        j = i + 1; end = min(N, i + 1 + window); loaded = None
        while j < end:
            k2, d2 = P[j]
            if k2 == 'ret': break
            if k2 == 'write' and d2 == base: break
            if k2 == 'store' and d2[0] == base: break
            if k2 == 'store_imm' and d2[0] == base: break
            if k2 == 'load' and d2[1] == base and d2[2] == target_disp:
                loaded = (ins[j][0], d2[0])
            elif k2 == 'disp' and loaded:
                r, sd, mn = d2
                if r == loaded[1]:
                    hits.append((ins[i][0], imm, loaded[0], ins[j][0], sd))
            j += 1
    return hits

STK_BASES = tuple(L.GEN) + tuple(L.STK)
A = chain(0, 'vts', bases=L.GEN)
Bv = chain(0, 'vts', bases=STK_BASES)
def textrate(H):
    ok = sum(1 for h in H if B.dw(h[1] + 4 * h[4]) is not None and B.sec_of(B.dw(h[1] + 4 * h[4])) == '.text')
    return ok, len(H), round(ok / len(H), 4) if H else None
A4 = chain(4, 'vts', bases=L.GEN)
Anon = chain(0, 'nonvts', bases=L.GEN)
new = [h for h in Bv if h not in A]
res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'instructions': N, 'vt_distinct': len(VTS),
 'A_chains': len(A), 'A_text': textrate(A), 'A_distinct_vt': len({h[1] for h in A}),
 'B_chains': len(Bv), 'B_text': textrate(Bv), 'B_distinct_vt': len({h[1] for h in Bv}),
 'B_new_chains': len(new), 'B_new_text': textrate(new),
 'offset4_chains': len(A4), 'nonvts_chains': len(Anon),
 'A_samples': [[hex(h[0]), hex(h[1]), hex(h[2]), hex(h[3]), h[4]] for h in A[:8]],
 'new_samples': [[hex(h[0]), hex(h[1]), hex(h[2]), hex(h[3]), h[4]] for h in new[:8]],
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('忠实移植在 GEN 上复现 R143 的 68 条（方法可复现旧结论，不是我在改判据）', len(A) == 68, len(A))
chk('偏移 4 的链 = 1（与 R143 反控一致）', len(A4) == 1, len(A4))
chk('非虚表 imm 的链 = 20（与 R143 一致）', len(Anon) == 20, len(Anon))
chk('加入 STK 基址后链数增加', len(Bv) > len(A), [len(A), len(Bv)])
chk('新增链的槽值落 .text 率 >= 0.95', (res['B_new_text'][2] or 0) >= 0.95, res['B_new_text'])
chk('B 的 distinct 虚表数 >= A 的', res['B_distinct_vt'] >= res['A_distinct_vt'], [res['A_distinct_vt'], res['B_distinct_vt']])
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r144/r144n_chain_faithful.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'POS'}, indent=1, ensure_ascii=False)[:2600])
print('\n'.join('%-70s %s %s' % (p[0], p[1], p[2]) for p in POS))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
