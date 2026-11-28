#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 主会话第二刀：538 条 [reg(+off)]=imm32 装表 store 的「目标偏移」切片。

m1 发现 42 条 other_main 里有 19 条 imm 指向「与 vt_d 无 RTTI 血缘」的类（?$VectorClass@..@、
?$rc_ptr@..@、GenericNode），形状像是「在对象内部偏移处装**内嵌成员子对象**的表」而不是装主表。
本刀用 store 的目标偏移（base + disp）做硬判据：
 K1 全部 538 条 store 记录 (基址寄存器, 偏移, imm)；偏移缺省记 0。
 K2 按 (偏移==0 / 偏移!=0) x (own/base/other/nonvt/sub) 交叉。
 K3 血统判据（与 m1 同）：imm 的 pTD 是否是 vt_d 的祖先（含自身）。
     假设 H1：偏移==0 的 store 全是血缘内（own/base/ancestor）；偏移!=0 的 store 允许血缘外。
 K4 对偏移!=0 的样本，给偏移值分布与 imm 类名清单（去重）。
反控：
 R1 把偏移判据从「操作数文本里有 +0x..」换成「base 寄存器是 esp/ebp」（栈上对象），看交叉是否变化。
 R2 用 m1 的 42 条 other_main 单独看偏移分布：若 42 条全是偏移!=0，则 R199 的「装其它主表」表述应改为
    「在对象内部偏移处装内嵌子对象表」。
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
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], pchd=w[i + 4],
                                 name=nm.decode('latin1'))
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
        bcd = P.dw(bca + 4 * i)
        ptd = P.dw(bcd + 0) if bcd else None
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
ck('K0a 516', len(s0d) == 516, len(s0d))

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
rows = []
for vt_d, a, vt_b in s0d:
    for ad, sz, mn, op in body(a) or []:
        if mn != 'mov': continue
        m = STORE_RE.match(op)
        if not m: continue
        reg = m.group(1); off = int(m.group(2), 16) if m.group(2) else 0
        imm = int(m.group(3), 16)
        if imm == vt_d: t = 'own_main'
        elif imm == vt_b: t = 'base_main'
        elif imm in VT and MD[imm] != 0: t = 'subtable'
        elif imm in VT: t = 'other_main'
        else: t = 'nonvt'
        rows.append(dict(vt_d=vt_d, impl=a, at=ad, reg=reg, off=off, imm=imm, cat=t))
ck('K1a store 总数 538', len(rows) == 538, len(rows))

cross = collections.Counter()
for r in rows: cross[('off0' if r['off'] == 0 else 'offN', r['cat'])] += 1
print('   K2 交叉: %s' % dict(sorted(cross.items())))
ck('K2a off0 总数 + offN 总数 == 538', sum(v for (k, c), v in cross.items() if k == 'off0') +
   sum(v for (k, c), v in cross.items() if k == 'offN') == 538, True)

# K3 血统
def lineage_ok(vt_d, imm):
    if imm not in VT: return False
    p_d = PTD_OF[vt_d]; p_i = PTD_OF[imm]
    if p_d == p_i: return True
    lst = PTD_BCD.get(p_d)
    if not lst: return False
    return any(x[0] == p_i for x in lst[1:])

l3 = collections.Counter()
for r in rows:
    ok = lineage_ok(r['vt_d'], r['imm'])
    l3[('off0' if r['off'] == 0 else 'offN', 'kin' if ok else 'out')] += 1
print('   K3 偏移 x 血统: %s' % dict(sorted(l3.items())))
off0_out = l3[('off0', 'out')]; offN_out = l3[('offN', 'out')]
ck('K3a 偏移 0 的 store 里血缘外的条数', True, off0_out)
ck('H1 偏移!=0 的血缘外条数 >= 偏移 0 的血缘外条数', offN_out >= off0_out, (offN_out, off0_out))

# K4 偏移分布
offc = collections.Counter(r['off'] for r in rows)
print('   K4 偏移分布 Top12: %s' % [(hex(o), c) for o, c in offc.most_common(12)])
print('   K4 offN 的 (类, imm 类名, 偏移) 去重:')
seen = set()
for r in rows:
    if r['off'] == 0: continue
    key = (CLS[r['vt_d']], CLS.get(r['imm'], hex(r['imm'])), r['off'])
    if key in seen: continue
    seen.add(key)
    print('        %-56s <- %-56s +0x%X' % key)
ck('K4a offN 去重形状数 >= 10', len(seen) >= 10, len(seen))

# R199 的 42 条 other_main 的偏移分布
om = [r for r in rows if r['cat'] == 'other_main']
omz = sum(1 for r in om if r['off'] == 0)
ck('R2a other_main 42 条中偏移==0 的条数', True, omz)
print('   R2 other_main 偏移==0 条数 %d / 42 ; 偏移分布 %s' %
      (omz, [(hex(o), c) for o, c in collections.Counter(r['off'] for r in om).most_common(8)]))
# 反控 R1: 栈基址
stk = sum(1 for r in rows if r['reg'] in ('esp', 'ebp'))
ck('R1 栈基址 store 条数', True, stk)

json.dump(dict(cross={'%s|%s' % k: v for k, v in cross.items()},
               lin={'%s|%s' % k: v for k, v in l3.items()},
               offdist={hex(o): c for o, c in offc.items()},
               om_off0=omz, n_om=len(om), stk=stk,
               rows=[dict(cls_d=CLS[r['vt_d']], impl=hex(r['impl']), reg=r['reg'], off=r['off'],
                          imm=hex(r['imm']), cat=r['cat'], cls_imm=CLS.get(r['imm'])) for r in rows],
               asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r200/m2_store_off.json', 'w'),
          ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
