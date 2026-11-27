#!/usr/bin/env python3
"""R146 C：大位移组的决定性判据 —— **基址寄存器是从哪来的**。

r146b 已确立（全部可失败）：
  ① 严格口径 278 / 宽容口径 283（差 5，全为负位移，正是 R145 修的形态）；
  ② small 组 202/202 个多站点组位移为步长 4 的等差数列 = 多继承子对象；
  ③ large 组只有 7/15 组等差，步长 28/24 而非 4；
  ④ large 组 top imm 全是 coloff==0 的模板类（TypeList<>/VectorClass<>），
     却写在位移 40/152/332/424/3664… 处 —— 说明**不是**「该类的正规 vptr 安装」。
  ⑤ J2（同函数内另有正规安装）是**退化判据**（small 组同样 0），已弃用。

本脚本换一个不相交的维度：对每个站点回溯 base 寄存器的**最后定义点**，把来源分六类：
  IMM      mov reg, 0xADDR          ⇒ 写进**静态全局对象**的固定偏移
  LEA_STK  lea reg, [esp/ebp+X]     ⇒ 写进**栈上局部对象**
  LEA_GLB  lea reg, [0xADDR]        ⇒ 全局对象的地址
  LOAD     mov reg, [mem]           ⇒ 从内存取到的指针（堆对象 / 静态指针容器）
  REG      mov reg, reg2            ⇒ 寄存器搬运（来源未定，向上再退一层不追）
  POP/UNK  pop / 调用后未定义
判据：
  K1 若 large 组以 IMM/LEA_GLB 为主而 small 组以 LOAD/LEA_STK 为主 ⇒ 大位移 = **静态全局
     结构体内嵌成员的内联 vptr 写**（不是堆对象成员数组）。
  K2 统计 (函数, base) 组内 distinct imm 与 distinct disp：若同组多个**不同** vt 写在不同
     大位移 ⇒ 一个构造函数内联初始化多个内嵌成员（聚合式），不是数组同型。
  K3 回溯距离（定义点到使用点的字节跨度）：若 large 组距离远大于 small 组，
     说明基址不是就地取的 this，而是长寿命寄存器复用（结构体指针变量）。
反控：small 组同判据必须给出不同的分布（否则判据无判别力）。
纪律：disasm_lite 64KB 流式，无 detail=True。
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

def classify(mn, op):
    """返回 (目标寄存器, 来源类别)。只看会定义 GEN 的指令。"""
    if not op: return None
    head, _, rest = op.partition(',')
    head = head.strip()
    if head not in GEN: return None
    mn = mn
    rest = rest.strip()
    if mn == 'mov':
        if L.RE_IMM.match(rest): return head, 'IMM'
        m = re.fullmatch(r'dword ptr \[(.+?)\]', rest)
        if m:
            pm = parse_mem(m.group(1))
            if pm and pm[0] in ('esp', 'ebp'): return head, 'LOAD_STK'
            return head, 'LOAD'
        if rest in GEN: return head, 'REG'
        return head, 'MOV_OTHER'
    if mn == 'lea':
        m = re.fullmatch(r'\[(.+?)\]', rest)
        if m:
            e = m.group(1).replace(' ', '')
            if 'esp' in e or 'ebp' in e: return head, 'LEA_STK'
            if re.fullmatch(r'0x[0-9a-f]+', e) or L.RE_IMM.match(e): return head, 'LEA_GLB'
            return head, 'LEA_OTHER'
        return head, 'LEA_OTHER'
    if mn == 'pop': return head, 'POP'
    if mn in ('xor', 'and', 'sub', 'or', 'xor_') and rest == head: return head, 'ZERO'
    if mn in ('add', 'sub', 'inc', 'dec', 'shl', 'shr', 'sar', 'and', 'or', 'xor', 'imul'):
        return head, 'ARITH'
    return head, 'OTHER'

CLOBBER = ('eax', 'ecx', 'edx')
sites = []
lastdef = {}          # reg -> (va, kind, op)
calltgt = set()
for a, sz, mn, op in B.sweep(md):
    if mn == 'call':
        m2 = re.match(r'^(0x[0-9a-f]+)$', op or '')
        if m2: calltgt.add(int(m2.group(1), 16))
        for rr in CLOBBER: lastdef[rr] = (a, 'CLOBBER', 'call')
    mt = TOL.match(op or '')
    if mt and mn == 'mov':
        pm = parse_mem(mt.group(1))
        if pm:
            base, disp = pm
            tgt = (mt.group(2) or '').strip()
            if L.RE_IMM.match(tgt) and immv(tgt) in VTS and base in GEN:
                d = lastdef.get(base)
                sites.append({'va': a, 'base': base, 'disp': disp, 'vt': immv(tgt),
                              'strict': L.RE_STORE.match(op) is not None,
                              'ori_kind': d[1] if d else 'NONE',
                              'ori_va': d[0] if d else None,
                              'ori_op': d[2] if d else None})
    c = classify(mn, op or '')
    if c: lastdef[c[0]] = (a, c[1], op)

ct = sorted(calltgt)
def func_of(va):
    i = bisect.bisect_right(ct, va) - 1
    return ct[i] if i >= 0 else None

bucket = lambda d: 'small' if d in (4, 8, 12) else 'large'
nz = [s for s in sites if s['disp'] != 0]
large = [s for s in nz if bucket(s['disp']) == 'large']
small = [s for s in nz if bucket(s['disp']) == 'small']

def dist(s):
    return (s['va'] - s['ori_va']) if s['ori_va'] is not None else None

res = {'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
       'sites': len(sites), 'nz': len(nz), 'large': len(large), 'small': len(small)}

def profile(grp, tag):
    kinds = collections.Counter(s['ori_kind'] for s in grp)
    ds = [dist(s) for s in grp if dist(s) is not None]
    ds.sort()
    return {'n': len(grp), 'kinds': kinds.most_common(),
            'kind_frac': {k: round(v / len(grp), 4) for k, v in kinds.items()} if grp else {},
            'dist_median': ds[len(ds) // 2] if ds else None,
            'dist_p90': ds[int(len(ds) * 0.9)] if ds else None,
            'dist_max': ds[-1] if ds else None}
res['K1_large'] = profile(large, 'large')
res['K1_small'] = profile(small, 'small')
res['K1_by_disp_top'] = [[hex(s['va']), s['base'], s['disp'], s['ori_kind'], hex(s['ori_va']) if s['ori_va'] else None, s['ori_op'], name_of(s['vt'])]
                          for s in sorted(large, key=lambda x: x['disp'])[:14]]

# ---- K2 同 (函数,base) 组内 distinct imm / distinct disp ----
def k2(grp):
    by = collections.defaultdict(list)
    for s in grp: by[(func_of(s['va']), s['base'])].append(s)
    multi_imm = 0; multi_disp = 0; cnt = 0
    samples = []
    for k, v in by.items():
        if len(v) < 2: continue
        cnt += 1
        di, dd = {x['vt'] for x in v}, {x['disp'] for x in v}
        if len(di) >= 2: multi_imm += 1
        if len(dd) >= 2: multi_disp += 1
        if len(samples) < 8 and len(di) >= 2:
            samples.append([hex(k[0]) if k[0] else None, k[1], len(v), len(di), len(dd),
                            sorted(dd)[:6], [name_of(x) for x in sorted(di)][:4]])
    return {'groups_ge2': cnt, 'with_multi_imm': multi_imm, 'with_multi_disp': multi_disp, 'samples': samples}
res['K2_large'] = k2(large); res['K2_small'] = k2(small)

# ---- small 组的 IMM/LEA_GLB 站点挑出来看（反控：若也有，说明判据不唯一）----
res['small_imm_like'] = [[hex(s['va']), s['base'], s['disp'], s['ori_kind'], s['ori_op'], name_of(s['vt'])]
                         for s in small if s['ori_kind'] in ('IMM', 'LEA_GLB')][:10]
res['small_imm_like_n'] = sum(1 for s in small if s['ori_kind'] in ('IMM', 'LEA_GLB'))
res['large_imm_like_n'] = sum(1 for s in large if s['ori_kind'] in ('IMM', 'LEA_GLB'))

POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('严格口径大位移站点 = 278（复现 R144）', sum(1 for s in large if s['strict']) == 278, sum(1 for s in large if s['strict']))
chk('large 组 IMM/LEA_GLB 比例 > small 组（判据有判别力）',
    res['large_imm_like_n'] / len(large) > res['small_imm_like_n'] / len(small),
    [res['large_imm_like_n'], res['small_imm_like_n']])
chk('large 组回溯距离中位数 > small 组（基址是长寿命指针变量）',
    (res['K1_large']['dist_median'] or 0) > (res['K1_small']['dist_median'] or 0),
    [res['K1_large']['dist_median'], res['K1_small']['dist_median']])
chk('没有任何类别占 large 组 100%（结论不靠单一类别）', not any(v == len(large) for v in dict(res['K1_large']['kinds']).values()), res['K1_large']['kinds'])
res['POS'] = POS; res['pos_fail'] = sum(1 for x in POS if not x[1])
res['elapsed_s'] = round(time.time() - T0, 1)
json.dump(res, open('/home/t628/projects/ra2-campaign-forge/_r146/r146c_origin.json', 'w'), indent=1)
for x in POS: print(('PASS ' if x[1] else 'FAIL ') + x[0], x[2])
print('pos_fail', res['pos_fail'], 'elapsed', res['elapsed_s'])
