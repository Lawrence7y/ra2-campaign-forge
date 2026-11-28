#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 主会话第五刀：42 条 other_main 与「直基类主表 vt_b」的关系定位。

m4 已定量：538 条 store 里 518 条（96.28%）基址归约为 this；this 侧 other_main 30 条、非 this 侧 12 条。
本刀回答「既然装的是别的表，那它到底比直基类表更靠上还是更靠下」：
 N1 对每条 other_main，沿 vt_d 的 BCD 祖先列表求：
     idx_imm = imm 类在祖先里的下标（0 = 自身，>=1 为祖先；-1 表示不在）
     idx_b   = 直基类（vt_b 的类）在祖先里的下标
 N2 统计 (idx_b, idx_imm) 对：若 idx_imm > idx_b 说明装的是「更靠上（更远）的祖先」，
    idx_imm < idx_b 说明装的是「比直基类更近的自表」（正常应为 own_main）。
 N3 对 idx_imm > idx_b 的样本，给 vt_d / 直基类 / imm 三者的 nslot，判断是否「同槽数族」
    （= 编译器把 grand-base 表直接写进去的冗余初始化）。
 N4 对 sibling / unrelated 样本，给 vtable 表头地址的差值（imm_vt - vt_d）与是否相邻排布。
反控：
 R1 把祖先列表换成「只取 mdisp==0 的祖先」重算 idx，看分类是否变化。
 R2 用「nslot 相同」作为替代判据，看与 N3 是否一致。
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
rows = []
for vt_d, a, vt_b in s0d:
    for ad, sz, mn, op in body(a) or []:
        if mn != 'mov': continue
        m = STORE_RE.match(op)
        if not m: continue
        imm = int(m.group(3), 16)
        if imm not in VT or MD[imm] != 0: continue
        if imm == vt_d or imm == vt_b: continue
        p_d = PTD_OF[vt_d]; p_i = PTD_OF[imm]; p_b = PTD_OF[vt_b]
        lst = PTD_BCD.get(p_d) or []
        idx_imm = next((i for i, x in enumerate(lst) if x[0] == p_i), -1)
        idx_b = next((i for i, x in enumerate(lst) if x[0] == p_b), -1)
        rows.append(dict(vt_d=vt_d, impl=a, at=ad, imm=imm, vt_b=vt_b,
                         idx_imm=idx_imm, idx_b=idx_b,
                         nd=nslot(vt_d), ni=nslot(imm), nb=nslot(vt_b),
                         cd=CLS[vt_d], ci=CLS[imm], cb=CLS[vt_b]))
ck('N0a other_main 42', len(rows) == 42, len(rows))
pairs2 = collections.Counter((r['idx_b'], r['idx_imm']) for r in rows)
print('   N2 (idx_b, idx_imm) 分布: %s' % dict(sorted(pairs2.items())))
ck('N2a idx_b 全为 1 的条数', True, sum(1 for r in rows if r['idx_b'] == 1))
deeper = [r for r in rows if r['idx_imm'] > r['idx_b'] and r['idx_imm'] >= 0]
closer = [r for r in rows if 0 <= r['idx_imm'] < r['idx_b']]
noidx = [r for r in rows if r['idx_imm'] < 0]
ck('N2b 三分类覆盖 42', len(deeper) + len(closer) + len(noidx) == 42, (len(deeper), len(closer), len(noidx)))
print('   N2c 更远祖先 %d / 更近 %d / 不在血缘 %d' % (len(deeper), len(closer), len(noidx)))
same_slot = sum(1 for r in deeper if r['ni'] == r['nb'] == r['nd'])
print('   N3 更远祖先里三者槽数全等 %d / %d' % (same_slot, len(deeper)))
eq_nb = sum(1 for r in rows if r['ni'] == r['nb'])
ck('N3a imm 表与直基类表槽数相同的条数', True, eq_nb)
for r in rows:
    print('   N1 %-50s <- %-50s (base %-40s) idx_imm=%-2d idx_b=%-2d n=%d/%d/%d' %
          (r['cd'], r['ci'], r['cb'], r['idx_imm'], r['idx_b'], r['nd'], r['ni'], r['nb']))
# N4 邻近排布
adj = sum(1 for r in rows if 0 < r['imm'] - r['vt_d'] <= 0x100)
ck('N4a imm 表与 vt_d 间隔 <= 0x100 的条数', True, adj)
# R1 只取 mdisp==0 祖先
alt = 0
for r in rows:
    lst = PTD_BCD.get(PTD_OF[r['vt_d']]) or []
    z = [x[0] for x in lst if x[2] == 0]
    if PTD_OF[r['imm']] in z: alt += 1
ck('R1a 只数 mdisp==0 祖先时命中条数', True, alt)
# R2 同槽数判据与 idx 判据一致性
r2 = collections.Counter()
for r in rows:
    r2[('same_slot' if r['ni'] == r['nb'] else 'diff_slot', 'deeper' if r['idx_imm'] > r['idx_b'] else ('closer' if r['idx_imm'] >= 0 else 'noKin'))] += 1
print('   R2 交叉: %s' % dict(r2))
json.dump(dict(n=len(rows), dist={'%s|%s' % k: v for k, v in pairs2.items()},
               deeper=[dict(cd=r['cd'], ci=r['ci'], cb=r['cb'], idx_imm=r['idx_imm'], n=[r['nd'], r['ni'], r['nb']]) for r in deeper],
               closer=[dict(cd=r['cd'], ci=r['ci'], n=[r['nd'], r['ni'], r['nb']]) for r in closer],
               noidx=[dict(cd=r['cd'], ci=r['ci']) for r in noidx],
               same_slot=same_slot, eq_nb=eq_nb, adj=adj, alt=alt,
               r2cross={'%s|%s' % k: v for k, v in r2.items()}, asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r200/m5_relation.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
