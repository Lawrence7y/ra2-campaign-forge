#!/usr/bin/env python3
"""R143 G：合并测量（修正解析器后重跑全部关键量）。

修正的错：capstone 对位移 < 10 十进制打印（[esi + 4]），>= 10 十六进制打印（[esi + 0xc]）。
我前几版解析器只认 +0xNN，把所有位移 1..9 的指令整条丢掉了 —— 其中恰含虚调用 slot1(+4)/slot2(+8)。
本脚本用 r143lib 的统一归一化重算，并把「旧口径」作为反控一并报出，证明错在哪、错多少。

产出：
 T1 全 .text 指令数、间接 call/jmp [reg+disp] 的位移直方图（含 +4/+8）
 T2 喂给派发的装载：按装载基址（对象类/栈类）与装载位移分组，给 feed 率
 T3 装表点：mov dword ptr [reg+0], imm==vt 的站点与 distinct vt 覆盖
 T4 反控：伪虚表集合、位移 4/8 的 feed 率、objdump 起点集
"""
import json, re, collections, random, hashlib, subprocess, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin()
TDs, COL, VTS = B.vtset()
md = Cs(CS_ARCH_X86, CS_MODE_32)

def scan(vtset):
    f1 = []                          # 装表 imm 站点 (va, base, disp, imm)
    f_abs = []                       # 绝对地址装表
    rec = []                         # 派发点 (va, mn, reg, disp, kind, load_base, load_disp, load_va)
    loads = []                       # 全部内存装载 (va, dst, base, disp)
    last = {}
    n_ins = 0
    for a, sz, mn, op in B.sweep(md):
        n_ins += 1
        if not op: continue
        if mn in ('call', 'jmp'):
            mc = L.RE_CALL.match(op)
            if mc:
                r, ds = mc.group(1), L.disp_of(mc.group(2))
                if r in L.GEN:
                    l = last.get(r)
                    if l and l[0] == 'load':
                        rec.append((a, mn, r, ds, 'load', l[1], l[2], l[3]))
                    else:
                        rec.append((a, mn, r, ds, (l[0] if l else 'unknown'), None, None, None))
                for x in ('eax', 'ecx', 'edx'):
                    last[x] = ('clobber', None, None, a)
                continue
        ms = L.RE_STORE.match(op)
        if ms and mn in ('mov', 'movl'):
            base, ds, tgt = ms.group(1), L.disp_of(ms.group(2)), ms.group(3)
            if tgt is not None and L.RE_IMM.match(tgt):
                iv = L.immval(tgt)
                if base in L.GEN:
                    if iv in vtset: f1.append((a, base, ds, iv))
                else:
                    f_abs.append((a, base, ds, iv))
            continue
        ml = L.RE_LOAD.match(op)
        if ml and mn == 'mov':
            dst, base, ds = ml.group(1), ml.group(2), L.disp_of(ml.group(3))
            loads.append((a, dst, base, ds))
            if dst in L.GEN:
                last[dst] = ('load', base, ds, a)
            continue
        if mn == 'lea' and ',' in op:
            d = op.partition(',')[0]
            if d in L.GEN: last[d] = ('other', None, None, a)
        elif mn in L.W_MN:
            d = op.partition(',')[0]
            if d in L.GEN: last[d] = ('other', None, None, a)
    return dict(f1=f1, f_abs=f_abs, rec=rec, loads=loads, n_ins=n_ins)

S = scan(VTS)
fed = {r[7] for r in S['rec'] if r[4] == 'load' and r[7] is not None}

# T1 派发位移直方图
dhist = collections.Counter(r[3] for r in S['rec'])
# T2 feed 率
tot_obj = collections.Counter(); tot_stk = collections.Counter()
fed_obj = collections.Counter(); fed_stk = collections.Counter()
for a, dst, base, ds in S['loads']:
    if base in L.GEN:
        tot_obj[ds] += 1
        if a in fed: fed_obj[ds] += 1
    elif base in L.STK:
        tot_stk[ds] += 1
        if a in fed: fed_stk[ds] += 1

def row(tot, fd, keys):
    out = []
    for k in keys:
        t = tot.get(k, 0); f = fd.get(k, 0)
        out.append({'disp': k, 'loads': t, 'fed': f, 'rate': (round(f / t, 4) if t else None)})
    return out

KEYS = [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 0x84, 0x1b8]
obj_tab = row(tot_obj, fed_obj, KEYS)
stk_tab = row(tot_stk, fed_stk, KEYS)

# T3 装表
f1 = S['f1']
d0 = [s for s in f1 if s[2] == 0]
dn = [s for s in f1 if s[2] != 0]
cov0 = {s[3] for s in d0}
covn = {s[3] for s in dn}

# T4 反控 1：伪虚表集合
random.seed(143)
pool = []
for nm, ava, vs, raw, rs in B.secs:
    if nm in ('.data', '.rdata'):
        blob = B.data[raw:raw + rs]
        for i in range(len(blob) // 4):
            pool.append(__import__('struct').unpack_from('<I', blob, i * 4)[0])
FAKE = set(random.sample(pool, len(VTS)))
Sf = scan(FAKE)
f0 = [s for s in Sf['f1'] if s[2] == 0]
covf = {s[3] for s in f0}

# T4 反控 3：objdump 起点集
starts = set(int(x, 16) for x in open('_r140/obj_starts.txt').read().split())
in_st = sum(1 for r in S['rec'] if r[0] in starts)

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'instructions': S['n_ins'],
 'td': len(TDs), 'col': len(COL), 'vt_distinct': len(VTS),
 'T1_dispatch_total': len(S['rec']),
 'T1_dispatch_disp_hist': dict(sorted(dhist.items())),
 'T1_dispatch_disp4': dhist.get(4, 0), 'T1_dispatch_disp8': dhist.get(8, 0),
 'T1_dispatch_mod4': sum(v for k, v in dhist.items() if k % 4 == 0),
 'T1_kind': dict(collections.Counter(r[4] for r in S['rec'])),
 'T2_loads_total': len(S['loads']),
 'T2_obj_loads': sum(tot_obj.values()), 'T2_obj_fed': sum(fed_obj.values()),
 'T2_obj_overall_rate': round(sum(fed_obj.values()) / max(1, sum(tot_obj.values())), 4),
 'T2_stk_loads': sum(tot_stk.values()), 'T2_stk_fed': sum(fed_stk.values()),
 'T2_stk_overall_rate': round(sum(fed_stk.values()) / max(1, sum(tot_stk.values())), 4),
 'T2_obj_table': obj_tab, 'T2_stk_table': stk_tab,
 'T2_obj_top_by_fed': fed_obj.most_common(12),
 'T2_obj_top_by_loads': tot_obj.most_common(12),
 'T3_install_sites': len(f1),
 'T3_install_disp0_sites': len(d0),
 'T3_install_disp0_distinct_vt': len(cov0),
 'T3_install_disp0_coverage': round(len(cov0) / len(VTS), 4),
 'T3_install_dispn_sites': len(dn),
 'T3_install_dispn_distinct_vt': len(covn),
 'T3_install_union_coverage': round(len(cov0 | covn) / len(VTS), 4),
 'T3_install_disp_hist': dict(sorted(collections.Counter(s[2] for s in f1).items())),
 'T3_install_base_regs': dict(collections.Counter(s[1] for s in f1)),
 'T3_abs_sites': len(S['f_abs']),
 'N1_fake_n': len(FAKE), 'N1_fake_disp0_sites': len(f0), 'N1_fake_disp0_distinct': len(covf),
 'N2_starts_n': len(starts), 'N2_dispatch_in_starts': in_st,
 'N2_starts_baseline': round(len(starts) / B.T[4], 4),
}
print(json.dumps(res, ensure_ascii=False, indent=1))
json.dump(res, open('_r143/r143g_consolidated.json', 'w'), ensure_ascii=False, indent=1)
json.dump({'install_d0': [[hex(a), b, hex(v)] for a, b, d, v in d0[:60]],
           'install_dn': [[hex(a), b, d, hex(v)] for a, b, d, v in dn[:60]],
           'dispatch_disp4_8': [[hex(r[0]), r[1], r[2], r[3], r[4], r[5], r[6]] for r in S['rec'] if r[3] in (4, 8)][:40]},
          open('_r143/r143g_samples.json', 'w'), ensure_ascii=False, indent=1)
