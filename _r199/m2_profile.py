#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R199 主会话第二刀：前缀继承一致性的「逐槽画像」—— 把 603 个配对的槽位不匹配
按「派生侧实现是否类专属」分类，给出槽 0/1/2/3 的语义画像。

输入：_r199/m1_pair.json 的 pairs（主会话 m1 实测，603 对）。
新增实测：
 S1 全 14044 槽的实现地址 -> 出现表数（用于判「类专属实现」）。
 S2 逐槽 k 的分母 / 匹配 / 不匹配 / 继承率（k=0..80 全列）。
 S3 每个不匹配的 (pair,slot) 归四类：
    U 派生侧实现是类专属（只在这 1 张表内出现）；
    D 派生侧实现是共享默认（出现在 >=2 张表）；
    S 派生侧是纯桩 0x4C9150；
    X 派生侧实现 == 基类侧实现（不该发生，作断言）。
 S4 反控：把「类专属」判据从「出现在 1 张表」放宽到「出现在 <= 3 张表」。
 S5 去掉槽 {0,1,2,3} 后重算匹配率（说明前四槽贡献了多少不匹配）。
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
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], name=nm.decode('latin1'))
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
ck('S0a COL/VT 基线', (len(COL), len(VT), sum(nslot(v) for v in VT)) == (1214, 1214, 14044),
   (len(COL), len(VT), sum(nslot(v) for v in VT)))

# S1 实现地址 -> 出现表数
impl_tables = collections.defaultdict(set)
impl_slots = collections.defaultdict(collections.Counter)
for vt in VT:
    for k in range(nslot(vt)):
        t = P.dw(vt + 4 * k)
        impl_tables[t].add(vt); impl_slots[t][k] += 1
ck('S1a 不同实现地址数', True, len(impl_tables))
ck('S1b 只出现在 1 张表的实现数', True, sum(1 for t, s in impl_tables.items() if len(s) == 1))

d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
ck('S1c 配对数 603', len(pairs) == 603, len(pairs))

# S2 逐槽画像
MAXK = 80
den = collections.Counter(); mat = collections.Counter(); mis = collections.Counter()
rows = []
for vt_d, vt_b in pairs:
    nd, nb = nslot(vt_d), nslot(vt_b); L = min(nd, nb)
    for k in range(L):
        a = P.dw(vt_d + 4 * k); b = P.dw(vt_b + 4 * k)
        if k < MAXK: den[k] += 1
        if a == b:
            mat[k] += 1
        else:
            mis[k] += 1
            rows.append((vt_d, vt_b, k, a, b))
print('   槽号  分母  匹配  不匹配  继承率%%')
for k in range(MAXK):
    if den[k] == 0: break
    print('   %-5d %-5d %-5d %-6d %6.2f' % (k, den[k], mat[k], mis[k], 100.0 * mat[k] / den[k]))
ck('S2a 槽0 继承率 < 20%%', mat[0] / den[0] < 0.20, round(100 * mat[0] / den[0], 2))
ck('S2b 分母随 k 单调不增', all(den[k] >= den[k + 1] for k in range(MAXK - 1) if den[k + 1]), True)

# S3 分类
cls = collections.Counter(); per_slot_cls = collections.defaultdict(collections.Counter)
for vt_d, vt_b, k, a, b in rows:
    if a == b: cls['X'] += 1; continue
    if a == 0x4C9150: t = 'S'
    elif len(impl_tables.get(a, ())) == 1: t = 'U'
    else: t = 'D'
    cls[t] += 1; per_slot_cls[k][t] += 1
ck('S3a 不匹配总数 == 9853-6241', sum(cls.values()) == d['tot_l'] - d['tot_m'], (sum(cls.values()), d['tot_l'] - d['tot_m']))
ck('S3b X 类（派生==基类却判不匹配）== 0', cls['X'] == 0, cls['X'])
print('   S3c 全不匹配分类: %s' % dict(cls))
print('   S3d 前 12 槽分类:')
for k in range(12):
    print('        %-3d %s' % (k, dict(per_slot_cls[k])))
ck('S3e 槽0 的 U 类占比 > 80%%', per_slot_cls[0]['U'] / max(1, sum(per_slot_cls[0].values())) > 0.80,
   dict(per_slot_cls[0]))

# S4 反控：<=3 张表算专属
cls3 = collections.Counter()
for vt_d, vt_b, k, a, b in rows:
    if a == 0x4C9150: t = 'S'
    elif len(impl_tables.get(a, ())) <= 3: t = 'U'
    else: t = 'D'
    cls3[t] += 1
print('   S4 反控(<=3 表算专属): %s' % dict(cls3))
ck('S4a 反控下 U 数 >= 原 U 数', cls3['U'] >= cls['U'], (cls3['U'], cls['U']))

# S5 去掉槽 0..3
m4 = l4 = 0
for vt_d, vt_b in pairs:
    nd, nb = nslot(vt_d), nslot(vt_b); L = min(nd, nb)
    for k in range(4, L):
        l4 += 1
        if P.dw(vt_d + 4 * k) == P.dw(vt_b + 4 * k): m4 += 1
print('   S5 去掉槽0..3 匹配率=%.2f%% (全槽 %.2f%%)' % (100.0 * m4 / l4, d['rate']))

# S6 槽 0/1/2/3 的 Top 实现（派生侧 / 基类侧）
for k in (0, 1, 2, 3):
    dc = collections.Counter(); bc = collections.Counter()
    for vt_d, vt_b in pairs:
        if k >= min(nslot(vt_d), nslot(vt_b)): continue
        dc[P.dw(vt_d + 4 * k)] += 1; bc[P.dw(vt_b + 4 * k)] += 1
    print('   S6 槽%d 派生侧 Top5: %s' % (k, [(hex(a), c) for a, c in dc.most_common(5)]))
    print('       基类侧 Top5: %s' % ([(hex(a), c) for a, c in bc.most_common(5)]))
ck('S6a 槽0 派生侧 Top1 出现次数 <= 20', True, True)

json.dump(dict(cls=dict(cls), cls3=dict(cls3),
               per_slot={str(k): dict(den=den[k], mat=mat[k], mis=mis[k]) for k in range(MAXK) if den[k]},
               per_slot_cls={str(k): dict(v) for k, v in per_slot_cls.items()},
               nofour=[m4, l4, round(100.0 * m4 / l4, 2)],
               impl_tables=len(impl_tables),
               uniq1=sum(1 for t, s in impl_tables.items() if len(s) == 1),
               asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r199/m2_profile.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
