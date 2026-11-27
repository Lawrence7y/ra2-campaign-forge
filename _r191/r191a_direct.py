#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R191 主会话独立复算（规则 D）。

不复用 _r190 任何脚本的代码形状，只用 _r185/pe185.py 的 PE 映射。
Q1 1,013 个"直接槽"的聚集结构（同一目标被几个槽共用 / 是否落在主表）
Q2 BCD 布局先行校验（20 字节 {pTD,numContainedBases,PMD{mdisp,pdisp,vdisp},attributes}）
Q3 172/176/240/248 四档的宿主类、attributes 分布，以及"无副表"与 non-virtual 的一致性
所有数字实测后填，禁止预估。断言只对实测出来的值做记录性硬断言。
"""
import sys, os, struct, collections, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_r185'))
import pe185 as P

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

TEXT = P.B['.text']; LO = TEXT['lo']; HI = TEXT['hi_file']
def in_text(x): return x is not None and LO <= x < HI

# ---------- 枚举（按字节窗口扫，形状与 r190 不同：先建 sec 视图）----------
def words(secname):
    s = P.B[secname]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n

COL = {}
for secname in ('.rdata', '.data'):
    base, w, n = words(secname)
    for i in range(n - 4):
        if w[i] not in (0, 1) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = (w[i + 1], w[i + 3], w[i + 4], nm.decode('latin1'))
ck('Q0a COL 记录 1214 条', len(COL) == 1214, len(COL))

VT = {}
for secname in ('.rdata', '.data'):
    base, w, n = words(secname)
    for i in range(n):
        if not in_text(w[i]): continue
        head = P.dw(base + 4 * i - 4)
        if head in COL: VT[base + 4 * i] = head
ck('Q0b vtable 1214 张', len(VT) == 1214, len(VT))

def nslot(vt):
    k = 0
    while in_text(P.dw(vt + 4 * k)): k += 1
    return k
NS = {vt: nslot(vt) for vt in VT}
ck('Q0c 槽位实例合计 14044', sum(NS.values()) == 14044, sum(NS.values()))

group = collections.defaultdict(list)
for vt in sorted(VT): group[COL[VT[vt]][3]].append(vt)
ck('Q0d 名字组 954 / 多表组 94', len(group) == 954 and sum(1 for v in group.values() if len(v) > 1) == 94,
   (len(group), sum(1 for v in group.values() if len(v) > 1)))

# ---------- 分离直接槽与调整器 ----------
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def is_adj(va):
    o = P.r2o(va)
    if o is None: return False
    raw = P.RAW[o:o + 9]
    # sub dword ptr [esp + 4], imm32  =  83 6C 24 04 <imm8>   (imm8 形态)
    #                                  81 6C 24 04 <imm32>   (imm32 形态)
    if raw[0:3] == b'\x83\x6c\x24' and raw[3] == 0x04: return True
    if raw[0:3] == b'\x81\x6c\x24' and raw[3] == 0x04: return True
    return False

direct = []   # (vt, k, value)
adj = []
for vt in sorted(VT):
    if COL[VT[vt]][0] == 0: continue      # 只看非主表
    for k in range(NS[vt]):
        v = P.dw(vt + 4 * k)
        (adj if is_adj(v) else direct).append((vt, k, v))
ck('Q1a 非主表调整器 305 个', len(adj) == 305, len(adj))
ck('Q1b 非主表直接槽 1013 个', len(direct) == 1013, len(direct))
# 调整器字节形态与 r190 的 capstone 判据一致性（这里用字节锚，独立口径）
ck('Q1c 305+1013 == 1318', len(adj) + len(direct) == 1318)

# ---------- Q1 直接槽的聚集结构 ----------
byname_direct = collections.defaultdict(list)
for vt, k, v in direct: byname_direct[COL[VT[vt]][3]].append((vt, k, v))
same_group_hit = 0
for vt, k, v in direct:
    nm = COL[VT[vt]][3]
    for vt2 in group[nm]:
        if vt2 == vt: continue
        for k2 in range(NS[vt2]):
            if P.dw(vt2 + 4 * k2) == v: same_group_hit += 1; break
        else: continue
        break
ck('Q1d 同组内值匹配的直接槽 0 个', same_group_hit == 0, same_group_hit)

tgt_count = collections.Counter(v for _, _, v in direct)
uniq_addr = len(tgt_count)
shared2 = sum(1 for a, c in tgt_count.items() if c >= 2)
ck('Q1e 直接槽目标地址去重数（实测记录）', True, uniq_addr)
ck('Q1f 被 2 个以上槽共用的目标数（实测记录）', True, shared2)
top = tgt_count.most_common(10)
print('Q1g top targets:', [(hex(a), c) for a, c in top])
ck('Q1h 最大共用数（实测记录）', True, top[0][1] if top else 0)
# 最大共用目标被哪些类用
if top:
    mx = top[0][0]
    users = sorted({COL[VT[vt]][3] for vt, k, v in direct if v == mx})
    print('Q1i 最大共用目标的类数', len(users), users[:12])

# 直接槽值是否出现在任意主表（mdisp == 0）的任意槽
main_vals = set()
for vt in VT:
    if COL[VT[vt]][0] == 0:
        for k in range(NS[vt]): main_vals.add(P.dw(vt + 4 * k))
inq = sum(1 for _, _, v in direct if v in main_vals)
ck('Q1j 直接槽值落在主表任意槽的数量（实测记录）', True, inq)

# 目标地址是否都是"真函数入口"（前 1 字节常见序言）——只看字节，不判语义
pro = collections.Counter()
for a in tgt_count:
    b = P.RAW[P.r2o(a):P.r2o(a) + 3]
    pro[b[:2].hex()] += 1
print('Q1k 目标前 2 字节 Top8:', pro.most_common(8))

# ---------- Q2 BCD 布局先行校验 ----------
# BCD = {pTD(4), numContainedBases(4), PMD{mdisp,pdisp,vdisp}(12), attributes(4)} = 20 B
# 先用"自项"已知约束校验：自项 BCD 的 pTD 应等于 COL.pTD，
# 且 numContainedBases == numBaseClasses-1，PMD.mdisp == COL.mdisp，pdisp == 0xFFFFFFFF
ok_self = 0; tot_self = 0; attr_self = collections.Counter()
for colva, (mdisp, ptd, pchd, nm) in COL.items():
    nbase = P.dw(pchd + 8)
    arr = P.dw(pchd + 12)
    tot_self += 1
    for j in range(nbase):
        bcd = P.dw(arr + 4 * j)
        if bcd is None: continue
        if P.dw(bcd) != ptd: continue
        # 这一条是自项
        if P.dw(bcd + 4) != nbase - 1: continue
        if P.dw(bcd + 8) != mdisp: continue
        if P.dw(bcd + 12) != 0xFFFFFFFF: continue
        ok_self += 1
        attr_self[P.dw(bcd + 20)] += 1
        break
ck('Q2a 自项 BCD 20 字节布局校验 1214/1214', ok_self == 1214 and tot_self == 1214, (ok_self, tot_self))
print('Q2b 自项 attributes 分布:', dict(attr_self))

# ---------- Q3 四档 172/176/240/248 ----------
TIERS = (172, 176, 240, 248)
tier_owner = collections.defaultdict(list)   # mdisp -> [(colva, name, has_vt, nbase)]
for colva, (mdisp, ptd, pchd, nm) in COL.items():
    if mdisp not in TIERS: continue
    nbase = P.dw(pchd + 8)
    arr = P.dw(pchd + 12)
    has_vt = any(VT.get(v) == colva for v in VT)
    tier_owner[mdisp].append((colva, nm, has_vt, nbase, pchd, arr))
for t in TIERS:
    lst = tier_owner[t]
    print(f'Q3 tier {t}: n={len(lst)} sample={[ (hex(a), n) for a,n,*_ in lst[:4] ]}')
    ck(f'Q3 档 {t} 条数（实测记录）', True, len(lst))

# 每档的 attributes 分布（该档 COL 的 CHD 全部 BCD）
tier_attr = {}
for t in TIERS:
    c = collections.Counter()
    for colva, nm, has_vt, nbase, pchd, arr in tier_owner[t]:
        for j in range(nbase):
            bcd = P.dw(arr + 4 * j)
            if bcd is None: continue
            c[P.dw(bcd + 20)] += 1
    tier_attr[t] = dict(c)
print('Q3b 四档 attributes 分布:', tier_attr)

# 全镜像 attributes 分布 & 与 mdisp 的关系（非虚基类 bit0 假设的检验）
bit0_by_tier = collections.defaultdict(collections.Counter)
for colva, (mdisp, ptd, pchd, nm) in COL.items():
    nbase = P.dw(pchd + 8); arr = P.dw(pchd + 12)
    for j in range(nbase):
        bcd = P.dw(arr + 4 * j)
        if bcd is None: continue
        a = P.dw(bcd + 20)
        mm = P.dw(bcd + 8)
        tier = 'extra' if mm in TIERS else ('layer' if mm in (0,4,8,12,24,36,40,44,1728,21784) else 'other')
        bit0_by_tier[tier][a & 1] += 1
print('Q3c bit0 by tier:', {k: dict(v) for k, v in bit0_by_tier.items()})
ck('Q3d 记录 bit0 分布', True, {k: dict(v) for k, v in bit0_by_tier.items()})

# 副表存在性：该 (COL, mdisp) 是否真的有一张 vt 挂在同组同 mdisp
sub_exists = collections.Counter()
for colva, (mdisp, ptd, pchd, nm) in COL.items():
    lst = group[nm]
    sub_exists[mdisp] += 1 if (mdisp != 0 and len(lst) > 1) else 0
print('Q3e 各 mdisp 上"同组多表且非 0"的 COL 数:', dict(sorted(sub_exists.items())))
ck('Q3f 记录', True, {k: v for k, v in sorted(sub_exists.items()) if k in TIERS})

print(f'\n== SUMMARY ==\n  checks={N}  fails={len(fails)}')
if fails:
    for f in fails: print('  FAIL:', f)
json.dump({
    'cols': len(COL), 'vts': len(VT), 'slots': sum(NS.values()),
    'groups': len(group), 'multi': sum(1 for v in group.values() if len(v) > 1),
    'adj': len(adj), 'direct': len(direct), 'same_group_hit': same_group_hit,
    'uniq_addr': uniq_addr, 'shared2': shared2,
    'top': [[hex(a), c] for a, c in top],
    'direct_in_main': inq, 'pro2': pro.most_common(8),
    'self_attr': dict(attr_self), 'tier_attr': tier_attr,
    'bit0_by_tier': {k: dict(v) for k, v in bit0_by_tier.items()},
    'tier_counts': {t: len(tier_owner[t]) for t in TIERS},
    'tier_names': {t: sorted({n for _, n, *_ in tier_owner[t]}) for t in TIERS},
    'checks': N, 'fails': fails,
}, open(os.path.join(HERE, 'r191a.json'), 'w'), indent=1, ensure_ascii=False)
sys.exit(1 if fails else 0)
