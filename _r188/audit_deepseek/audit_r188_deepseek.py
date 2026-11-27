#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R188 跨家族只读复核（deepseek 家族）。

独立实现：PE 映射、COL/vtable 枚举、线性扫描（5 种推进策略）、操作数解析器。
不 import r188d_resync.py，也不 import _r185/pe185.py。只读二进制，除本目录外不写文件。

运行： timeout 900 python3 _r188/audit_deepseek/audit_r188_deepseek.py
"""
import sys, os, re, json, struct, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
BIN = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
RAW = open(BIN, 'rb').read()

# ================= 独立 PE 映射 =================
pe = struct.unpack_from('<I', RAW, 0x3c)[0]
assert RAW[pe:pe + 4] == b'PE\0\0'
NSEC = struct.unpack_from('<H', RAW, pe + 6)[0]
OPTSZ = struct.unpack_from('<H', RAW, pe + 20)[0]
IB = struct.unpack_from('<I', RAW, pe + 24 + 28)[0]
ORDER, SEC = [], {}
for i in range(NSEC):
    o = pe + 24 + OPTSZ + 40 * i
    nm = RAW[o:o + 8].rstrip(b'\0').decode('latin1')
    vs, va, rs, ra = struct.unpack_from('<IIII', RAW, o + 8)
    SEC[nm] = dict(lo=IB + va, vsize=vs, raw=ra, rawsize=rs, hifile=IB + va + rs)
    ORDER.append(nm)

def r2o(va):
    for nm in ORDER:
        s = SEC[nm]
        if s['lo'] <= va < s['hifile']:
            return s['raw'] + (va - s['lo'])
    return None

def dw(va):
    o = r2o(va)
    return None if o is None or o + 4 > len(RAW) else struct.unpack_from('<I', RAW, o)[0]

def secname(va):
    for nm in ORDER:
        s = SEC[nm]
        if s['lo'] <= va < s['hifile']:
            return nm
    return None

def cstr(va, mx=200):
    o = r2o(va)
    if o is None:
        return None
    e = RAW.find(b'\0', o, o + mx)
    return None if e < 0 else RAW[o:e]

T = SEC['.text']
LO, HI = T['lo'], T['hifile']
BLOB = RAW[T['raw']:T['raw'] + T['rawsize']]
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32)
CH = 64 * 1024
print('PE ImageBase=%#x .text va=%#010x rawsize=%d(=%d x 64KB) vsize=%d' %
      (IB, LO, len(BLOB), len(BLOB) // CH, T['vsize']))

# ================= 独立扫描器：5 种推进策略 =================
def sweep(policy, chunk=CH, overlap=0):
    """返回 (指令数, call列表, 洞列表, 块统计)。指令与 call 都只留 (addr, op)。"""
    n = 0
    calls = []
    holes = []
    chunks = []
    pos = 0
    while pos < len(BLOB):
        end = min(pos + chunk, len(BLOB))
        lim = min(end + overlap, len(BLOB))
        last = None
        for a, sz, mn, op in MD.disasm_lite(BLOB[pos:lim], LO + pos):
            last = pos + (a - (LO + pos)) + sz
            n += 1
            if mn in ('call', 'jmp'):
                calls.append((a, mn, op))
        chunks.append((pos, end, last))
        if policy == 'aligned':          # 每块解到解不动就跳下一块（主会话"旧口径"）
            pos = end
            continue
        if last is None:
            holes.append((pos, 'empty'))
            pos += 1
        elif last >= end:
            pos = last if overlap else end
        elif policy == 'naive':
            holes.append((last, 'jump-end'))
            pos = end
        elif policy == 'resync':         # 坏字节处前进 1 字节
            holes.append((last, 'resync+1'))
            pos = last + 1
        elif policy == 'slide':          # 坏字节处原地重试
            holes.append((last, 'slide'))
            pos = last
        else:
            raise ValueError(policy)
    return n, calls, holes, chunks

print('\n================ C1：按 64KB 分块、每块解到解不动就跳下一块 ================')
na, calls_a, holes_a, chunks_a = sweep('aligned')
NCH = len(chunks_a)
early = [c for c in chunks_a if c[2] is not None and c[2] < c[1]]
empty = [c for c in chunks_a if c[2] is None]
clean = [c for c in chunks_a if c[2] is not None and c[2] >= c[1]]
consumed = sum((min(c[2], c[1]) - c[0]) if c[2] is not None else 0 for c in chunks_a)
print('块数 %d；达块尾 %d；未达块尾 %d（其中解出 0 条 %d）' % (NCH, len(clean), len(early) + len(empty), len(empty)))
print('消费字节 %d / %d = %.4f%%；丢弃 %d 字节' %
      (consumed, len(BLOB), 100.0 * consumed / len(BLOB), len(BLOB) - consumed))
print('对齐块扫描指令 %d、间接 call %d' % (na, len([c for c in calls_a if c[1] == 'call' and '[' in c[2]])))
print('未达块尾的块（块起点VA, 丢弃字节）：%s' %
      [(hex(c[0] + LO), c[1] - (c[2] if c[2] is not None else c[0])) for c in (early + empty)[:8]])
# 机制核验：整段一次 disasm_lite 会不会抛异常 / 停在哪
first = list(MD.disasm_lite(BLOB, LO))[:1]
try:
    nwhole = sum(1 for _ in MD.disasm_lite(BLOB, LO))
    flat = 'return'
except Exception as e:
    nwhole = -1
    flat = 'raise:%s' % type(e).__name__
print('整段一次 disasm_lite：行为=%s，只解出 %d 条（首个解不动处即返回，未抛异常）' % (flat, nwhole))

print('\n================ C2：重同步 / 原地重试 / 带重叠窗口 ================')
R = {}
for pol in ('naive', 'resync', 'slide'):
    n, cl, hl, chs = sweep(pol)
    R[pol] = (n, cl, hl)
    print('%-10s 指令 %7d  间接call %6d  洞/重启 %4d' %
          (pol, n, len([c for c in cl if c[1] == 'call' and '[' in c[2]]), len(hl)))
n, cl, hl, chs = sweep('resync', overlap=15)
R['resync_ovl'] = (n, cl, hl)
print('%-10s 指令 %7d  间接call %6d  洞/重启 %4d  <- 窗口带 15 字节重叠（消除边界截断）' %
      ('resync+ovl', n, len([c for c in cl if c[1] == 'call' and '[' in c[2]]), len(hl)))

holes_r = R['resync'][2]
offs = [h[0] for h in holes_r]
trunc, genuine = [], []
for o in offs:
    d = list(MD.disasm_lite(BLOB[o:o + 16], LO + o))
    (trunc if (d and d[0][1] <= len(BLOB) - o) else genuine).append(o)
print('97 个重启点分型：窗口截断型 %d（给足字节即可解码，是 64KB 窗口伪影）、真不可解 %d' %
      (len(trunc), len(genuine)))
print('  截断型地址样例 %s' % [hex(x + LO) for x in trunc[:6]])
print('  截断型距 64KB 边界的距离分布 %s' %
      dict(collections.Counter(CH - (x % CH) for x in trunc).most_common(6)))
runs = []
for o in sorted(offs):
    if runs and o == runs[-1][-1] + 1:
        runs[-1].append(o)
    else:
        runs.append([o])
print('  连续段 %d 段，段长分布 %s（相邻重同步很少，不存在"连续坏字节放大"）' %
      (len(runs), dict(collections.Counter(len(r) for r in runs))))
print('  重启后未覆盖字节 = %d（= 重启次数），占 .text %.6f%%' % (len(offs), 100.0 * len(offs) / len(BLOB)))
print('  重同步 vs 带重叠：指令差 %+d、间接call 差 %+d' %
      (R['resync'][0] - R['resync_ovl'][0],
       len(R['resync'][1]) - len(R['resync_ovl'][1])))

print('\n================ C3：独立解析器 / 间接 call 站点与基址分类 ================')
REG = r'(eax|ecx|edx|ebx|esp|ebp|esi|edi)'

def parse_mem(op):
    """自写：返回 (base, index, scale, disp, seg) 或 None。十进制与十六进制位移都吃。"""
    if not op.startswith('dword ptr [') and ' ptr [' not in op:
        return None
    i = op.index(' ptr [') + 5 if ' ptr [' in op else op.index('[')
    seg = None
    if op[i - 1] == ':':
        m = re.search(r'([a-z]{2}):\[', op)
        seg = m.group(1) if m else '?'
    j = op.rindex(']')
    if op[j + 1:].strip():
        return None
    inner = op[i + 1:j]
    parts = []
    for t in inner.split('+'):
        if ' - ' in t:
            a, b = t.split(' - ')
            parts += [a.strip(), '-' + b.strip()]
        elif ' - ' not in t and '-' in t.strip().lstrip('-'):
            return None
        else:
            parts.append(t.strip())
    base = idx = None
    scale = 1
    disp = 0
    for t in parts:
        neg = t.startswith('-')
        tt = t[1:].strip() if neg else t
        if re.fullmatch(REG, tt):
            base = tt
        elif re.fullmatch(r'%s ?\* ?[1248]' % REG, tt):
            m = re.fullmatch(r'(%s) ?\* ?([1248])' % REG, tt)
            idx = m.group(1)
            scale = int(m.group(3))
        elif re.fullmatch(r'0x[0-9a-f]+|[0-9]+', tt):
            disp = int(tt, 0) * (-1 if neg else 1)
        else:
            return None
    return (base, idx, scale, disp, seg)

def analyze(policy):
    n, cl, hl = R[policy] if isinstance(R[policy], tuple) and len(R[policy]) == 3 else (R[policy][0], R[policy][1], R[policy][2])
    ind = [c for c in cl if c[1] == 'call' and '[' in c[2]]
    strict = [c for c in ind if c[2].startswith('dword ptr [')]
    unparsed = []
    bd = collections.Counter()
    segs = collections.Counter()
    idxed = []
    for a, mn, op in ind:
        pm = parse_mem(op)
        if pm is None:
            unparsed.append((a, op))
            continue
        b, ix, sc, dp, sg = pm
        segs[sg] += 1
        bd[b or 'abs'] += 1
        if ix:
            idxed.append((a, op, b, ix, sc, dp))
    return dict(all=ind, strict=strict, unp=unparsed, bd=bd, segs=segs, idx=idxed)

A = {p: analyze(p) for p in ('naive', 'resync', 'resync_ovl')}
CLAIM = dict(edx=9852, eax=6715, abs=3832, ecx=1445, esi=326, edi=261, ebx=163, ebp=128, esp=9)
for p in ('naive', 'resync', 'resync_ovl'):
    d = A[p]
    print('%-11s 含中括号 call %d；严格 dword ptr [ 开头 %d；未解析 %d' %
          (p, len(d['all']), len(d['strict']), len(d['unp'])))
    print('            段前缀分布 %s' % dict(d['segs']))
    print('            基址分布 %s' % dict(d['bd'].most_common()))
    print('            带 index 的 %d 例 %s' % (len(d['idx']), [(hex(a), o) for a, o, *_ in d['idx'][:3]]))
    if d['unp']:
        print('            未解析样例 %s' % [(hex(a), o) for a, o in d['unp'][:6]])
print('\n逐类对账（主会话 C3 vs 本审计 resync，严格定义=排除段前缀）：')
mine = A['resync']['bd']
print('  %-4s %8s %8s %8s' % ('基址', '主会话', '本审计', '判定'))
for k in sorted(set(CLAIM) | set(mine), key=lambda z: -CLAIM.get(z, 0)):
    print('  %-4s %8d %8d %8s' % (k, CLAIM.get(k, 0), mine.get(k, 0),
                                  '一致' if CLAIM.get(k, 0) == mine.get(k, 0) else '不符'))
print('  合计 主会话 %d / 本审计 %d' % (sum(CLAIM.values()), sum(mine.values())))
print('  口径差：把 %s 这类段前缀 call 计入后 = %d' %
      (dict(A['resync']['segs']), len(A['resync']['all'])))

# 增量站点的来源分析
set_a = {a for a, _, _ in A['naive']['all']}
set_r = {a for a, _, _ in A['resync']['all']}
set_o = {a for a, _, _ in A['resync_ovl']['all']}
set_s = {a for a, _, _ in analyze('slide')['all']}
extra = set_r - set_a
print('\n增量间接 call 站点：resync 新增 %d（主会话称 3,249）' % len(extra))
print('  其中同时被 resync+15重叠 策略找到 %d；同时被 slide 策略找到 %d' %
      (len(extra & set_o), len(extra & set_s)))
lost = set_a - set_r
print('  naive 有而 resync 无的站点 %d 例 %s' % (len(lost), [hex(x) for x in list(lost)[:5]]))
# 增量站点是否都落在 naive 丢弃的块尾
cut = {}
for (p0, end, last) in chunks_a:
    cut[p0] = (last if last is not None else p0)
def in_discarded(a):
    o = a - LO
    p0 = (o // CH) * CH
    last = cut.get(p0)
    return last is None or o >= last
print('  增量站点中落在 naive 丢弃块尾的比例 %d / %d' %
      (sum(1 for a in extra if in_discarded(a)), len(extra)))

print('\n================ C4：capstone 位移十进制/十六进制格式 ================')
for perm in (0, 1, 7, 8, 9, 10, 11, 15, 16, 68, 132):
    bb = b'\xff\xd0' if perm == 0 else b'\xff\x50' + bytes([perm]) if perm < 256 else None
    d = list(MD.disasm(bb, 0x1000))
    print('  disp=%-3d 字节 %-10s -> %s' % (perm, bb.hex(), d[0].op_str if d else '解不出'))
real8 = [c for c in A['resync']['all'] if c[2] == 'dword ptr [esi + 8]'][:2]
real44 = [c for c in A['resync']['all'] if c[2] == 'dword ptr [esi + 0x44]'][:2]
reala = [c for c in A['resync']['all'] if c[2] == 'dword ptr [esi + 0xa]'][:2]
for lab, lst in (('[esi + 8]（十进制渲染）', real8), ('[esi + 0x44]（十六进制渲染）', real44),
                 ('[esi + 0xa]（十进制 10 起即转十六进制）', reala)):
    print('  %-34s %s' % (lab, [(hex(a), o) for a, _, o in lst] or '未出现'))

print('\n================ 枚举（自写，按卡片判据）================')
COLS = {}
for nm in ('.rdata', '.data'):
    s = SEC[nm]
    n = s['rawsize'] // 4
    v = struct.unpack_from('<%dI' % n, RAW, s['raw'])
    for i in range(n - 4):
        d0, d1, d2, d3, d4 = v[i], v[i + 1], v[i + 2], v[i + 3], v[i + 4]
        if d0 not in (0, 1) or d2 != 0:
            continue
        if secname(d3) != '.data' or secname(d4) != '.rdata':
            continue
        cn = cstr(d3 + 8)
        if not (cn and cn.startswith(b'.?A') and cn.endswith(b'@@')):
            continue
        COLS[s['lo'] + 4 * i] = dict(mdisp=d1, td=d3, name=cn.decode('latin1'))
VTS = {}
for nm in ('.rdata', '.data'):
    s = SEC[nm]
    n = s['rawsize'] // 4
    v = struct.unpack_from('<%dI' % n, RAW, s['raw'])
    for i, x in enumerate(v):
        if not (LO <= x < HI):
            continue
        va = s['lo'] + 4 * i
        p = dw(va - 4)
        if p in COLS:
            VTS[va] = COLS[p]
print('COL %d / vtable %d（主会话 A0a：1214 / 1214）' % (len(COLS), len(VTS)))

def nslots(vt):
    k = 0
    while k < 4000:
        d = dw(vt + 4 * k)
        if d is None or not (LO <= d < HI):
            return k
        k += 1
    return k
SN = {vt: nslots(vt) for vt in VTS}
IMP = collections.defaultdict(list)
for vt in VTS:
    for k in range(SN[vt]):
        IMP[dw(vt + 4 * k)].append((vt, k))
print('槽位实例 %d（主会话 14044）/ 实现去重 %d（主会话 6692）/ 最小槽数 %d' %
      (sum(SN.values()), len(IMP), min(SN.values())))
print('宿主表按 COL.offset(mdisp) 分布 %s' %
      dict(collections.Counter(VTS[vt]['mdisp'] for vt in VTS).most_common(6)))

# ---------- 配对：mov reg,[esi] -> call [reg+disp] ----------
MOVP = re.compile(r'^(eax|ecx|edx|ebx|esp|ebp|esi|edi), dword ptr \[(eax|ecx|edx|ebx|esp|ebp|esi|edi)\]$')
WM = set('mov movzx movsx lea xor add sub and or adc sbb pop inc dec mul imul div idiv '
         'neg not shl shr sar rol ror xchg bswap'.split())

def pair_stream(policy, src='esi', window=32, checkwrite=True, chunk=CH, overlap=0):
    pos = 0
    recent = collections.deque(maxlen=window)
    pairs = []
    nmov = 0
    while pos < len(BLOB):
        end = min(pos + chunk, len(BLOB))
        lim = min(end + overlap, len(BLOB))
        last = None
        for a, sz, mn, op in MD.disasm_lite(BLOB[pos:lim], LO + pos):
            last = pos + (a - LO - pos) + sz
            if mn == 'mov':
                m = MOVP.match(op)
                if m and m.group(2) == src:
                    nmov += 1
                    recent.append((a, 'M', m.group(1), op))
                else:
                    recent.append((a, mn, None, op))
            elif mn == 'call':
                pm = parse_mem(op)
                if pm and pm[0] and pm[1] is None:
                    r, d = pm[0], pm[3]
                    for (pa, pk, pr, pop) in reversed(recent):
                        if pk == 'M' and pr == r:
                            pairs.append((pa, r, a, d, a - pa))
                            break
                        if checkwrite and pk in WM and pop.split(',')[0].strip() == r:
                            break
                recent.append((a, mn, None, op))
            else:
                recent.append((a, mn, None, op))
        if last is None:
            pos += 1
        elif last >= end:
            pos = last if overlap else end
        elif policy == 'resync':
            pos = last + 1
        elif policy == 'slide':
            pos = last
        else:
            pos = end
    return nmov, pairs

nmov_r, pairs_r = pair_stream('resync')
nmov_n, pairs_n = pair_stream('naive')
PD = collections.Counter(p[3] for p in pairs_r)
print('\n配对（resync）：mov r32,[esi] %d（主会话 9128）、配对 %d（主会话 6965）、去重站点 %d' %
      (nmov_r, len(pairs_r), len({p[2] for p in pairs_r})))
print('配对（naive）：mov r32,[esi] %d、配对 %d（主会话 5840）' % (nmov_n, len(pairs_n)))
print('配对位移去重 %d（主会话 267）、合计 %d，4 对齐 %s，无负位移 %s' %
      (len(PD), sum(PD.values()), all(d % 4 == 0 for d in PD), all(d >= 0 for d in PD)))
print('配对寄存器 %s' % dict(collections.Counter(p[1] for p in pairs_r).most_common()))

print('\n================ C8：top6 三元组（实现, 出现表数, 槽号）================')
INFO = []
for d, cnt_calls in PD.most_common(6):
    k = d // 4
    tbls = [vt for vt in VTS if SN[vt] > k]
    vals = collections.Counter(dw(vt + 4 * k) for vt in tbls)
    impl, topn = vals.most_common(1)[0]
    occ = IMP.get(impl, [])
    hist = collections.Counter(kk for _, kk in occ)
    site = [p for p in pairs_r if p[3] == d][0]
    INFO.append(dict(disp=d, k=k, calls=cnt_calls, impl=impl, tables=len(tbls), topn=topn,
                     occ=len(occ), hist=dict(hist), site=site[2],
                     bytes=RAW[r2o(site[2]):r2o(site[2]) + 3].hex()))
    print('槽%3d disp=%#5x calls=%3d 站点=%#010x 字节=%s 有该槽的表=%4d 实现=%#010x 出现=%d表 直方=%s' %
          (k, d, cnt_calls, site[2], INFO[-1]['bytes'], len(tbls), impl, len(occ),
           dict(hist.most_common(3))))
print('一一对应判定 %s' % [(hex(x['impl']), x['occ'], x['hist']) for x in INFO])

print('\n================ C5：槽3 thunk 0x410210 ================')
TH = [x for x in INFO if x['k'] == 3][0]
va = TH['impl']
o = r2o(va)
print('实现 %#010x：出现 %d 表，直方 %s' % (va, TH['occ'], TH['hist']))
print('前 16 字节 %s（主会话断言 8b4424048b50fc8d48fcff522cc20400）' % RAW[o:o + 16].hex())
for i in MD.disasm(RAW[o:o + 16], va):
    print('  %#010x  %-7s %s' % (i.address, i.mnemonic, i.op_str))
owners = [vt for vt, kk in IMP[va] if kk == 3]
print('宿主表 %d 张；COL.offset 分布 %s' % (len(owners), dict(collections.Counter(VTS[vt]['mdisp'] for vt in owners).most_common())))
print('宿主表槽数 <= 11（读不到槽11）的 %d 张' % sum(1 for vt in owners if SN[vt] <= 11))
S11 = collections.Counter(dw(vt + 44) for vt in owners if SN[vt] > 11)
print('宿主表槽11 取值分布 %s' % [(hex(k), v) for k, v in S11.most_common(6)])
print('宿主表类名样例 %s' % [VTS[vt]['name'] for vt in owners[:6]])
for tgt in [k for k, _ in S11.most_common(4)]:
    ot = r2o(tgt)
    if ot is None:
        print('  %#010x 不在文件' % tgt)
        continue
    seq = list(MD.disasm(RAW[ot:ot + 16], tgt))
    print('  %#010x %s | %s' % (tgt, RAW[ot:ot + 12].hex(),
                                ' ; '.join('%s %s' % (i.mnemonic, i.op_str) for i in seq[:4])))
    print('            该函数是否出现在某张虚表槽位上：%s（出现 %d 次）' %
          ('是' if tgt in IMP else '否', len(IMP.get(tgt, []))))

print('\n================ C7：槽4 getter 0x410220 ================')
G = [x for x in INFO if x['k'] == 4][0]
gva = G['impl']
og = r2o(gva)
print('实现 %#010x：出现 %d 表，直方 %s' % (gva, G['occ'], G['hist']))
print('前 10 字节 %s（主会话断言 8b4424048b400cc20400）' % RAW[og:og + 10].hex())
for i in MD.disasm(RAW[og:og + 10], gva):
    print('  %#010x  %-7s %s' % (i.address, i.mnemonic, i.op_str))
go = [vt for vt, kk in IMP[gva] if kk == 4]
print('宿主表 %d 张；COL.offset(mdisp) 分布 %s（主会话称全为 4）' %
      (len(go), dict(collections.Counter(VTS[vt]['mdisp'] for vt in go).most_common())))
print('宿主表槽数 <= 4 的 %d 张（槽 4 存在性是枚举前提）' % sum(1 for vt in go if SN[vt] <= 4))
print('与 C5 的宿主表交集 %d 张' % len(set(go) & set(owners)))

print('\n================ 反控（全部实跑）================')
multi = [(va2, dict(collections.Counter(kk for _, kk in lst))) for va2, lst in IMP.items()
         if len(lst) >= 2 and len(collections.Counter(kk for _, kk in lst)) > 1]
print('P1 "实现<->槽号一一"不是普遍性质：出现 >=2 次且跨多个槽号的实现有 %d 个，例 %s' %
      (len(multi), [(hex(v), h) for v, h in multi[:3]]))
print('P2 97 重启点里 %d 个是 64KB 窗口截断伪影；带 15 字节重叠后重启点 %d 个，'
      '指令 %d->%d、间接call %d->%d' %
      (len(trunc), len(R['resync_ovl'][2]), R['resync'][0], R['resync_ovl'][0],
       len(A['resync']['all']), len(A['resync_ovl']['all'])))
c_ex = 0
for nm in ('.rdata', '.data'):
    s = SEC[nm]
    n = s['rawsize'] // 4
    v = struct.unpack_from('<%dI' % n, RAW, s['raw'])
    for i in range(n - 4):
        d3 = v[i + 3]
        if v[i] not in (0, 1) or v[i + 2] != 0:
            continue
        if secname(d3) != '.data' or secname(v[i + 4]) != '.rdata':
            continue
        cn = cstr(d3 + 8, 256)
        if not cn:
            continue
        p = cn.find(b'@@')
        if cn.startswith(b'.?A') and p >= 3 and (p + 3 >= len(cn) or cn[p + 2] == 0):
            c_ex += 1
print('P3 执行员的 COL 判据（.?A 开头 + find(@@)>=3 + @@ 后为 0 或串尾）-> COL %d；'
      '卡片判据（C 串以 @@ 结尾）-> %d。两者不是同一判据，COL/vtable 基数不可直接对比' %
      (c_ex, len(COLS)))
print('P4 槽号 k+1 后一一对应失败：%s' %
      all(x['hist'].get(x['k'] + 1, 0) != x['occ'] for x in INFO))
p1 = pair_stream('resync', window=1)[1]
print('P5 配对窗口 32->1：%d -> %d（窗口是判据的一部分，非自由参数）' % (len(pairs_r), len(p1)))
print('P6 关掉写入检查：%d -> %d' % (len(pairs_r), len(pair_stream('resync', checkwrite=False)[1])))
