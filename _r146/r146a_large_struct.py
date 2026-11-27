#!/usr/bin/env python3
"""R146 A：278 站点「大位移组」到底是什么结构（R145 下轮待办 #3）。

背景（R144 实测，_r144/r144d_strat.json / r144i_global_perm.json）：
  disp≠0 装表站点 1,305；按位移分桶 small={4,8,12} 1,027 站点 / 一致率 0.9766、
  large=其余 278 站点 / 一致率 0.1259 / 零模型 0.0079 / lift 15.87。
  「已证不是 vptr，未证是什么」。R145 建议按「成员数组 / 结构体」两假说做可失败判据。

本脚本对 278 个 large 站点做**结构解剖**，四个可失败判据：
  H1 成员数组假说：同一 (base 寄存器) 在同一函数内出现多个大位移站点，且位移构成
     等差数列（步长 = 元素大小）。判据：存在某个 (函数, base) 组合，其大位移 ≥3 个
     且位移去重后相邻差恒定。
  H2 结构体内嵌子对象假说：同一 base 的大位移站点位移集合，其最大位移 + 4 与
     「该 base 的来源（该函数内对 base 的 lea/mov base,reg 的最近前置）」一致，
     或位移值命中 RTTI 反推的 mdisp 集合。判据：位移 ∈ CHD mdisp 集合的比例。
  H3 表体内存槽假说：大位移站点的 imm（虚表）在**同一函数内**被多次写（对象数组
     初始化），判据：同一 (函数, imm) 出现 ≥2 次的比例。
  H4 假阳性假说：大位移站点中的 imm 并不真的「装进对象首字段」，而是
     「把虚表地址当普通常量写进某个大结构」，判据：该位移处没有任何后续
     虚调用（call dword ptr [base+disp]）证据。

关键纪律：disasm_lite 64KB 流式，绝不对整段 .text 开 detail=True。
每个判据都配**反控**（同一个量在 small 桶上算一遍作对照）。
"""
import sys, re, json, struct, collections, hashlib, time, bisect
sys.path.insert(0, '_r143')
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r143')
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
def off_of(vt): return coloff.get(COLof.get(vt))
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

# ---------- 宽容内存操作数解析（R145 教训：必须吃 [reg - N] 与十进制/十六进制混排）----------
TOL = re.compile(r'^dword ptr \[(.+?)\](?:,(.+))?$')
def parse_mem(s):
    s = s.replace(' ', '')
    m = re.fullmatch(r'([a-z0-9]+)(?:([+-])(0x[0-9a-f]+|\d+))?', s)
    if not m: return None
    if m.group(3) is None: return m.group(1), 0
    v = int(m.group(3), 16) if m.group(3).startswith('0x') else int(m.group(3))
    return m.group(1), (-v if m.group(2) == '-' else v)

# ---------- 一次流式扫描：收集所有 dword 立即数写站点 + 函数边界 + 虚调用 ----------
sites = []          # (va, base, disp, imm)
vcalls = []         # (va, base, disp)  call/jmp dword ptr [base+disp]
funcstarts = []     # 函数起始 VA（用 call 目标 + 节内 ret 后位置近似）
calltgt = set()
allins = []         # 仅存需要的：mov reg,imm / lea reg,[...] 供 base 溯源
prev_lea = collections.defaultdict(list)   # 全局：base 寄存器 -> [(va, expr)]
FUNC_BREAK = set()
for a, sz, mn, op in B.sweep(md):
    if not op: continue
    mt = TOL.match(op)
    if mt:
        pm = parse_mem(mt.group(1))
        if pm:
            base, disp = pm
            tgt = (mt.group(2) or '').strip()
            # R144 口径：只收 imm ∈ VTS 的装表站点（上一版本漏了这个过滤，站点数虚高到 5,446）
            if mn == 'mov' and tgt and L.RE_IMM.match(tgt) and immv(tgt) in VTS:
                sites.append((a, base, disp, immv(tgt)))
            if mn in ('call', 'jmp') and mt.group(2) is None:
                vcalls.append((a, base, disp))
    if mn == 'call':
        m2 = re.match(r'^(0x[0-9a-f]+)$', op)
        if m2: calltgt.add(int(m2.group(1), 16))

# 函数边界：把 call 目标与「ret 之后的下一条」都当候选起点
calltgt_sorted = sorted(calltgt)
def func_of(va):
    """返回 <= va 的最近已知函数起始（call 目标集合）。"""
    i = bisect.bisect_right(calltgt_sorted, va) - 1
    return calltgt_sorted[i] if i >= 0 else None

bucket = lambda d: 'small' if d in (4, 8, 12) else 'large'
nz = [s for s in sites if s[2] != 0 and s[1] in GEN]
large = [s for s in nz if bucket(s[2]) == 'large']
small = [s for s in nz if bucket(s[2]) == 'small']

def r(ok, tot): return [ok, tot, round(ok / tot, 4) if tot else None]

res = {'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
       'sites_all': len(sites), 'sites_nonzero': len(nz), 'large': len(large), 'small': len(small),
       'vcalls_total': len(vcalls)}

# ---------- H1 成员数组：同 (函数, base) 的多站点位移等差 ----------
def h1(grp, tag):
    by = collections.defaultdict(list)
    for va, base, d, imm in grp:
        by[(func_of(va), base)].append((va, d, imm))
    multi = {k: v for k, v in by.items() if len({x[1] for x in v}) >= 3}
    arith = 0
    detail = []
    for k, v in multi.items():
        ds = sorted({x[1] for x in v})
        gaps = [ds[i + 1] - ds[i] for i in range(len(ds) - 1)]
        if len(set(gaps)) == 1:
            arith += 1
            if len(detail) < 8:
                detail.append([hex(k[0]) if k[0] else None, k[1], len(v), len(ds), ds[:8], gaps[0]])
    return {'groups_ge3_distinct_disp': len(multi), 'arithmetic_groups': arith,
            'arity_frac': round(arith / len(multi), 4) if multi else None,
            'samples': detail, 'by_key_n': len(by)}
h1l = h1(large, 'large'); h1s = h1(small, 'small')
res['H1'] = {'large': h1l, 'small': h1s}

# ---------- H2 位移是否命中 mdisp 集合 / 是否小整数倍数 ----------
def mdispset():
    """从 CHD（ClassHierarchyDescriptor）读全部基类 mdisp（子对象偏移）。

    口径照 _r145/r145f_chd.py：COL[0x10]=pClassDescriptor → p+8=numBaseClasses、
    p+0xC=pBaseClassArray；BCD 每项 [0]=pTD [4]=numContained [8]=PMD(mdisp,pdisp,vdisp)。
    不做任何阈值筛选，只按结构读。"""
    s = set()
    nbad = 0
    for col in COL:
        p = B.dw(col + 16)
        if not p or not B.sec_of(p): continue
        n, arr = B.dw(p + 8), B.dw(p + 12)
        if arr is None or not B.sec_of(arr) or not n or n > 64: nbad += 1; continue
        for i in range(n):
            bp = B.dw(arr + 4 * i)
            if not bp or not B.sec_of(bp): continue
            s.add(struct.unpack('<i', struct.pack('<I', B.dw(bp + 8)))[0])
    return s, nbad
MD, MD_BAD = mdispset()
res['mdisp_count'] = len(MD)
res['mdisp_bad_chd'] = MD_BAD
res['mdisp_sample'] = sorted(MD)[:20]
md_hit_l = sum(1 for s in large if s[2] in MD)
md_hit_s = sum(1 for s in small if s[2] in MD)
res['H2'] = {'large_in_mdisp': r(md_hit_l, len(large)), 'small_in_mdisp': r(md_hit_s, len(small)),
             'large_distinct_disp': len({s[2] for s in large}), 'small_distinct_disp': len({s[2] for s in small})}

# ---------- H3 同函数同 imm 重复写（对象数组/多实例初始化）----------
def h3(grp):
    by = collections.defaultdict(list)
    for va, base, d, imm in grp:
        by[(func_of(va), imm)].append(va)
    rep = sum(1 for v in by.values() if len(v) >= 2)
    byimm = collections.defaultdict(list)
    for va, base, d, imm in grp: byimm[imm].append(va)
    repimm = sum(1 for v in byimm.values() if len(v) >= 2)
    return {'pairs': len(by), 'pairs_ge2': rep, 'frac': round(rep / len(by), 4) if by else None,
            'distinct_imm': len(byimm), 'imm_ge2': repimm,
            'top_imm': [[hex(k), len(v)] for k, v in sorted(byimm.items(), key=lambda x: -len(x[1]))[:8]]}
res['H3'] = {'large': h3(large), 'small': h3(small)}

# ---------- H4 该位移处有无虚调用（call/jmp dword ptr [base+disp]）----------
vc_set = set((b, d) for _, b, d in vcalls)
h4_l = sum(1 for s in large if (s[1], s[2]) in vc_set)
h4_s = sum(1 for s in small if (s[1], s[2]) in vc_set)
res['H4'] = {'large_vcall_same_slot': r(h4_l, len(large)), 'small_vcall_same_slot': r(h4_s, len(small)),
             'vcall_distinct_slots': len(vc_set)}

# ---------- 附加：large 站点按位移的直方图（前 20）+ 按「imm==COL.offset 一致」拆 ----------
disp_hist = collections.Counter(s[2] for s in large).most_common(20)
res['large_disp_hist_top'] = [[d, n] for d, n in disp_hist]
res['large_agree'] = r(sum(1 for s in large if off_of(s[3]) == s[2]), len(large))
res['small_agree'] = r(sum(1 for s in small if off_of(s[3]) == s[2]), len(small))

# 正控：把 large 判据原样套到 small 上，结果必须不同（否则判据无判别力）
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('大位移站点数 278（复现 R144）', len(large) == 278, len(large))
chk('小位移站点数 1,027（复现 R144）', len(small) == 1027, len(small))
chk('大位移一致率 < 0.2（复现 R144）', (res['large_agree'][2] or 0) < 0.2, res['large_agree'])
chk('小位移一致率 > 0.95（正控）', (res['small_agree'][2] or 0) > 0.95, res['small_agree'])
chk('H4 大位移「同槽虚调用」比例低于小位移（判据有判别力）',
    (h4_l / len(large) if large else 0) < (h4_s / len(small) if small else 0), [h4_l, h4_s])
chk('mdisp 集合非空', len(MD) > 0, len(MD))
res['POS'] = POS; res['pos_fail'] = sum(1 for x in POS if not x[1])
res['elapsed_s'] = round(time.time() - T0, 1)
json.dump(res, open('/home/t628/projects/ra2-campaign-forge/_r146/r146a_large_struct.json', 'w'), indent=1)
for x in POS: print(('PASS ' if x[1] else 'FAIL ') + x[0], x[2])
print('pos_fail', res['pos_fail'], 'elapsed', res['elapsed_s'])
