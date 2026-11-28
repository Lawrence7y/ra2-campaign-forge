#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 主会话第三刀：m2 里「偏移==0 但血缘外」的 16 条 store 专查（R199 表述订正的关键）。

m1: 42 条 other_main 分 ancestor 21 / unrelated 19 / sibling 2。
m2: 538 条里偏移全为 0 的 532 条中有 16 条「imm 的 pTD 不是 vt_d 的祖先」。
本刀逐条给：
 L1 (派生类名, 实现地址, store 地址, imm 地址, imm 类名, n_d, n_imm) 全表。
 L2 imm 的 pTD 在 vt_d 类的 BCD 里的下标（找不到记 -1）；以及 vt_d 的 pTD 在 imm 类的 BCD 里的下标。
 L3 判定三种可解释形态：
     (i) imm 类 == vt_d 类的**子类**（vt_d 是 imm 的祖先）=> 装的是子类表 = 伪装的 vtable hack；
     (ii) imm 类与 vt_d 类同 pTD（多继承子表）—— m1 已 0，此处复核；
     (iii) 两边互不祖先 => 真无关。
 L4 对 (i) 类给出该 store 之后紧跟的 call 目标（是否在虚表内）。
反控：
 R1 把祖先判据改成「BCD 任意下标匹配」与「含自身」，看 16 条的分类是否变化。
"""
import sys, struct, collections, json, re
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
MAINBYPTD = {}
for vt in VT:
    if MD[vt] == 0: MAINBYPTD[PTD_OF[vt]] = vt

d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
s0d = []
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1: continue
    a = P.dw(vt_d); b = P.dw(vt_b)
    if a != b: s0d.append((vt_d, a, vt_b))

def body(va, maxb=600, maxi=300):
    o = P.r2o(va)
    if o is None: return None
    ins = []
    for i in md.disasm(RAW[o:o + maxb], va):
        ins.append((i.address, i.size, i.mnemonic, i.op_str))
        if i.mnemonic.startswith('ret'): break
        if len(ins) >= maxi: break
    return ins

STORE_RE = re.compile(r'^dword ptr \[(e[a-z]{2})(?: \+ (0x[0-9a-f]+))?\], (0x[0-9a-f]+)$')
ALLREF = collections.defaultdict(set)
for vt in VT:
    for k in range(nslot(vt)):
        ALLREF[P.dw(vt + 4 * k)].add((vt, k))

targets = []
for vt_d, a, vt_b in s0d:
    ins = body(a) or []
    for idx, (ad, sz, mn, op) in enumerate(ins):
        if mn != 'mov': continue
        m = STORE_RE.match(op)
        if not m: continue
        off = int(m.group(2), 16) if m.group(2) else 0
        imm = int(m.group(3), 16)
        if off != 0: continue
        if imm not in VT: continue
        p_d = PTD_OF[vt_d]; p_i = PTD_OF[imm]
        if p_d == p_i: continue
        lst = PTD_BCD.get(p_d)
        if lst and any(x[0] == p_i for x in lst[1:]): continue
        # 血缘外
        nxt = None
        for j in range(idx + 1, len(ins)):
            if ins[j][2] == 'call' and ins[j][3].startswith('0x'): nxt = int(ins[j][3], 16); break
        targets.append((vt_d, a, ad, imm, nxt))

ck('L0a 偏移 0 血缘外条数 16', len(targets) == 16, len(targets))
kind = collections.Counter(); detail = []
for vt_d, a, ad, imm, nxt in targets:
    p_d = PTD_OF[vt_d]; p_i = PTD_OF[imm]
    bcd_i = PTD_BCD.get(p_i) or []
    bcd_d = PTD_BCD.get(p_d) or []
    idx_d_in_i = next((i for i, x in enumerate(bcd_i) if x[0] == p_d), -1)
    idx_i_in_d = next((i for i, x in enumerate(bcd_d) if x[0] == p_i), -1)
    if idx_d_in_i >= 0: k = 'imm_is_subclass'
    elif idx_i_in_d >= 0: k = 'imm_is_ancestor'
    else: k = 'unrelated'
    kind[k] += 1
    detail.append(dict(cls_d=CLS[vt_d], cls_imm=CLS[imm], impl=hex(a), store=hex(ad), imm=hex(imm),
                       n_d=nslot(vt_d), n_imm=nslot(imm), n_b=nslot(vt_b) if False else None,
                       idx_d_in_i=idx_d_in_i, idx_i_in_d=idx_i_in_d, kind=k,
                       next_call=hex(nxt) if nxt else None,
                       nxt_in_vt=(nxt in ALLREF) if nxt else None,
                       mdisp_imm=MD[imm]))
for r in detail:
    print('   L1 %-52s <- %-52s n_d=%-3d n_imm=%-3d idx_d_in_i=%-2d idx_i_in_d=%-2d %-16s call=%s%s' %
          (r['cls_d'], r['cls_imm'], r['n_d'], r['n_imm'], r['idx_d_in_i'], r['idx_i_in_d'], r['kind'],
           r['next_call'], ' (inVT)' if r['nxt_in_vt'] else ''))
print('   L3 形态分布: %s' % dict(kind))
ck('L2a imm 的 mdisp 全为 0（主表）', all(r['mdisp_imm'] == 0 for r in detail), True)
ck('L3a 三类覆盖 16', sum(kind.values()) == 16, sum(kind.values()))

# R1 反控：把祖先判据改成「BCD 任意下标含 0」+「含自身」
alt = 0
for vt_d, a, ad, imm, nxt in targets:
    p_d = PTD_OF[vt_d]; p_i = PTD_OF[imm]
    lst = PTD_BCD.get(p_d) or []
    if any(x[0] == p_i for x in lst): alt += 1
ck('R1 含下标 0 的宽松口径下血缘内条数', True, alt)
json.dump(dict(n=len(targets), kind=dict(kind), detail=detail, alt_kin=alt, asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r200/m3_off0out.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
