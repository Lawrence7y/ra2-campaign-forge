#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R199 主会话第四刀：配对覆盖面的成因 —— 95 个 (d2) 与 256 个 (b) 到底是哪一类。

C1 (b) 256 个：给它们的 ncb[0]、BCD 数组长度、CHD 指针、类名前 20 条。
   交叉验证：全体 BCD 里 ncb==0 的个数、以及这 256 个的 mdisp 分布。
C2 (d2) 95 个：给类名、直基类名、直基类 pTD 是否在 .data、该 pTD+8 名串、直基类的 mdisp。
C3 交付比例：698/954 = 73.17% 有可配对主基类，256 无直基类 = 26.83%。
C4 反控：把「直基类须 mdisp==0」放宽成「任一直基类 pTD 落在 954 主表集合」，
   配对数从 603 变成多少（说明 mdisp 约束的影响）。
C5 反控：把「CHD 根结点下标 0」改成「取 BCD 数组第 0 个元素的 ncb 为 n-1 的那张」，应仍 954/954。
C6 槽 0 类专属实现的「每类一份」检验：516 个槽 0 不匹配里，派生侧实现地址里有多少个
   在全镜像 14044 槽里只出现 1 次；有多少个只出现在槽 0。
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
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
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
MAIN = [vt for vt in VT if COL[VT[vt]]['mdisp'] == 0]
TD2VT = {}
for vt in MAIN: TD2VT[COL[VT[vt]]['ptd']] = vt

CHD = {}
for c, cc in COL.items():
    v = cc['pchd']
    if v in CHD: continue
    CHD[v] = dict(sig=P.dw(v), attr=P.dw(v + 4), n=P.dw(v + 8), arr=P.dw(v + 12))
BCDS = {}
for v, d in CHD.items():
    arr = d['arr']; lst = None
    if P.where(arr) not in ('None', 'other') and d['n'] is not None and 0 < d['n'] <= 64:
        lst = [P.dw(arr + 4 * j) for j in range(d['n'])]
        if any(x is None for x in lst): lst = None
    d['bcds'] = lst
    for b in (lst or []):
        BCDS[b] = dict(ptd=P.dw(b), ncb=P.dw(b + 4), mdisp=s32(P.dw(b + 8)),
                       pdisp=s32(P.dw(b + 12)), vdisp=s32(P.dw(b + 16)), attr=P.dw(b + 20), chd=v)
ck('C0a CHD 954 / BCD 1002', (len(CHD), len(BCDS)) == (954, 1002), (len(CHD), len(BCDS)))

def direct_children(bcds, i):
    out = []; n = len(bcds)
    lim = i + BCDS[bcds[i]]['ncb']; j = i + 1
    while j <= lim and j < n:
        out.append(j); j = j + BCDS[bcds[j]]['ncb'] + 1
    return out

# C1 (b) 256 个无直基类
b_list = []
for vt in MAIN:
    col = COL[VT[vt]]; d = CHD.get(col['pchd'])
    if not d or not d['bcds']: b_list.append(vt); continue
    if not direct_children(d['bcds'], 0): b_list.append(vt)
ck('C1a (b)+无CHD 合计 256', len(b_list) == 256, len(b_list))
nb0 = collections.Counter(); nmd = collections.Counter(); nlen = collections.Counter()
for vt in b_list:
    col = COL[VT[vt]]; d = CHD.get(col['pchd'])
    nmd[col['mdisp']] += 1
    if d and d['bcds']:
        nb0[BCDS[d['bcds'][0]]['ncb']] += 1; nlen[len(d['bcds'])] += 1
    else:
        nb0['noCHD'] += 1; nlen['noCHD'] += 1
print('   C1b (b) 的 ncb[0] 分布: %s' % dict(nb0))
print('   C1c (b) 的 BCD 数组长度分布: %s' % dict(nlen))
print('   C1d (b) 的 mdisp 分布: %s' % dict(nmd))
print('   C1e (b) 类名前 20: %s' % [COL[VT[v]]['name'] for v in b_list[:20]])
ck('C1f (b) 全部 ncb[0]==0 或 -1', all(k in (0, -1, 'noCHD') for k in nb0), dict(nb0))
ck('C1g (b) 全部是 mdisp==0 主表', set(nmd) == {0}, dict(nmd))
all_ncb0 = sum(1 for b, x in BCDS.items() if x['ncb'] == 0)
print('   C1h 全体 BCD 里 ncb==0 的个数=%d（其中根结点数=%d）' % (all_ncb0, len([v for v in b_list if CHD.get(COL[VT[v]]['pchd'], {}).get('bcds')])))

# C2 (d2) 95 个
d2 = []
for vt in MAIN:
    col = COL[VT[vt]]; d = CHD.get(col['pchd'])
    if not d or not d['bcds']: continue
    ch = direct_children(d['bcds'], 0)
    if not ch: continue
    z = [j for j in ch if BCDS[d['bcds'][j]]['mdisp'] == 0]
    if len(z) != 1: continue
    bp = BCDS[d['bcds'][z[0]]]['ptd']
    if bp not in TD2VT:
        bn = P.cstr(bp + 8, 400) if P.where(bp) else None
        d2.append((col['name'], bn.decode('latin1') if bn else '?', bp,
                   BCDS[d['bcds'][z[0]]]['mdisp'], P.where(bp)))
ck('C2a (d2) 共 95 个', len(d2) == 95, len(d2))
print('   C2b (d2) 前 30 (类 -> 直基类, pTD, mdisp, pTD段):')
for r in d2[:30]: print('        %-42s -> %-38s %s %s %s' % r)
dn = collections.Counter(r[1] for r in d2)
print('   C2c (d2) 直基类名去重=%d，Top10: %s' % (len(dn), dn.most_common(10)))
ck('C2d (d2) 直基类 pTD 全落 .data', set(r[4] for r in d2) <= {'.data'}, collections.Counter(r[4] for r in d2))

# C4 反控：去掉 mdisp==0 约束
c4 = 0
for vt in MAIN:
    col = COL[VT[vt]]; d = CHD.get(col['pchd'])
    if not d or not d['bcds']: continue
    ch = direct_children(d['bcds'], 0)
    if any(BCDS[d['bcds'][j]]['ptd'] in TD2VT for j in ch): c4 += 1
print('   C4 放宽 mdisp 约束后配对数=%d（原 603，差 +%d）' % (c4, c4 - 603))
ck('C4a 放宽后配对数 >= 603', c4 >= 603, (c4, 603))

# C5 反控：ncb[0]==n-1 自证
ok = 0; tot = 0
for v, d in CHD.items():
    if not d['bcds']: continue
    tot += 1
    if BCDS[d['bcds'][0]]['ncb'] == len(d['bcds']) - 1: ok += 1
print('   C5 ncb[0]==n-1 成立 %d/%d' % (ok, tot))
ck('C5a ncb[0]==n-1 全覆盖', ok == tot, (ok, tot))

# C6 槽0 不匹配实现的唯一性
impl_tab = collections.defaultdict(set); impl_slot = collections.defaultdict(set)
for vt in VT:
    for k in range(nslot(vt)):
        t = P.dw(vt + 4 * k); impl_tab[t].add(vt); impl_slot[t].add(k)
dp = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in dp['pairs']]
s0u = [];
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1: continue
    a = P.dw(vt_d); b = P.dw(vt_b)
    if a != b: s0u.append(a)
ck('C6a 槽0 不匹配 516 条', len(s0u) == 516, len(s0u))
u1 = sum(1 for a in s0u if len(impl_tab[a]) == 1)
u_0only = sum(1 for a in s0u if impl_slot[a] == {0})
uniq = len(set(s0u))
print('   C6b 槽0 不匹配的派生实现: 出现次数=%d 去重=%d 只占1张表=%d 只出现在槽0=%d'
      % (len(s0u), uniq, u1, u_0only))
ck('C6c 槽0 不匹配的实现去重后每个基本只见 1 次', uniq >= 0.95 * len(s0u), (uniq, len(s0u)))

json.dump(dict(b_count=len(b_list), b_names=[COL[VT[v]]['name'] for v in b_list],
               b_ncb0={str(k): v for k, v in nb0.items()}, b_len={str(k): v for k, v in nlen.items()},
               d2=[[r[0], r[1], hex(r[2]), r[3], r[4]] for r in d2],
               c4=c4, ncb0_root_ok=[ok, tot],
               s0u=[hex(a) for a in s0u], s0u_uniq=uniq, s0u_1table=u1, s0u_slot0only=u_0only,
               asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r199/m4_coverage.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
