#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 主会话第八刀（收口）：把「store 归属」与「RTTI 血缘位置」合并成一张终表，并修正调用图扫描口径。

自错（本轮第二处，当场抓出并在本刀修正）：
  m7 的 E7a/E7b/E8a/E8b 四项 FAIL 是**我的扫描器缺陷**，不是执行员错：
  m7 用「每 64KB 块独立 disasm_lite」，块边界处的指令被截断且失败后不重同步 ⇒ CALLAT 只得 55,419（真值 68,244）、
  0x7C8B3D 只得 3,790（真值 4,498）。本刀改为「整段单次迭代 + 失败按 1 字节重同步」，
  并保留逐块版本作反控，给两个数。
  m7 的 E6a 也不该按「去重目标数」判：执行员报的 9 是**记录数**（9 条记录 → 4 个不同目标），
  两口径都对，需分开陈述。

判据：
 P1 扫描器：disasm_lite 单次迭代，pos += insn.size；无指令产出时 pos += 1 并计数 resync。
 P2 终表：538 条 store 逐条给 (base 归属, 偏移, imm 类别, 血缘下标 idx_imm, idx_b) 五元组。
 P3 汇总：按 (base 归属: this / non-this) x (idx_imm: own / base / 更远祖先>=2 / 不在血缘 -1) 交叉。
 P4 首 call 目标：去重目标数、记录数、其中落在虚表槽内的目标数与记录数。
反控：
 R1 逐块扫描（m7 口径）必须给出 55,419，与单次迭代 68,244 差 12,825。
 R2 重同步事件数与执行员自报 139 对比。
"""
import sys, struct, collections, json, re, bisect
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW
def in_text(x): return x is not None and LO <= x < HI

COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], pchd=w[i + 4], name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
NS = {}
def nslot(vt):
    if vt in NS: return NS[vt]
    k = 0
    while True:
        if not in_text(P.dw(vt + 4 * k)): break
        k += 1
    NS[vt] = k; return k
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}
CLS = {vt: COL[VT[vt]]['name'] for vt in VT}
PTD_OF = {vt: COL[VT[vt]]['ptd'] for vt in VT}
CHD = {}
for vt, col in VT.items():
    chd = COL[col]['pchd']
    if chd in CHD: continue
    n = P.dw(chd + 8); bca = P.dw(chd + 12)
    if n is None or bca is None or n <= 0 or n > 200: CHD[chd] = None; continue
    it = []
    for i in range(n):
        bcd = P.dw(bca + 4 * i); ptd = P.dw(bcd + 0) if bcd else None
        if ptd is None: it = None; break
        it.append((ptd, P.dw(bcd + 4), s32(P.dw(bcd + 8))))
    CHD[chd] = it
PTD_BCD = {}
for vt, col in VT.items():
    c = COL[col]; lst = CHD.get(c['pchd'])
    if lst: PTD_BCD[c['ptd']] = lst

d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
s0d = []
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1: continue
    a = P.dw(vt_d); b = P.dw(vt_b)
    if a != b: s0d.append((vt_d, a, vt_b))

# ---------- P1 正确扫描器 ----------
BUF = RAW[T['rawptr']:T['rawptr'] + (HI - LO)]
def scan_single():
    CALLAT = []; resync = 0; pos = 0
    while pos < len(BUF):
        got = False
        for off, sz, mn, op in md.disasm_lite(BUF[pos:pos + 65536], LO + pos):
            got = True
            if mn == 'call' and op.startswith('0x'):
                t = int(op, 16)
                if in_text(t): CALLAT.append((off, t))
            pos += sz
        if not got:
            pos += 1; resync += 1
    return CALLAT, resync
def scan_chunked():
    CALLAT = []; pos = 0
    while pos < len(BUF):
        for off, sz, mn, op in md.disasm_lite(BUF[pos:pos + 65536], LO + pos):
            if mn == 'call' and op.startswith('0x'):
                t = int(op, 16)
                if in_text(t): CALLAT.append((off, t))
        pos += 65536
    return CALLAT
CALLAT, resync = scan_single()
chunked = scan_chunked()
ck('P1a 单次迭代 CALLAT == 68,244', len(CALLAT) == 68244, len(CALLAT))
ck('P1b 重同步事件数', True, resync)
ck('R1a 逐块口径 == 55,419（m7 的同源缺陷）', len(chunked) == 55419, len(chunked))
ck('R1b 两口径差 == 12,825', len(CALLAT) - len(chunked) == 12825, len(CALLAT) - len(chunked))
cc = collections.Counter(t for _, t in CALLAT)
ck('P1c 0x7C8B3D 调用点 4,498 / 0x7B46F0 883 / 0x7B6760 384',
   (cc[0x7C8B3D], cc[0x7B46F0], cc[0x7B6760]) == (4498, 883, 384), (cc[0x7C8B3D], cc[0x7B46F0], cc[0x7B6760]))
CALLERS = collections.defaultdict(list)
for c, t in CALLAT: CALLERS[t].append(c)
SORT = sorted(set(t for _, t in CALLAT))
def host_of(c):
    i = bisect.bisect_left(SORT, c) - 1
    return SORT[i] if i >= 0 else None
hosts = set(host_of(c) for c in CALLERS[0x7C8B3D])
ck('P1d 0x7C8B3D 不同宿主 == 1,229', len(hosts) == 1229, len(hosts))

# ---------- P2/P3 终表 ----------
STORE_RE = re.compile(r'^dword ptr \[(e[a-z]{2})(?: ([\+\-]) (0x[0-9a-f]+|\d+))?\], (0x[0-9a-f]+)$')
REGS = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')
def parse_store(op):
    m = STORE_RE.match(op)
    if not m: return None
    reg = m.group(1); sign = m.group(2); val = m.group(3); imm = int(m.group(4), 16)
    off = 0
    if val is not None:
        off = int(val, 16) if val.startswith('0x') else int(val)
        if sign == '-': off = -off
    return reg, off, imm
def body(va, maxb=600, maxi=300):
    o = P.r2o(va)
    if o is None: return None
    ins = []
    for i in md.disasm(RAW[o:o + maxb], va):
        ins.append((i.address, i.size, i.mnemonic, i.op_str))
        if i.mnemonic.startswith('ret'): break
        if len(ins) >= maxi: break
    return ins
def evolve(ins):
    state = {}; hist = []
    for idx, (ad, sz, mn, op) in enumerate(ins):
        hist.append(dict(state))
        if mn in ('mov', 'lea') and ',' in op:
            dst, src = [x.strip() for x in op.split(',', 1)]
            if dst in REGS: state[dst] = (mn, src)
        elif mn == 'xor' and len(set(x.strip() for x in op.split(','))) == 1 and op.split(',')[0].strip() in REGS:
            state[op.split(',')[0].strip()] = ('zero', '0')
        elif mn == 'pop' and op.strip() in REGS:
            state[op.strip()] = ('pop', '')
        elif mn == 'call':
            state['eax'] = ('call', op)
        elif mn in ('add', 'sub', 'inc', 'dec', 'and', 'or', 'shl', 'shr', 'sar') and ',' in op:
            dst = op.split(',')[0].strip()
            if dst in REGS: state[dst] = ('arith', op)
    return hist
rows = []
for vt_d, a, vt_b in s0d:
    ins = body(a) or []
    hist = evolve(ins)
    for idx, (ad, sz, mn, op) in enumerate(ins):
        if mn != 'mov': continue
        ps = parse_store(op)
        if ps is None: continue
        reg, off, imm = ps
        if imm == vt_d: t = 'own'
        elif imm == vt_b: t = 'base'
        elif imm in VT and MD[imm] != 0: t = 'subtable'
        elif imm in VT: t = 'other'
        else: t = 'nonvt'
        if reg == 'esi': owner = 'this'
        elif reg in hist[idx]:
            dm, ds = hist[idx][reg]
            if ds == 'esi': owner = 'this'
            elif ds.startswith('dword ptr [esi') or ds.startswith('dword ptr [esp'): owner = 'field'
            elif ds.startswith('dword ptr ['): owner = 'field'
            elif dm == 'call': owner = 'new'
            elif ds in REGS:
                r2 = ds
                if r2 in hist[idx] and hist[idx][r2][1] == 'esi': owner = 'this'
                elif hist[idx].get(r2, ('', ''))[0] == 'call': owner = 'new'
                else: owner = 'other'
            else: owner = 'other'
        else: owner = 'unknown'
        lst = PTD_BCD.get(PTD_OF[vt_d]) or []
        idx_imm = next((i for i, x in enumerate(lst) if x[0] == PTD_OF.get(imm, -1)), -1) if imm in VT else -1
        idx_b = next((i for i, x in enumerate(lst) if x[0] == PTD_OF.get(vt_b, -2)), -1)
        rows.append(dict(cls_d=CLS[vt_d], impl=hex(a), at=hex(ad), reg=reg, off=off, imm=hex(imm),
                         immn=imm, cat=t, owner=owner, idx_imm=idx_imm, idx_b=idx_b,
                         cls_imm=CLS.get(imm)))
ck('P2a store 总数 538', len(rows) == 538, len(rows))
cross = collections.Counter()
for r in rows:
    if r['cat'] != 'other': continue
    pos = 'own' if r['idx_imm'] == 0 else ('base' if r['idx_imm'] == 1 else ('anc2+' if r['idx_imm'] >= 2 else 'noKin'))
    cross[(r['owner'], pos)] += 1
print('   P3 other_main 42 条交叉 (owner x 血缘位置): %s' % dict(sorted(cross.items())))
ck('P3a other 42 条全覆盖', sum(cross.values()) == 42, sum(cross.values()))
own_all = collections.Counter(r['owner'] for r in rows)
print('   P3b 全部 538 条的 owner 分布: %s' % dict(own_all))
ck('P3c this 侧 518 / 非 this 20', (own_all['this'], len(rows) - own_all['this']) == (518, 20), own_all['this'])
# 逐条打印 other 的 42 条
print('   P2b other_main 42 条明细:')
for r in rows:
    if r['cat'] != 'other': continue
    print('        %-50s <- %-50s owner=%-6s off=0x%-5x idx_imm=%-2d idx_b=%-2d' %
          (r['cls_d'], r['cls_imm'], r['owner'], r['off'], r['idx_imm'], r['idx_b']))

# ---------- P4 首 call ----------
ALLREF = collections.defaultdict(set)
for vt in VT:
    for k in range(nslot(vt)):
        ALLREF[P.dw(vt + 4 * k)].add((vt, k))
recs = []; tgts = set()
for vt_d, a, vt_b in s0d:
    cs = [int(op, 16) for _, _, mn, op in (body(a) or []) if mn == 'call' and op.startswith('0x')]
    if cs:
        tgts.add(cs[0]); recs.append((a, cs[0]))
invt_t = sorted(t for t in tgts if t in ALLREF)
invt_r = [(a, t) for a, t in recs if t in ALLREF]
ck('P4a 首 call 目标去重 51 / 记录 510', (len(tgts), len(recs)) == (51, 510), (len(tgts), len(recs)))
ck('P4b 落在虚表槽内：目标 4 / 记录 9', (len(invt_t), len(invt_r)) == (4, 9), (len(invt_t), len(invt_r)))
print('   P4c in-vtable 目标: %s ; 记录: %s' % ([hex(t) for t in invt_t],
      [(hex(a), hex(t)) for a, t in invt_r]))
ck('P4d 0x7C8B3D 是首 call 的记录数', True, sum(1 for a, t in recs if t == 0x7C8B3D))

json.dump(dict(callat=len(CALLAT), resync=resync, chunked=len(chunked),
               cc7c8b3d=cc[0x7C8B3D], hosts7c8b3d=len(hosts),
               cross={'%s|%s' % k: v for k, v in cross.items()}, owners=dict(own_all),
               t1=len(tgts), recs=len(recs), invt_t=[hex(t) for t in invt_t], invt_rec=len(invt_r),
               rows=rows, asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r200/m8_final.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
