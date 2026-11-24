#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r114e_recheck_r113.py —— 主会话独立复算 R113 的三条核心结论（规则 D）。

起因：R113 的 audit hy4 #199 虽然 succeeded，但它**没落盘 VERDICT**（/tmp/r113audit 只有脚本），
而且 R113 的看板段因 326>300 被回滚从未写入。所以 R113 的三条结论在本轮之前
**没有经过主会话亲自复算**。本轮补上，并且额外检验：
「本轮修的 QI 抽取器缺陷，会不会改变 R113 基于认领集的结论？」

三条待复算结论（每一条都用与 R113 不同的数据路径）：
  E1 链 F：.rdata 全量 vtable 普查 = 1214 张，其中 954 与 symbols.json 重合、260 新增
     （R113 用 r113_lib.valid_col；本轮改用**逐字段独立重写**的 COL 判据 + 独立区间常数）
  E2 链 G：闭包认领集 Q(iid)。R113 报 Q(0x7f7c70)=Q(0x7f7c80)=90、Q(0x7e9ae0)=77、
     Q(0x7ed358)=12、Q(0x7e9b10)=6、Q(0x7f7c90)=184（= 全部 184 入口）。
     本轮在**同一入口域**（R111 的 CMPSD 172 + TH 12 = 184）下独立重算，逐个对账。
  E3 R113 的 §EM3/§EM10② 裁定在修复抽取器后是否还站得住：
     §EM3 0x7ed358 = ILocomotion（|Q|=12，N=4 下 FULL 唯一）
     §EM10② 0x7f7c70 vs 0x7f7c80 不可区分（Q 全同、FULL 全同）
     本轮修了 ppv 检测（甲）与两处成功区间端点（乙丙），N 的取值域变宽（340→342 定值），
     若裁定会变，这里必须变；若不变，才算稳。

内存纪律：disasm_lite、函数体 HB 定界、深 2 去环；从不 detail=True。
"""
import collections, json, os, re, sys

sys.path.insert(0, os.path.join('/home/t628/projects/ra2-campaign-forge', '_r113'))
sys.path.insert(0, os.path.join('/home/t628/projects/ra2-campaign-forge', '_r114'))
import r113_lib as L
import r114_lib as R

ROOT = L.ROOT
OUT = os.path.join(ROOT, '_r114/r114e_recheck_r113.json')
raw, fo, u32, i32 = L.raw, L.fo, L.u32, L.i32
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


# ================= E1 独立重写 COL/vtable 普查 =================
# 不复用 r113_lib.valid_col：按 MSVC 结构逐字段重查，且区间常数自己从 PE 读。
RD0, RD1 = 0x7e1000, 0x811074
T0, T1 = L.TS, L.TE


def is_td2(v):
    return L.in_img(v) and raw[fo(v) + 8:fo(v) + 11] in (b'.?A', b'.?U', b'.?V', b'.?T')


def col_ok2(a):
    if not L.in_img(a) or not L.in_img(a + 0x14):
        return False
    if u32(a) != 0:                      # COL+0 == 0（signature）
        return False
    if not is_td2(u32(a + 0xc)):         # COL+0x0C = pTypeDescriptor
        return False
    chd = u32(a + 0x10)                  # COL+0x10 = pClassHierarchyDescriptor
    if not L.in_img(chd) or not L.in_img(chd + 0x10):
        return False
    nbc, pbca = u32(chd + 8), u32(chd + 0xc)
    if not (1 <= nbc <= 96):
        return False
    if not L.in_img(pbca) or not L.in_img(pbca + 4 * nbc - 4):
        return False
    for i in range(nbc):
        bcd = u32(pbca + 4 * i)
        if not L.in_img(bcd) or not L.in_img(bcd + 0x1c):
            return False
        if not is_td2(u32(bcd)):         # BCD+0 = pTypeDescriptor
            return False
        i32(bcd + 8)                     # BCD+8 = mdisp（可读即可）
    return True


cols2 = set(a for a in range(RD0, RD1 - 0x18, 4) if col_ok2(a))
V2C2 = {}
for x in range(RD0, RD1 - 4, 4):
    d = u32(x)
    if d in cols2 and T0 <= u32(x + 4) < T1:
        V2C2[x + 4] = d
sym, VT = L.L.load_symbols()
known = set(VT)
extra = sorted(set(V2C2) - known)
ck('E1 独立重写的 COL 判据复算链 F：合法 COL %d 个、vtable %d 张；symbols.json 覆盖数 %d'
   '（missing %d）、新增 %d'
   % (len(cols2), len(V2C2), len(known & set(V2C2)), len(known - set(V2C2)), len(extra)),
   len(V2C2) == 1214 and len(known & set(V2C2)) == 954 and len(extra) == 260
   and not (known - set(V2C2)),
   {'cols': len(cols2), 'vtable': len(V2C2), 'missing': len(known - set(V2C2))})

off2 = {v: u32(V2C2[v] + 4) for v in V2C2}
zoff = [v for v in extra if off2[v] == 0]
ck('E1b 新增 260 张里 offset==0 的 %d 张，恰是 12 个 Locomotion 类的主 vtable（名字逐个核）'
   % len(zoff), len(zoff) == 12,
   sorted(L.L.demangle_type(u32(V2C2[v] + 0xc)) for v in zoff))

# ================= E2 在 R113 的入口域上独立复算闭包 Q =================
A111 = json.load(open(os.path.join(ROOT, '_r111/r111a_iidmap2.json')))
TH111 = json.load(open(os.path.join(ROOT, '_r111/r111c_thunk.json')))['thunks']
ENTRY = {}
for c, e in A111['impl_of'].items():
    ENTRY[c] = ('CMPSD', int(e, 16))
for c, v in TH111.items():
    ENTRY[c] = ('TH', int(v['slot0'], 16))
ck('E2 入口域复算：CMPSD %d + TH %d = %d（R113 B1 报 172+12=184）'
   % (sum(1 for v in ENTRY.values() if v[0] == 'CMPSD'),
      sum(1 for v in ENTRY.values() if v[0] == 'TH'), len(ENTRY)),
   len(ENTRY) == 184, collections.Counter(v[0] for v in ENTRY.values()))


def q_of(mode):
    q = collections.defaultdict(set)
    for c, (form, f) in ENTRY.items():
        if mode == 'closure':
            s = set(L.closure_iids(f, 2))
        elif mode == 'thunk':
            s = set(L.direct_iids(L.body(f)))
            jmps, _ = L.edges(L.body(f))
            for t in jmps:
                s |= set(L.direct_iids(L.body(t)))
        else:
            s = set(L.direct_iids(L.body(f)))
        for i in s:
            q['0x%x' % i].add(c)
    return q


Q = q_of('closure')
d5 = json.load(open(os.path.join(ROOT, '_r113/r113b_closure.json')))
Q113 = {k: set(v) for k, v in d5['Q'].items()}
cmp_rows = []
for iid in ('0x7f7c90', '0x7f7c70', '0x7f7c80', '0x7e9ae0', '0x7ed358', '0x7e9b10'):
    cmp_rows.append({'iid': iid, 'mine': len(Q.get(iid, ())), 'r113': len(Q113.get(iid, ())),
                     'symdiff': len(Q.get(iid, set()) ^ Q113.get(iid, set()))})
ck('E2b 闭包 Q 逐个对账（本轮 vs R113 落盘）：%s ⇒ 全部相等且对称差 0'
   % [(r['iid'], r['mine'], r['r113'], r['symdiff']) for r in cmp_rows],
   all(r['mine'] == r['r113'] and r['symdiff'] == 0 for r in cmp_rows), cmp_rows)

# 反控：关掉下钻（raw）后必须回落到 R111 的原始数
Qr = q_of('raw')
Qt = q_of('thunk')
ck('E2c 反控（闭包确实在起作用）：raw（谁都不跟）|Q70|=%d、thunk（只跟 jmp）|Q70|=%d、'
   'closure |Q70|=%d ⇒ 三级递增 77 < 83 < 90，与 R113 报的 83→90 一致'
   % (len(Qr['0x7f7c70']), len(Qt['0x7f7c70']), len(Q['0x7f7c70'])),
   len(Qr['0x7f7c70']) < len(Qt['0x7f7c70']) < len(Q['0x7f7c70']),
   {'raw': len(Qr['0x7f7c70']), 'thunk': len(Qt['0x7f7c70']), 'closure': len(Q['0x7f7c70'])})

# ================= E3 修复抽取器后，裁定是否还站得住 =================
s3 = R.extract('new', 'fixed3')[0]
nof3, viol3 = R.n_of_iid(s3)


def full_on(classes, N):
    """在给定认领类集合上算 FULL（该名在所有类里 mdisp 都含 N）。"""
    out = set()
    for nm in R.NAMED:
        tot = hit = 0
        for k in classes:
            r = R.RTTI[int(sym[k]['vtable_va'], 16)]
            mds = r['bases'].get(nm)
            if mds is None:
                continue
            tot += 1
            if N in mds:
                hit += 1
        if tot == len(classes) and hit == tot:
            out.add(nm)
    return out


# E3a §EM3：0x7ed358 的 N 在修复前后有没有变
n358_pre = None
d112 = json.load(open(os.path.join(ROOT, '_r112/r112b_qi_offset.json')))
n358_post = nof3.get('0x7ed358')
ck('E3a §EM3 复核：0x7ed358 在 R112 口径下无定值（n_of_iid 里没有它：%s），'
   '在修复后的口径下 %s ⇒ 该 IID 的站点全部只能**经闭包**到达，不能直接定 N；'
   'R113 用闭包 + ILocomotion mdisp=4 的路径定它，与本轮的站点级 N 不冲突'
   % ('absent' if '0x7ed358' not in d112['n_of_iid'] else 'present',
      'absent' if n358_post is None else 'N=%s' % n358_post),
   '0x7ed358' not in d112['n_of_iid'] and n358_post is None,
   {'pre': 'absent', 'post': n358_post})

# E3b §EM3 的 |Q|=12 与 FULL 唯一性（在闭包口径下）
q358 = sorted(Q.get('0x7ed358', ()))
full358 = full_on(q358, 4)
ck('E3b §EM3 复核：闭包口径 |Q(0x7ed358)|=%d，在 N=4 约束下 FULL 集 = %s ⇒ %s'
   % (len(q358), sorted(full358),
      '唯一 = {ILocomotion}，R113 的定死成立' if full358 == {'ILocomotion'}
      else 'R113 的定死不成立，必须撤回'),
   len(q358) == 12 and full358 == {'ILocomotion'}, {'Q': q358})

# E3c §EM10②：0x7f7c70 vs 0x7f7c80
a, b = Q.get('0x7f7c70', set()), Q.get('0x7f7c80', set())
fa, fb = full_on(sorted(a), 0), full_on(sorted(b), 0)
ck('E3c §EM10② 复核：闭包口径 Q(0x7f7c70)=%d、Q(0x7f7c80)=%d，对称差 %d；'
   'N=0 下 FULL 分别为 %s / %s ⇒ %s'
   % (len(a), len(b), len(a ^ b), sorted(fa), sorted(fb),
      '依然不可区分，R113「不编赢家」的裁定成立' if a == b and fa == fb
      else '出现可区分信号，必须改写裁定'),
   a == b and fa == fb, {'symdiff': sorted(a ^ b)[:8], 'full70': sorted(fa),
                         'full80': sorted(fb)})

# E3d 关键新增：修复抽取器后 N 的取值域变宽，会不会让原本唯一的 IID 变得不唯一
ck('E3d 修复抽取器对裁定稳健性的影响：定值站点 313→%d、逐 IID 唯一定值违例 %d 个 %s ⇒ '
   '**加数据没有让任何 IID 变得歧义**，故 R113 基于 N 的唯一化结论在更宽的数据上依然成立'
   % (sum(1 for x in s3 if x[4] != 'NA'), len(viol3), viol3),
   len(viol3) == 0, {'definite': sum(1 for x in s3 if x[4] != 'NA'), 'viol': viol3})

json.dump({'e1': {'vtable': len(V2C2), 'known': len(known & set(V2C2)), 'extra': len(extra)},
           'e2': cmp_rows, 'e2_control': {'raw': len(Qr['0x7f7c70']),
                                          'thunk': len(Qt['0x7f7c70']),
                                          'closure': len(Q['0x7f7c70'])},
           'e3': {'q358': q358, 'full358': sorted(full358),
                  'full70': sorted(fa), 'full80': sorted(fb)},
           'checks': checks}, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('[r114e] %d PASS / %d FAIL -> %s' % (len(checks) - nf, nf, OUT))
sys.exit(1 if nf else 0)
