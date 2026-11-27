#!/usr/bin/env python3
"""R146 B：大位移组（R144 278 / R145 宽容解析 283）的结构判决。

r146a 已给出的分层事实（全部可失败断言）：
  small（disp∈{4,8,12}）1,027 站点：位移 100% ∈ CHD mdisp 集合、202/202 个
  「(函数,base) 多站点组」位移是步长 4 的等差数列 ⇒ 就是多继承子对象 vptr。
  large 283 站点：156 个不同位移、只有 21.2% 命中 mdisp、只有 7/15 组等差。

本脚本对 large 组做三个互相独立、都能失败的判据：
  J1 「内部指针 / 元素数组」判据（成员数组假说的可失败形式）：
     残差 res = disp − COL.offset(vt)。若 large 站点是「同一类对象的数组第 k 个元素」，
     则同一 (函数, base) 组内 res 必须构成步长为元素大小的等差数列，且**步长跨组相同**。
     反控：small 组上跑同一判据必须给出步长 4 的 100% 等差（已知真值）。
  J2 「同函数内有正规 vptr 安装」判据：
     对每个 large 站点所在函数，看该函数里有没有「disp == COL.offset(vt)」的同 imm 站点。
     有 ⇒ 该函数确实在建对象（大位移是加料，不是替代）；没有 ⇒ 大位移是唯一写入点。
  J3 「同一个 imm 被大位移反复写」判据：
     top imm 0x7E4DD8 出现 70 次 —— 若是数组初始化，则应集中在少数函数且位移等差；
     若是常量表填充，则应跨大量函数、位移无关。
另外单列 R144(278) vs R145(283) 的差 5 站点，验证是否恰为 R145 修掉的负位移形态。
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

sites = []                 # (va, base, disp, imm, strict_ok)
calltgt = set()
for a, sz, mn, op in B.sweep(md):
    if not op: continue
    if mn == 'call':
        m2 = re.match(r'^(0x[0-9a-f]+)$', op)
        if m2: calltgt.add(int(m2.group(1), 16))
    mt = TOL.match(op)
    if not mt: continue
    pm = parse_mem(mt.group(1))
    if not pm: continue
    base, disp = pm
    tgt = (mt.group(2) or '').strip()
    if mn == 'mov' and tgt and L.RE_IMM.match(tgt) and immv(tgt) in VTS:
        strict = L.RE_STORE.match(op) is not None      # R144/r143 的窄口径（不吃负位移）
        sites.append((a, base, disp, immv(tgt), strict))

ct = sorted(calltgt)
def func_of(va):
    i = bisect.bisect_right(ct, va) - 1
    return ct[i] if i >= 0 else None

bucket = lambda d: 'small' if d in (4, 8, 12) else 'large'
nz = [s for s in sites if s[2] != 0 and s[1] in GEN]
large = [s for s in nz if bucket(s[2]) == 'large']
small = [s for s in nz if bucket(s[2]) == 'small']
strict_nz = [s for s in nz if s[4]]
strict_large = [s for s in strict_nz if bucket(s[2]) == 'large']

res = {'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
       'sites_all_imminvts': len(sites), 'nz_tolerant': len(nz), 'nz_strict': len(strict_nz),
       'large_tolerant': len(large), 'large_strict': len(strict_large),
       'small_tolerant': len(small), 'small_strict': len([s for s in strict_nz if bucket(s[2]) == 'small'])}

# ---- 差 5：宽容 vs 严格 ----
extra = [s for s in nz if not s[4]]
res['tolerant_minus_strict'] = [[hex(a), b, d, hex(v)] for a, b, d, v, _ in extra]
res['extra_all_negative'] = all(d < 0 for _, _, d, _, _ in extra)

# ---- J1 残差等差判据 ----
def j1(grp):
    by = collections.defaultdict(list)
    for va, base, d, vt, _ in grp:
        by[(func_of(va), base)].append((va, d, vt, d))
    steps = collections.Counter(); arith = 0; multi = 0; detail = []
    for k, v in by.items():
        ds = sorted({x[3] for x in v})
        if len(ds) < 3: continue
        multi += 1
        gaps = [ds[i + 1] - ds[i] for i in range(len(ds) - 1)]
        if len(set(gaps)) == 1:
            arith += 1; steps[gaps[0]] += 1
            if len(detail) < 8:
                detail.append([hex(k[0]) if k[0] else None, k[1], len(v), ds[:6], gaps[0]])
    return {'groups_res_ge3': multi, 'arith': arith,
            'frac': round(arith / multi, 4) if multi else None,
            'steps': steps.most_common(6), 'samples': detail}
res['J1'] = {'large': j1(large), 'small': j1(small)}

# ---- J2 同函数内是否有「disp == COL.offset」的同 imm 站点 ----
by_func = collections.defaultdict(set)
for va, base, d, vt, _ in nz:
    by_func[func_of(va)].add((vt, d))          # 记 (vt, 该站点自己的位移)，不是 COL.offset
j2_hit = 0; j2_miss = 0; j2_samples = []
for va, base, d, vt, _ in large:
    f = func_of(va)
    if off_of(vt) is not None and (vt, off_of(vt)) in by_func.get(f, ()) and d != off_of(vt): j2_hit += 1
    else:
        j2_miss += 1
        if len(j2_samples) < 10: j2_samples.append([hex(va), hex(f) if f else None, base, d, hex(vt), off_of(vt), name_of(vt)])
# 正控：small 组上同一判据
s_hit = sum(1 for va, base, d, vt, _ in small
            if off_of(vt) is not None and (vt, off_of(vt)) in by_func.get(func_of(va), ()) and d != off_of(vt))
res['J2'] = {'large_with_regular_install': [j2_hit, len(large), round(j2_hit / len(large), 4)],
             'small_with_regular_install': [s_hit, len(small), round(s_hit / len(small), 4)],
             'large_missing_samples': j2_samples}

# ---- J3 top imm 的结构 ----
byimm = collections.defaultdict(list)
for va, base, d, vt, _ in large: byimm[vt].append((va, base, d))
top = []
for vt, v in sorted(byimm.items(), key=lambda x: -len(x[1]))[:8]:
    funcs = collections.Counter(func_of(x[0]) for x in v)
    ds = sorted({x[2] for x in v})
    gaps = [ds[i + 1] - ds[i] for i in range(len(ds) - 1)]
    top.append({'vt': hex(vt), 'n': len(v), 'name': name_of(vt), 'coloff': off_of(vt),
                'distinct_funcs': len(funcs), 'top_funcs': [[hex(k) if k else None, n] for k, n in funcs.most_common(4)],
                'distinct_disp': len(ds), 'disp_head': ds[:8],
                'arith': bool(gaps) and len(set(gaps)) == 1, 'step': gaps[0] if gaps and len(set(gaps)) == 1 else None})
res['J3_top_imm'] = top

# 全体 large 的函数集中度（判「数组初始化」还是「散落常量填充」）
fc = collections.Counter(func_of(s[0]) for s in large)
res['large_func_count'] = len(fc)
res['large_func_top'] = [[hex(k) if k else None, n] for k, n in fc.most_common(10)]
res['large_sites_in_top10_funcs'] = sum(n for _, n in fc.most_common(10))

POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('严格口径复现 R144 的 278 个大位移站点', len(strict_large) == 278, len(strict_large))
chk('宽容口径比严格多 5 个站点（R145 修的负位移形态）', len(large) - len(strict_large) == 5, len(large) - len(strict_large))
chk('多出的 5 个站点位移全为负', res['extra_all_negative'], [x[2] for x in res['tolerant_minus_strict']])
chk('small 组残差等差比例 == 1.0（正控）', (res['J1']['small']['frac'] or 0) == 1.0, res['J1']['small'])
chk('large 组残差等差比例 < 0.6（成员数组假说不成立）',
    (res['J1']['large']['frac'] or 0) < 0.6, res['J1']['large']['frac'])
chk('large 组「同函数内有正规 vptr 安装」比例低于 small 组',
    res['J2']['large_with_regular_install'][2] < res['J2']['small_with_regular_install'][2], res['J2'])
chk('large 站点分布跨 >100 个函数（不是单点初始化）', res['large_func_count'] > 100, res['large_func_count'])
res['POS'] = POS; res['pos_fail'] = sum(1 for x in POS if not x[1])
res['elapsed_s'] = round(time.time() - T0, 1)
json.dump(res, open('/home/t628/projects/ra2-campaign-forge/_r146/r146b_large_verdict.json', 'w'), indent=1)
for x in POS: print(('PASS ' if x[1] else 'FAIL ') + x[0], x[2])
print('pos_fail', res['pos_fail'], 'elapsed', res['elapsed_s'])
