#!/usr/bin/env python3
"""R146 D：大位移组的**决定性结构判据** —— COL.offset 与写入位移的关系。

r146c 已定位：large 组基址 92.6% 来自 `mov reg,reg`（REG，中位回溯距离 191 B），
small 组中位仅 29 B ⇒ 基址不是就地取的 this，而是长寿命指针变量。

本脚本给出**结构性**判据（不依赖寄存器来源，故与 K1 独立）：
  COL.offset(vt) 是该虚表所属类在自己对象内的 vptr 偏移。
  若一个写入站点是「对象自身的 vptr 安装」，则必然 disp == COL.offset(vt)。
  ⇒ disp != COL.offset(vt) 的站点是**把某个类当成成员/子对象内嵌在更外层结构里**：
     内嵌主对象（COL.offset==0）写在 disp≠0 ⇒ 聚合/成员；
     内嵌非主子对象（COL.offset∈{4,8,12,...}）写在 disp≠它 ⇒ 更深的成员。
判据 D1：large 组「disp == COL.offset」比例 ≈ small 组（若相近则无差别，判据作废）。
判据 D2：large 组中 COL.offset==0 的占比。
判据 D3：把 large 站点按「函数内同 vt 的位移集合」再分：等差=数组，非等差=不同成员。
另对 top 函数 0x665650（54 个 large 站点同属 TypeList<H>）做**逐指令上下文取证**，
这是判定「数组 / 链式成员」最直接的一手证据。
纪律：disasm_lite 流式扫描；仅对目标地址区间用 disasm（不开 detail）。
"""
import sys, re, json, struct, collections, hashlib, time, bisect
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
GEN = L.GEN
COLof = {}
for vt in VTS:
    c = B.dw(vt - 4)
    if c in COL: COLof[vt] = c
coloff = {c: B.dw(c + 4) for c in COL}
coltd = {c: B.dw(c + 12) for c in COL}
def off_of(vt): return coloff.get(COLof.get(vt))
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF
TDname = {td: nm.decode('latin-1', 'replace') for td, nm in TDs.items()}
def name_of(vt):
    c = COLof.get(vt)
    return TDname.get(coltd.get(c)) if c else None

TOL = re.compile(r'^dword ptr \[(.+?)\](?:,(.+))?$')
def parse_mem(s):
    s = s.replace(' ', '')
    m = re.fullmatch(r'([a-z0-9]+)(?:([+-])(0x[0-9a-f]+|\d+))?', s)
    if not m: return None
    if m.group(3) is None: return m.group(1), 0
    v = int(m.group(3), 16) if m.group(3).startswith('0x') else int(m.group(3))
    return m.group(1), (-v if m.group(2) == '-' else v)

sites = []; calltgt = set()
for a, sz, mn, op in B.sweep(md):
    if mn == 'call':
        m2 = re.match(r'^(0x[0-9a-f]+)$', op or '')
        if m2: calltgt.add(int(m2.group(1), 16))
    mt = TOL.match(op or '')
    if not mt or mn != 'mov': continue
    pm = parse_mem(mt.group(1))
    if not pm: continue
    base, disp = pm
    tgt = (mt.group(2) or '').strip()
    if L.RE_IMM.match(tgt) and immv(tgt) in VTS and base in GEN:
        sites.append({'va': a, 'base': base, 'disp': disp, 'vt': immv(tgt),
                      'strict': L.RE_STORE.match(op) is not None})
ct = sorted(calltgt)
def func_of(va):
    i = bisect.bisect_right(ct, va) - 1
    return ct[i] if i >= 0 else None

bucket = lambda d: 'small' if d in (4, 8, 12) else 'large'
nz = [s for s in sites if s['disp'] != 0]
large = [s for s in nz if bucket(s['disp']) == 'large']
small = [s for s in nz if bucket(s['disp']) == 'small']

def agrees(grp):
    return sum(1 for s in grp if off_of(s['vt']) == s['disp'])
res = {'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
       'large': len(large), 'small': len(small)}

# D1/D2
for tag, grp in (('large', large), ('small', small)):
    a = agrees(grp)
    res['D_' + tag] = {
        'n': len(grp), 'agree': a, 'agree_frac': round(a / len(grp), 4),
        'coloff_zero': sum(1 for s in grp if off_of(s['vt']) == 0),
        'coloff_zero_frac': round(sum(1 for s in grp if off_of(s['vt']) == 0) / len(grp), 4),
        'coloff_hist': collections.Counter(off_of(s['vt']) for s in grp).most_common(8),
        'disp_hist': collections.Counter(s['disp'] for s in grp).most_common(8)}
res['D_large']['coloff_zero_and_disp_nonzero'] = sum(
    1 for s in large if off_of(s['vt']) == 0 and s['disp'] != 0)
res['D_large']['nonagree_coloff_zero'] = sum(
    1 for s in large if off_of(s['vt']) == 0 and s['disp'] != 0)

# D3 数组 vs 成员：同 (函数, vt) 的位移集合
def d3(grp):
    by = collections.defaultdict(list)
    for s in grp: by[(func_of(s['va']), s['vt'])].append(s['disp'])
    arith = 0; nonarith = 0; single = 0; samples = []
    for k, v in by.items():
        ds = sorted(set(v))
        if len(ds) < 2: single += 1; continue
        gaps = [ds[i + 1] - ds[i] for i in range(len(ds) - 1)]
        if len(set(gaps)) == 1:
            arith += 1
            if len(samples) < 8: samples.append([hex(k[0]) if k[0] else None, name_of(k[1]), len(v), len(ds), 'ARITH', gaps[0], ds[:6]])
        else:
            nonarith += 1
            if len(samples) < 8: samples.append([hex(k[0]) if k[0] else None, name_of(k[1]), len(v), len(ds), 'MIXED', gaps[:5], ds[:6]])
    return {'keys': len(by), 'single': single, 'arith': arith, 'nonarith': nonarith, 'samples': samples}
res['D3_large'] = d3(large); res['D3_small'] = d3(small)

# ---- top 函数 0x665650 逐指令上下文 ----
TOP = 0x665650
ctx = [s for s in large if func_of(s['va']) == TOP]
ctx_sorted = sorted(ctx, key=lambda s: s['va'])
span_lo = ctx_sorted[0]['va'] - 0x40 if ctx_sorted else 0
span_hi = ctx_sorted[-1]['va'] + 0x40 if ctx_sorted else 0
lines = []
if ctx_sorted:
    off = B.va2off(span_lo); n = span_hi - span_lo
    blob = B.data[off:off + n] if off is not None else b''
    for ins in md.disasm(blob, span_lo):          # CsInsn（此处是 <=64KB 小窗口，不用 detail）
        a = ins.address; mark = ''
        for s in ctx:
            if s['va'] == a: mark = '   <== LARGE disp=%d vt=%s %s' % (s['disp'], hex(s['vt']), name_of(s['vt']))
        lines.append('%08X  %-8s %s%s' % (a, ins.mnemonic, ins.op_str, mark))
res['TOP_func'] = {'va': hex(TOP), 'n_sites': len(ctx), 'distinct_disp': len({s['disp'] for s in ctx}),
                   'span': [hex(span_lo), hex(span_hi)], 'lines': lines[:400],
                   'distinct_vt': len({s['vt'] for s in ctx}),
                   'vts': [[hex(v), name_of(v), sum(1 for s in ctx if s['vt'] == v)] for v in sorted({s['vt'] for s in ctx})]}
res['TOP_func_disp_min_max'] = [min(s['disp'] for s in ctx), max(s['disp'] for s in ctx)] if ctx else None

POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('严格口径大位移 278', sum(1 for s in large if s['strict']) == 278, sum(1 for s in large if s['strict']))
chk('large 组 disp==COL.offset 比例 < 0.2（复现 R144 的 0.1259）', res['D_large']['agree_frac'] < 0.2, res['D_large']['agree_frac'])
chk('small 组 disp==COL.offset 比例 > 0.95（正控）', res['D_small']['agree_frac'] > 0.95, res['D_small']['agree_frac'])
chk('large 组 COL.offset==0 占比 > 0.7（内嵌主对象）', res['D_large']['coloff_zero_frac'] > 0.7, res['D_large']['coloff_zero_frac'])
chk('top 函数内 large 站点 > 20（结构可一手取证）', res['TOP_func']['n_sites'] > 20, res['TOP_func']['n_sites'])
res['POS'] = POS; res['pos_fail'] = sum(1 for x in POS if not x[1])
res['elapsed_s'] = round(time.time() - T0, 1)
json.dump(res, open('/home/t628/projects/ra2-campaign-forge/_r146/r146d_coloff.json', 'w'), indent=1)
for x in POS: print(('PASS ' if x[1] else 'FAIL ') + x[0], x[2])
print('pos_fail', res['pos_fail'], 'elapsed', res['elapsed_s'])
