#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R199 主会话第十刀：复核执行员 B 的核心主张，并查它与「槽 0 恒为类专属」的冲突。

复核项：
 J1 0x4C9150 的 33 槽号 / 39 表 / 205 槽位（主会话独立算）。
 J2 「39 张表全部没有 mdisp==0 直基类」——与 (b)=256 的集合做交叉，验证 39 是不是 256 的子集。
 J3 槽 0 上出现 0x4C9150 的表（执行员报 5 张）：逐张列出类名 / 槽数 / 该表槽 0 是否真的是 0x4C9150，
    并检查这些表是否在 954 主表内（若是主表，则与本轮「槽 0 恒为类专属析构」的画像冲突，必须解释）。
 J4 33 个槽号逐个给「有几张表在该槽填桩」「该槽在 954 主表上的继承率（来自 m2）」。
 J5 每张表的桩槽位是否在表尾（k >= nslot-3）。
 J6 反控：把桩判据从「地址 0x4C9150」换成「体内恰为 xor eax,eax; ret 且首 3 字节 33 C0 C3」，
    重算 33/39/205。
"""
import sys, struct, collections, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

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
MAIN = [vt for vt in VT if MD[vt] == 0]

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
def has_base0(vt):
    col = COL[VT[vt]]; ch = CHD.get(col['pchd'])
    if not ch or not ch['bcds']: return False
    for j in direct_children(ch['bcds'], 0):
        if BCDS[ch['bcds'][j]]['mdisp'] == 0: return True
    return False

STUB = 0x4C9150
tabs = []; slots = collections.Counter()
for vt in VT:
    ks = [k for k in range(nslot(vt)) if P.dw(vt + 4 * k) == STUB]
    if ks:
        tabs.append((vt, ks));
        for k in ks: slots[k] += 1
tot = sum(len(k) for _, k in tabs)
print('   J1 桩: 槽号种类=%d 表数=%d 槽位数=%d' % (len(slots), len(tabs), tot))
ck('J1a 33/39/205 复现', (len(slots), len(tabs), tot) == (33, 39, 205), (len(slots), len(tabs), tot))
print('   J1b 槽号集合=%s' % sorted(slots))

# J2 交叉
nobase = set(vt for vt in MAIN if not has_base0(vt))
sub = sum(1 for vt, _ in tabs if vt in nobase)
print('   J2 39 张表里在 954 主表内的=%d，在 (b) 无直基类集合(=%d) 内的=%d'
      % (sum(1 for vt, _ in tabs if vt in MD and MD[vt] == 0), len(nobase), sub))
ck('J2a 39 张全在无直基类集合', sub == len(tabs), (sub, len(tabs)))
ck('J2b (b) 集合大小 256 复现', len(nobase) == 256, len(nobase))

# J3 槽 0 上的桩
s0tabs = [vt for vt, ks in tabs if 0 in ks]
print('   J3 槽 0 上填桩的表 %d 张:' % len(s0tabs))
for vt in s0tabs:
    print('        %-46s vt=%s nslot=%d mdisp=%d 有直基类主表=%s'
          % (CLS[vt], hex(vt), nslot(vt), MD[vt], has_base0(vt)))
ck('J3a 槽 0 填桩的表数 <= 8', len(s0tabs) <= 8, len(s0tabs))

# J4 逐槽号
m2 = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m2_profile.json'))
ps = m2['per_slot']
print('   J4 槽号 / 填桩表数 / 该槽在 954 主表上的继承率')
for k in sorted(slots):
    d = ps.get(str(k))
    r = ('%.2f%%' % (100.0 * d['mat'] / d['den'])) if d else 'n/a'
    print('        %-4d %-4d %s' % (k, slots[k], r))
ck('J4a 桩槽号为 33 个', len(slots) == 33, len(slots))

# J5 桩在表尾？
tail = 0; mid = 0
for vt, ks in tabs:
    n = nslot(vt)
    if max(ks) >= n - 1: tail += 1
    else: mid += 1
print('   J5 桩覆盖到表尾的表=%d，桩止于表中间的=%d' % (tail, mid))
ck('J5a 桩多在表尾', tail >= mid, (tail, mid))

# J6 反控
bt = RAW[T['rawptr']:T['rawptr'] + (HI - LO)]
hits = set(LO + i for i in range(len(bt) - 2) if bt[i:i + 3] == b'\x33\xc0\xc3')
t2 = 0; s2 = collections.Counter(); tot2 = 0
for vt in VT:
    for k in range(nslot(vt)):
        if P.dw(vt + 4 * k) in hits:
            t2 += 1; s2[k] += 1; tot2 += 1
print('   J6 反控(按体首3字节): 槽号种类=%d 表数=%d 槽位数=%d' % (len(s2), t2, tot2))
ck('J6a 反控使槽位总数显著变大', tot2 > tot, (tot2, tot))

json.dump(dict(stub=[len(slots), len(tabs), tot], slotmap=dict(slots),
               s0tabs=[[hex(vt), CLS[vt], nslot(vt)] for vt in s0tabs],
               nobase=len(nobase), sub=sub, tail=[tail, mid],
               ctrl=[len(s2), t2, tot2], asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r199/m10_stubcheck.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
