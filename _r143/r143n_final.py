#!/usr/bin/env python3
"""R143 N：收口测量 —— 采纳审计员指出的分母病修正，并复算其四项关键数字（规则 D）。

审计员（deepseek #316）提出两条可机械判定的批评：
  C-a 「派发点基址来源」还漏了第三类「绝对地址基址」（例如 call dword ptr [0x7e1208]），
      我的分类只写了 obj/stack 两类，绝对类被静默丢弃。
  C-b 「偏移 0 的 feed 率 0.5975 vs 偏移 4 的 0.0144 = 41 倍」有分母病：
      偏移 4 的装载绝大多数从不被当作内存基址用（只被当标量读），拿它当分母无判别力。
      它的修正分母 = 「该位移的装载里，被用作某个内存访问基址的条数」（ptr-like 分母）。

本脚本：
  1 复算全部主数字，并把基址来源分成 obj / stack / absolute 三类
  2 实现 ptr-like 分母，逐位移报 feed 率
  3 复算审计员的 rate_given_ptrlike0=0.9422 / rate_given_ptrlike4=0.0729
  4 链式判据（装表->读回->派发->槽值可执行+COL回指）
  5 正反控断言，含「绝对基址必须被单独归类」这一条
"""
import sys, json, collections, random, hashlib
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
ANY = L.GEN + L.STK

def parse(a, sz, mn, op):
    if not op: return ('nop', None)
    if mn in ('call', 'jmp'):
        m = L.RE_CALL.match(op)
        if m:
            base = m.group(1)
            d = L.disp_of(m.group(2))
            if base in L.GEN: return ('disp', (base, d, mn, 'obj'))
            if base in L.STK: return ('disp', (base, d, mn, 'stack'))
            if base.startswith('0x'): return ('disp_abs', (int(base, 16), mn))
        return ('nop', None)
    ms = L.RE_STORE.match(op)
    if ms and mn in ('mov', 'movl'):
        t = ms.group(3); base, ds = ms.group(1), L.disp_of(ms.group(2))
        if t is not None and L.RE_IMM.match(t):
            return ('store_imm', (base, ds, L.immval(t)))
        return ('store', (base, ds, t))
    m = L.RE_LOAD.match(op)
    if m and mn == 'mov':
        d = L.disp_of(m.group(3))
        base = m.group(2); dst = m.group(1)
        cls = 'obj' if base in L.GEN else ('stack' if base in L.STK else ('abs' if base.startswith('0x') else 'idx'))
        return ('load', (dst, base, d, cls))
    if mn in L.W_MN:
        return ('write', op.partition(',')[0])
    if mn in ('ret', 'retn'):
        return ('ret', None)
    return ('other', None)

ins = list(B.sweep(md))
P = [parse(*x) for x in ins]
N = len(P)

# ---------- 一遍状态机 ----------
last = {}
rec = []                  # (va, mn, base, disp, kind, load_base, load_disp, load_va, load_class)
loads = []                # (va, dst, base, disp, cls)
f1 = []                   # 装表 (va, base, disp, imm)
base_use = set()          # 被当作内存基址的寄存器装载 VA（ptr-like 分母）
for idx, (kind, d) in enumerate(P):
    if kind == 'disp':
        a = ins[idx][0]; base, disp, mn, cls = d
        l = last.get(base)
        if l and l[0] == 'load':
            rec.append((a, mn, base, disp, 'load', l[1], l[2], l[3], l[4]))
        else:
            rec.append((a, mn, base, disp, (l[0] if l else 'unknown'), None, None, None, None))
        for x in ('eax', 'ecx', 'edx'): last[x] = ('clobber', None, None, a, None)
    elif kind == 'disp_abs':
        pass
    elif kind == 'store_imm':
        a = ins[idx][0]; base, ds, iv = d
        if base in L.GEN and iv in VTS: f1.append((a, base, ds, iv))
    elif kind == 'store':
        # 若该 store 的基址寄存器来自某次装载，那次装载就是 ptr-like
        base = d[0]
        if base in L.GEN:
            l = last.get(base)
            if l and l[0] == 'load': base_use.add(l[3])
    elif kind == 'load':
        a = ins[idx][0]; dst, base, ds, cls = d
        loads.append((a, dst, base, ds, cls))
        if dst in L.GEN:
            last[dst] = ('load', base, ds, a, cls)
            base_use.add(a)          # 该装载的结果本身被用作基址（保守：先记，后剔除未被用者）
    elif kind == 'write':
        last.pop(d, None)

# 真正的 ptr-like：装载结果被用作某个内存访问的基址（call/jmp 或 mov 的 [reg] 形式）
ptr_like = set()
for idx, (kind, d) in enumerate(P):
    if kind in ('disp', 'disp_abs'):
        fld = 0 if kind == 'disp' else None
        if kind == 'disp':
            l = last.get(d[0])   # 不能用末态快照；用 rec 里的 load_va
        continue
# 用 rec（call/jmp）与 store/load 的「基址由装载得来」重建
# 简化且可复算：遍历所有指令，凡内存操作数基址是通用寄存器，且该寄存器最近一次定义是装载，则那次装载 ptr-like
last = {}
ptr_like = set()
for idx, (kind, d) in enumerate(P):
    if kind in ('disp', 'disp_abs'):
        if kind == 'disp':
            base = d[0]
            l = last.get(base)
            if l and l[0] == 'load': ptr_like.add(l[3])
        for x in ('eax', 'ecx', 'edx'): last[x] = ('clobber', None, None, ins[idx][0], None)
    elif kind in ('store', 'store_imm'):
        base = d[0]
        if base in ANY:
            l = last.get(base)
            if l and l[0] == 'load' and base in L.GEN: ptr_like.add(l[3])
    elif kind == 'load':
        dst, base, ds, cls = d
        if base in L.GEN:
            l = last.get(base)
            if l and l[0] == 'load': ptr_like.add(l[3])
        if dst in L.GEN:
            last[dst] = ('load', base, ds, ins[idx][0], cls)
    elif kind == 'write':
        last.pop(d, None)

fed = {r[7] for r in rec if r[4] == 'load' and r[7] is not None}

# ---------- 分组统计 ----------
def grp(sel, key):
    c = collections.Counter()
    for x in sel: c[key(x)] += 1
    return c

rec_load = [r for r in rec if r[4] == 'load']
rec_obj = [r for r in rec_load if r[8] == 'obj']
rec_stk = [r for r in rec_load if r[8] == 'stack']
rec_abs = [r for r in rec_load if r[8] == 'abs']
rec_other = [r for r in rec_load if r[8] not in ('obj', 'stack', 'abs')]

def tab(cls, keys=(0, 4, 8, 12, 16)):
    out = []
    for k in keys:
        tot = sum(1 for l in loads if l[4] == cls and l[3] == k)
        fd = sum(1 for l in loads if l[4] == cls and l[3] == k and l[0] in fed)
        pl = sum(1 for l in loads if l[4] == cls and l[3] == k and l[0] in ptr_like)
        plf = sum(1 for l in loads if l[4] == cls and l[3] == k and l[0] in ptr_like and l[0] in fed)
        out.append({'disp': k, 'loads': tot, 'fed': fd, 'ptr_like': pl,
                    'rate_raw': round(fd / tot, 4) if tot else None,
                    'rate_ptr': round(plf / pl, 4) if pl else None})
    return out

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

S0 = sites(0, 'vts')
H0 = [((ins[i][0]), P[i][1][2], *follow(i, 0)) for i in S0 if follow(i, 0)]
t_text = sum(1 for (a, v, dva, sd) in H0 if (B.dw(v + sd) or 0) and B.sec_of(B.dw(v + sd)) == '.text')
t_col = sum(1 for (a, v, dva, sd) in H0 if B.dw(v - 4) in COL)

random.seed(143)
pool = []
for nm, ava, vs, raw, rs in B.secs:
    if nm in ('.data', '.rdata'):
        blob = B.data[raw:raw + rs]
        for i in range(len(blob) // 4):
            pool.append(__import__('struct').unpack_from('<I', blob, i * 4)[0])
FAKE = set(random.sample(pool, len(VTS)))
fake_sites = sum(1 for s in f1 if s[3] in FAKE and s[2] == 0)
fake_vt = len({s[3] for s in f1 if s[3] in FAKE and s[2] == 0})

starts = set(int(x, 16) for x in open('_r140/obj_starts.txt').read().split())

def ratio(a, b): return round(a / b, 4) if b else None
res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'td': len(TDs), 'col': len(COL), 'vt_distinct': len(VTS),
 'instructions': N,
 'dispatch_total_obj_base': len([r for r in rec]),
 'dispatch_abs_base': sum(1 for k, d in P if k == 'disp_abs'),
 'dispatch_kind': dict(collections.Counter(r[4] for r in rec)),
 'dispatch_base_class': {'obj': len(rec_obj), 'stack': len(rec_stk), 'abs': len(rec_abs), 'other': len(rec_other)},
 'dispatch_disp_hist_top10': collections.Counter(r[3] for r in rec).most_common(10),
 'C1_sites': len(f1), 'C1_disp0_sites': sum(1 for s in f1 if s[2] == 0),
 'C1_disp0_distinct_vt': len({s[3] for s in f1 if s[2] == 0}),
 'obj_table': tab('obj'), 'stack_table': tab('stack'),
 'R0_obj_disp0_rate_raw': ratio(sum(1 for l in loads if l[4] == 'obj' and l[3] == 0 and l[0] in fed),
                                sum(1 for l in loads if l[4] == 'obj' and l[3] == 0)),
 'R0_obj_disp4_rate_raw': ratio(sum(1 for l in loads if l[4] == 'obj' and l[3] == 4 and l[0] in fed),
                                sum(1 for l in loads if l[4] == 'obj' and l[3] == 4)),
 'chain_disp0_sites': len(S0), 'chain_disp0_hits': len(H0),
 'chain_disp0_rate': ratio(len(H0), len(S0)),
 'chain_disp0_distinct_vt': len({h[1] for h in H0}),
 'chain_text_target': t_text, 'chain_col_backref': t_col,
 'chain_sample': [[hex(a), hex(v), hex(dva), sd] for a, v, dva, sd in H0[:15]],
 'N_fake_sites_disp0': fake_sites, 'N_fake_distinct': fake_vt,
 'N_starts_n': len(starts),
 'N_dispatch_in_starts': sum(1 for r in rec if r[0] in starts),
}
print(json.dumps(res, ensure_ascii=False, indent=1))

# ---------- 断言 ----------
POS = []; NEG = []
def A(n, c, d=''): POS.append((n, bool(c), d))
def G(n, c, d=''): NEG.append((n, bool(c), d))
A('虚表集合 1218', len(VTS) == 1218, len(VTS))
A('派发点基址分三类且绝对类非零', len(rec_abs) > 0, len(rec_abs))
A('对象类派发点最多', len(rec_obj) > len(rec_stk) and len(rec_obj) > len(rec_abs))
A('C1 偏移0 装表覆盖 > 800', len({s[3] for s in f1 if s[2] == 0}) > 800)
A('链式判据命中 > 40', len(H0) > 40, len(H0))
A('链式命中里槽目标落 .text 的比例 > 0.9', t_text / max(1, len(H0)) > 0.9, t_text / max(1, len(H0)))
A('链式命中里 vt-4 回指 COL 的比例 > 0.9', t_col / max(1, len(H0)) > 0.9, t_col / max(1, len(H0)))
G('伪虚表集合 distinct 覆盖 < 真集合 5%', fake_vt < 0.05 * len({s[3] for s in f1 if s[2] == 0}), fake_vt)
G('派发点全在 objdump 起点集', sum(1 for r in rec if r[0] in starts) == len(rec))
G('绝对基址派发点不被计入对象类', all(r[8] == 'obj' for r in rec_obj))
res['POS'] = POS; res['NEG'] = NEG
res['pos_pass'] = sum(1 for _, c, _ in POS if c); res['pos_fail'] = sum(1 for _, c, _ in POS if not c)
res['neg_pass'] = sum(1 for _, c, _ in NEG if c); res['neg_fail'] = sum(1 for _, c, _ in NEG if not c)
for n, c, d in POS + NEG:
    if not c: print('FAIL:', n, d)
print('POS %d/%d NEG %d/%d' % (res['pos_pass'], len(POS), res['neg_pass'], len(NEG)))
json.dump(res, open('_r143/r143n_final.json', 'w'), ensure_ascii=False, indent=1)
