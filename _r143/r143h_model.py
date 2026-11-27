#!/usr/bin/env python3
"""R143 H：把 C1/C2/C3 三条判据写成带正反控断言的正式测量（修正解析器后）。

修正：capstone 对位移 <10 打印十进制。前几版解析器只认 +0xNN，丢掉全部 +4/+8，
造成「slot1/slot2 从不被虚派发」的假事实（恰与历史「9551 站」口径冲突的根源）。
本版用 r143lib.norm 统一，并对同一批数据同时报「旧口径（漏十进制）」与「新口径」，
使这个自错的影响范围可量化。

判据：
  C1 写入侧：mov dword ptr [reg+0], imm==虚表  => 覆盖多少 distinct 虚表
  C2 读取侧：虚派发基址由 mov reg,[reg2+0] 装载的比例 vs 基线
  C3 相对判据：逐位移的 feed 率（该位移被用作派发基址的装载 / 该位移全部装载）
               —— 若偏移 0 不是 vptr，则 feed 率在 0 与 4/8 上应当同量级
"""
import sys, json, re, collections, random, hashlib
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin()
TDs, COL, VTS = B.vtset()
md = Cs(CS_ARCH_X86, CS_MODE_32)

def sweep_old():
    """旧口径：只认 +0xNN/-NN，丢掉十进制小位移。用于量化自错。"""
    off = B.T[3]; end = off + B.T[4]
    while off < end:
        chunkb = B.data[off:min(off + 65536, end)]
        base = B.IB + (B.T[1] + (off - B.T[3]))
        consumed = 0
        for a, sz, mn, op in md.disasm_lite(chunkb, base):
            if a - base + sz > len(chunkb): break
            consumed = a - base + sz
            o = re.sub(r'\s*([+,*])\s*', r'\1', op or '')   # 不转十进制
            yield a, sz, mn, o
        off += consumed if consumed else 1

RE_STORE3 = re.compile(r'^dword ptr \[([a-z0-9]+)((?:\+0x[0-9a-f]+)|(?:-\d+))?\](?:,([^,]+))?$')
RE_LOAD3 = re.compile(r'^([a-z0-9]+),dword ptr \[([a-z0-9]+)((?:\+0x[0-9a-f]+)|(?:-\d+))?\]$')
RE_CALL3 = re.compile(r'^dword ptr \[([a-z0-9]+)((?:\+0x[0-9a-f]+)|(?:-\d+))?\]$')

def disp_old(s):
    if not s: return 0
    if s.startswith('+0x'): return int(s[3:], 16)
    if s.startswith('-'): return -int(s[1:])
    return 0

def scan(sweeper, vtset, RE_S, RE_L, RE_C, DOF, old=False):
    f1 = []; rec = []; loads = []; last = {}
    for a, sz, mn, op in sweeper():
        if not op: continue
        if mn in ('call', 'jmp'):
            mc = RE_C.match(op)
            if mc and mc.group(1) in L.GEN:
                r = mc.group(1); d = DOF(mc.group(2))
                l = last.get(r)
                rec.append((a, mn, r, d, 'load' if (l and l[0] == 'load') else (l[0] if l else 'unknown'),
                            l[1] if l and l[0] == 'load' else None,
                            l[2] if l and l[0] == 'load' else None,
                            l[3] if l and l[0] == 'load' else None))
            for x in ('eax', 'ecx', 'edx'):
                last[x] = ('clobber', None, None, a)
            continue
        ms = RE_S.match(op)
        if ms and mn in ('mov', 'movl'):
            base, ds, tgt = ms.group(1), DOF(ms.group(2)), ms.group(3)
            if tgt is not None and L.RE_IMM.match(tgt) and base in L.GEN:
                iv = L.immval(tgt)
                if iv in vtset: f1.append((a, base, ds, iv))
            continue
        ml = RE_L.match(op)
        if ml and mn == 'mov':
            dst, base, ds = ml.group(1), ml.group(2), DOF(ml.group(3))
            loads.append((a, dst, base, ds))
            if dst in L.GEN: last[dst] = ('load', base, ds, a)
            continue
        if mn == 'lea' and ',' in op:
            d = op.partition(',')[0]
            if d in L.GEN: last[d] = ('other', None, None, a)
        elif mn in L.W_MN:
            d = op.partition(',')[0]
            if d in L.GEN: last[d] = ('other', None, None, a)
    return dict(f1=f1, rec=rec, loads=loads)

NEW = scan(lambda: B.sweep(md), VTS, L.RE_STORE, L.RE_LOAD, L.RE_CALL, L.disp_of)
OLD = scan(sweep_old, VTS, RE_STORE3, RE_LOAD3, RE_CALL3, disp_old, old=True)
FAKE = None
random.seed(143)
pool = []
for nm, ava, vs, raw, rs in B.secs:
    if nm in ('.data', '.rdata'):
        blob = B.data[raw:raw + rs]
        for i in range(len(blob) // 4):
            pool.append(__import__('struct').unpack_from('<I', blob, i * 4)[0])
FAKE = set(random.sample(pool, len(VTS)))
FG = scan(lambda: B.sweep(md), FAKE, L.RE_STORE, L.RE_LOAD, L.RE_CALL, L.disp_of)

def feed_stats(S):
    fed = {r[7] for r in S['rec'] if r[4] == 'load' and r[7] is not None}
    tot = collections.Counter(); f = collections.Counter()
    tot_s = collections.Counter(); f_s = collections.Counter()
    for a, dst, base, ds in S['loads']:
        if base in L.GEN:
            tot[ds] += 1
            if a in fed: f[ds] += 1
        elif base in L.STK:
            tot_s[ds] += 1
            if a in fed: f_s[ds] += 1
    return fed, tot, f, tot_s, f_s

fed, tot, fobj, tots, fstk = feed_stats(NEW)
fedO, totO, fobjO, totsO, fstkO = feed_stats(OLD)

def r(a, b): return round(a / b, 4) if b else None

keys = [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40]
obj_tab = [{'disp': k, 'loads': tot.get(k, 0), 'fed': fobj.get(k, 0),
            'rate': r(fobj.get(k, 0), tot.get(k, 0))} for k in keys]
stk_tab = [{'disp': k, 'loads': tots.get(k, 0), 'fed': fstk.get(k, 0),
            'rate': r(fstk.get(k, 0), tots.get(k, 0))} for k in keys]

d0 = [s for s in NEW['f1'] if s[2] == 0]
cov0 = {s[3] for s in d0}
f0 = [s for s in FG['f1'] if s[2] == 0]
covf = {s[3] for s in f0}
old_cov0 = {s[3] for s in OLD['f1'] if s[2] == 0}

starts = set(int(x, 16) for x in open('_r140/obj_starts.txt').read().split())
res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'td': len(TDs), 'col': len(COL), 'vt_distinct': len(VTS),
 'C1_install_disp0_sites': len(d0),
 'C1_install_disp0_distinct_vt': len(cov0),
 'C1_install_disp0_coverage': r(len(cov0), len(VTS)),
 'C1_install_all_sites': len(NEW['f1']),
 'C2_dispatch_total': len(NEW['rec']),
 'C2_kind': dict(collections.Counter(x[4] for x in NEW['rec'])),
 'C2_obj_loads': sum(tot.values()), 'C2_obj_fed': sum(fobj.values()),
 'C2_obj_overall_rate': r(sum(fobj.values()), sum(tot.values())),
 'C2_obj_table': obj_tab,
 'C2_stk_loads': sum(tots.values()), 'C2_stk_fed': sum(fstk.values()),
 'C2_stk_overall_rate': r(sum(fstk.values()), sum(tots.values())),
 'C2_stk_table': stk_tab,
 'C3_rate0_over_rate4': r(fobj.get(0, 0) / max(1, tot.get(0, 1)), fobj.get(4, 0) / max(1, tot.get(4, 1))),
 'C3_rate0_over_rate8': r(fobj.get(0, 0) / max(1, tot.get(0, 1)), fobj.get(8, 0) / max(1, tot.get(8, 1))),
 'OLD_C1_install_disp0_distinct_vt': len(old_cov0),
 'OLD_C2_dispatch_total': len(OLD['rec']),
 'OLD_C2_obj_loads': sum(totO.values()), 'OLD_C2_obj_fed': sum(fobjO.values()),
 'OLD_C2_obj_overall_rate': r(sum(fobjO.values()), sum(totO.values())),
 'OLD_C2_disp4_loads': totO.get(4, 0), 'OLD_C2_disp8_loads': totO.get(8, 0),
 'N1_fake_n': len(FAKE), 'N1_fake_disp0_sites': len(f0), 'N1_fake_disp0_distinct': len(covf),
 'N2_starts_n': len(starts),
 'N2_dispatch_in_starts': sum(1 for x in NEW['rec'] if x[0] in starts),
 'N2_starts_baseline': r(len(starts), B.T[4]),
}
print(json.dumps(res, ensure_ascii=False, indent=1))

# ---- 断言 ----
POS = []
def A(name, cond, det=''):
    POS.append((name, bool(cond), det))
A('虚表集合 1218', len(VTS) == 1218, len(VTS))
A('C1 偏移0 装表覆盖 >= 800 张表', len(cov0) >= 800, len(cov0))
A('C1 偏移0 站点数 > 2500', len(d0) > 2500, len(d0))
A('C2 派发点 > 18000', len(NEW['rec']) > 18000, len(NEW['rec']))
A('C2 对象类装载偏移0 feed 率 > 0.5', fobj.get(0, 0) / tot.get(0, 1) > 0.5, fobj.get(0, 0) / tot.get(0, 1))
A('C2 偏移0 feed 率是偏移4 的 20 倍以上',
  (fobj.get(0, 0) / tot.get(0, 1)) / max(1e-9, fobj.get(4, 0) / tot.get(4, 1)) > 20)
A('C2 偏移0 feed 率是偏移8 的 20 倍以上',
  (fobj.get(0, 0) / tot.get(0, 1)) / max(1e-9, fobj.get(8, 0) / tot.get(8, 1)) > 20)
A('C2 栈类偏移0 feed 率低于对象类', fstk.get(0, 0) / tots.get(0, 1) < fobj.get(0, 0) / tot.get(0, 1))
A('旧口径确实丢掉 displacement 4/8', totO.get(4, 0) == 0 and totO.get(8, 0) == 0)
A('新口径 displacement 4 装载 > 10000', tot.get(4, 0) > 10000, tot.get(4, 0))
NEG = []
def N(name, cond, det=''):
    NEG.append((name, bool(cond), det))
N('N1 伪集合 distinct 覆盖 < 20', len(covf) < 20, len(covf))
N('N1 伪集合 distinct 覆盖 < 真集合 5%', len(covf) < 0.05 * len(cov0), '%d vs %d' % (len(covf), len(cov0)))
N('N2 派发点全在 objdump 起点集', sum(1 for x in NEW['rec'] if x[0] in starts) == len(NEW['rec']))
N('N2 起点集基线 < 0.5', len(starts) / B.T[4] < 0.5)
res['POS'] = POS; res['NEG'] = NEG
res['pos_pass'] = sum(1 for _, c, _ in POS if c); res['pos_fail'] = sum(1 for _, c, _ in POS if not c)
res['neg_pass'] = sum(1 for _, c, _ in NEG if c); res['neg_fail'] = sum(1 for _, c, _ in NEG if not c)
for n, c, d in POS + NEG:
    if not c: print('FAIL:', n, d)
print('POS %d/%d  NEG %d/%d' % (res['pos_pass'], len(POS), res['neg_pass'], len(NEG)))
json.dump(res, open('_r143/r143h_model.json', 'w'), ensure_ascii=False, indent=1)
json.dump({'d0_head': [[hex(a), b, hex(v)] for a, b, d, v in d0[:60]],
           'rec_head': [[hex(x[0]), x[1], x[2], x[3], x[4], x[5], x[6]] for x in NEW['rec'][:40]]},
          open('_r143/r143h_samples.json', 'w'), ensure_ascii=False, indent=1)
sys.exit(1 if (res['pos_fail'] or res['neg_fail']) else 0)
