#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R199 主会话第七刀（决定性）：槽 0 的 516 个类专属实现 = 「改档到基类表 + 调基类槽0」的链式析构形态。
本卡不下语义命名断言，只给字节与地址的对应关系。

判据：
 H1 对每个派生侧槽 0 实现，取全部 mov dword ptr [reg(+disp)], imm32 里 imm 是虚表地址的那些。
 H2 对每个这样的 imm（= 被装的表 vt_x），取该表的类名 X 与 mdisp。
 H3 三分类：
    (i) X == 派生类自身（装回本类表）；
    (ii) X 的 pTD 出现在派生类 CHD 的 BCD 里（= X 是派生类的某个基类），进一步分
         mdisp==0 的直基类 / 其它基类；
    (iii) X 与派生类无 RTTI 关系。
 H4 紧跟在该 store 之后的 call 目标，是否等于被装那张表 vt_x 的槽 0 实现（= 直接转调基类槽 0）。
 H5 对 (ii)+mdisp==0 的那一类，给出「store 的表 == 直基类主表」的命中率。
 H6 部分实现无 store（54 个）：它们的槽 0 体首 20 条给出来，看是纯跳转/纯 delete。
反控：
 R1 把 H4 的判据放宽到「call 目标落在 vt_x 的前 8 个槽里任一」，命中率变化。
 R2 把 H3 的 (iii) 类（无 RTTI 关系）样本逐条列出，若数量少则证明分类完备。
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
CLS = {vt: COL[VT[vt]]['name'] for vt in VT}
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}
PTD = {vt: COL[VT[vt]]['ptd'] for vt in VT}

CHD = {}
for c, cc in COL.items():
    v = cc['pchd']
    if v in CHD: continue
    CHD[v] = dict(n=P.dw(v + 8), arr=P.dw(v + 12))
BCDS = {}
for v, d in CHD.items():
    arr = d['arr']; lst = None
    if P.where(arr) not in ('None', 'other') and d['n'] is not None and 0 < d['n'] <= 64:
        lst = [P.dw(arr + 4 * j) for j in range(d['n'])]
        if any(x is None for x in lst): lst = None
    d['bcds'] = lst
    for b in (lst or []):
        BCDS[b] = dict(ptd=P.dw(b), ncb=P.dw(b + 4), mdisp=s32(P.dw(b + 8)), chd=v)
def direct_children(bcds, i):
    out = []; n = len(bcds); lim = i + BCDS[bcds[i]]['ncb']; j = i + 1
    while j <= lim and j < n:
        out.append(j); j = j + BCDS[bcds[j]]['ncb'] + 1
    return out

def body(va, maxb=400, maxi=200):
    o = P.r2o(va)
    if o is None: return None
    ins = []
    for i in md.disasm(RAW[o:o + maxb], va):
        ins.append((i.address, i.size, i.mnemonic, i.op_str))
        if i.mnemonic.startswith('ret'): break
        if len(ins) >= maxi: break
    return ins

STORE_RE = re.compile(r'^dword ptr \[(e[a-z]{2})(?: \+ (0x[0-9a-f]+))?\], (0x[0-9a-f]+)$')
d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
s0d = []
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1: continue
    a = P.dw(vt_d); b = P.dw(vt_b)
    if a != b: s0d.append((vt_d, a))
ck('H0a 槽0 派生不匹配 516', len(s0d) == 516, len(s0d))

cls_c = collections.Counter(); h4_hit = 0; h4_tot = 0; h5_hit = 0; h5_tot = 0
no_store = []; other_samples = []; detail = []
for vt_d, a in s0d:
    ins = body(a); own = CLS[vt_d]
    col = COL[VT[vt_d]]; ch = CHD.get(col['pchd'])
    bptds = set()
    direct0 = set()
    if ch and ch['bcds']:
        for j, bb in enumerate(ch['bcds']): bptds.add(BCDS[bb]['ptd'])
        for j in direct_children(ch['bcds'], 0):
            if BCDS[ch['bcds'][j]]['mdisp'] == 0: direct0.add(BCDS[ch['bcds'][j]]['ptd'])
    stores = []; calls = []
    for i, (ad, sz, mn, op) in enumerate(ins):
        if mn == 'mov':
            m = STORE_RE.match(op)
            if m: stores.append((ad, m.group(1), int(m.group(3), 16), m.group(2)))
        if mn == 'call' and op.startswith('0x'):
            calls.append((ad, int(op, 16)))
    if not stores: no_store.append((own, hex(a), n_op := len(ins),
                                   [('%s %s' % (m, o)).strip() for _, _, m, o in ins[:12]]))
    for (sad, reg, imm, disp) in stores:
        if imm not in CLS: cls_c['nonvt'] += 1; continue
        if CLS[imm] == own: cls_c['self'] += 1; continue
        if CLS[imm] in ('',): cls_c['other'] += 1; continue
        if imm in VT and PTD[imm] in direct0:
            cls_c['direct0_base'] += 1
            h5_tot += 1
        elif imm in VT and PTD[imm] in bptds:
            cls_c['inbcd_non0'] += 1
        else:
            cls_c['noRTTI'] += 1
            if len(other_samples) < 12: other_samples.append((own, hex(a), CLS[imm], MD[imm]))
        # H4: store 之后第一个 call 的目标 == vt_x 的槽0
        nxt = None
        for (cad, tgt) in calls:
            if cad > sad: nxt = tgt; break
        h4_tot += 1
        nk = nslot(imm)
        if nk >= 1 and P.dw(imm) == nxt: h4_hit += 1
        if imm in VT and PTD[imm] in direct0:
            if nk >= 1 and P.dw(imm) == nxt: h5_hit += 1
print('   H3 store 目标分类: %s' % dict(cls_c))
ck('H3a self + direct0_base + inbcd_non0 + nonvt + noRTTI == store 总数',
   cls_c['self'] + cls_c['direct0_base'] + cls_c['inbcd_non0'] + cls_c['nonvt'] + cls_c['noRTTI'] == h4_tot,
   (dict(cls_c), h4_tot))
ck('H3b 装「直基类表」占 store 多数（>=60%%）', cls_c['direct0_base'] >= 0.60 * h4_tot,
   (cls_c['direct0_base'], h4_tot))
ck('H3c 无 RTTI 关系的 store 占比 < 5%%', cls_c['noRTTI'] < 0.05 * h4_tot, (cls_c['noRTTI'], h4_tot))
print('   H4 装表后首个 call == 该表槽0: %d/%d (%.2f%%)' % (h4_hit, h4_tot, 100.0 * h4_hit / h4_tot))
ck('H4a 转调命中率 >= 85%%', h4_hit >= 0.85 * h4_tot, (h4_hit, h4_tot))
print('   H5 装的是直基类表时转调命中: %d/%d (%.2f%%)' % (h5_hit, h5_tot, 100.0 * h5_hit / max(1, h5_tot)))
ck('H5a 直基类那支命中率 >= 90%%', h5_hit >= 0.90 * h5_tot, (h5_hit, h5_tot))
print('   H6 无 store 的实现 %d 个，例: %s' % (len(no_store), [(x[0], x[1], x[2]) for x in no_store[:8]]))
print('       0x414290 体: %s' % (no_store[0][3] if no_store else None))
ck('H6a 无 store 的个数 < 60', len(no_store) < 60, len(no_store))
print('   R2 无 RTTI 关系样本: %s' % other_samples[:12])

# R1 放宽到 vt_x 前 8 槽
h1 = 0; t1 = 0
for vt_d, a in s0d:
    ins = body(a); calls = [(ad, int(op, 16)) for ad, sz, mn, op in ins if mn == 'call' and op.startswith('0x')]
    for ad, sz, mn, op in ins:
        if mn != 'mov': continue
        m = STORE_RE.match(op)
        if not m: continue
        imm = int(m.group(3), 16)
        if imm not in CLS: continue
        sad = ad
        nxt = None
        for (cad, tgt) in calls:
            if cad > sad: nxt = tgt; break
        t1 += 1
        for k in range(8):
            if P.dw(imm + 4 * k) == nxt: h1 += 1; break
print('   R1 放宽到前 8 槽: %d/%d (%.2f%%)' % (h1, t1, 100.0 * h1 / t1))
ck('R1a 放宽后命中率 >= 严格命中率', h1 >= h4_hit, (h1, h4_hit))

json.dump(dict(cls=dict(cls_c), h4=[h4_hit, h4_tot], h5=[h5_hit, h5_tot], r1=[h1, t1],
               no_store=[[x[0], x[1], x[2]] for x in no_store],
               no_store_bodies={x[1]: x[3] for x in no_store[:6]},
               noRTTI_samples=other_samples, asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r199/m7_dtor.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
