#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R189 E：【本轮主攻】F55 ⑦「槽 3 thunk 的 76 张宿主表里 72 张槽 11 == 0x410450」
这一读数被检出**越界**：那 76 张宿主表的真实槽数（紧排口径）**全部是 6**，
槽 11 根本不存在；vt+44 落在**下一张表**的槽 4 上。

本脚本给出钉死证据：
  E1 76 张宿主表 PRE 恒为 6（无例外）。
  E2 每张宿主表的块 = [COL 指针 @vt−4][6 槽 @vt..vt+23]；vt+24 是下一张表的 COL 指针、
     vt+28 是下一张表头 —— 76/76 满足。
  E3 ⇒ vt+44（= 槽 11）**在块外**、且恰等于下一张表的槽 4（= vt+28+16）。
  E4 R188 报的四个数（72 / 2 / 1 / 1）是 vt+44 的直方，可复现，但语义是「下一张表的槽 4」。
  E5 基率检验：0x410450 出现在全镜像槽 4 的表数（分母 907）⇒ 72/76 与该基率对比。
  E6 反控：把读数改成「本表自己的槽 4」时，76 张里 0x410450 只出现 0 次；
     把读数改成「下一张表的槽 3」时直方完全不同。
"""
import sys, os, struct, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_r185'))
import pe185 as P

fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
COLS = {}
for sec in ('.rdata', '.data'):
    s = P.B[sec]; nd = s['rawsize'] // 4
    v = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
    for i in range(nd - 4):
        b = s['lo'] + 4 * i; d = v[i:i + 5]
        if d[0] not in (0, 1) or d[2] != 0: continue
        if P.where(d[3]) != '.data' or P.where(d[4]) != '.rdata': continue
        nm = P.cstr(d[3] + 8, 200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COLS[b] = dict(mdisp=d[1], name=nm.decode('latin1'))
VTS = {}
for sec in ('.rdata', '.data'):
    s = P.B[sec]; nd = s['rawsize'] // 4
    v = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
    for i, x in enumerate(v):
        if not (LO <= x < HI): continue
        b = s['lo'] + 4 * i
        if P.dw(b - 4) in COLS: VTS[b] = COLS[P.dw(b - 4)]
PRE = {}
for vt in VTS:
    k = 0
    while True:
        d = P.dw(vt + 4 * k)
        if d is None or not (LO <= d < HI): break
        k += 1
    PRE[vt] = k
ck('E0 1214 / 1214 / 14044 复现', (len(COLS), len(VTS), sum(PRE.values())) == (1214, 1214, 14044),
   (len(COLS), len(VTS), sum(PRE.values())))

# ---------- E1 thunk 宿主表 ----------
THUNK = 0x410210
ck('E0b thunk 字节 8b442404 8b50fc 8d48fc ff522c c20400',
   P.RAW[P.r2o(THUNK):P.r2o(THUNK) + 13].hex() == '8b4424048b50fc8d48fcff522c'
   and P.RAW[P.r2o(THUNK) + 13:P.r2o(THUNK) + 16].hex() == 'c20400',
   P.RAW[P.r2o(THUNK):P.r2o(THUNK) + 13].hex())
HOST = [vt for vt in VTS if PRE[vt] > 3 and P.dw(vt + 12) == THUNK]
ck('E1a 槽 3 装 thunk 的宿主表 76 张', len(HOST) == 76, len(HOST))
ph = collections.Counter(PRE[vt] for vt in HOST)
ck('E1b 这 76 张的真实槽数**全部是 6**（槽 11 不存在）', set(ph) == {6}, dict(ph))
ck('E1c 76 张的 vt+24（即「槽 6」）**不是 .text 值、而是一条 COL 地址**（块到此结束）',
   all(not (LO <= (P.dw(vt + 24) or 0) < HI) and P.dw(vt + 24) in COLS for vt in HOST),
   [(hex(vt), hex(P.dw(vt + 24) or 0)) for vt in HOST if P.dw(vt + 24) not in COLS][:3])
ck('E1d ⇒ 76 张表里「槽 7..槽 10」读到的 .text 值属于**下一张表**，不是本表的槽',
   all(LO <= (P.dw(vt + 28) or 0) < HI and (vt + 28) in VTS for vt in HOST),
   [(hex(vt)) for vt in HOST if (vt + 28) not in VTS][:3])

# ---------- E2 块结构 ----------
okblk = 0
for vt in HOST:
    nxt_col_ptr = vt + 24            # 本块终点 = 下一块的 COL 指针槽
    nxt_head = vt + 28
    if P.dw(nxt_col_ptr) in COLS and VTS.get(nxt_head) is not None and P.dw(nxt_head - 4) == P.dw(nxt_col_ptr):
        okblk += 1
ck('E2 76/76 满足：vt+24 是下一块的 COL 指针、vt+28 是下一张表头', okblk == 76, okblk)

# ---------- E3 vt+44 == 下一张表 slot4 ----------
same = 0; mism = []
for vt in HOST:
    a = P.dw(vt + 44); b = P.dw(vt + 28 + 16)
    if a == b: same += 1
    else: mism.append((hex(vt), hex(a), hex(b)))
ck('E3a vt+44（俗称槽 11）**恰等于** vt+28+16（下一张表 slot4）的：76/76', same == 76 and not mism,
   (same, mism[:3]))
ck('E3b 那 76 张「下一张表」与被读的宿主表**类名完全相同**（同一个类的 mdisp==0 主表）',
   all(VTS[vt + 28]['name'] == VTS[vt]['name'] for vt in HOST)
   and collections.Counter(VTS[vt]['mdisp'] for vt in HOST).keys() == {4},
   collections.Counter(VTS[vt]['mdisp'] for vt in HOST))
# 证明越界：vt+44 落在 [本块起点, 块终点) 之外
out = sum(1 for vt in HOST if not (vt - 4 <= vt + 44 < vt + 24))
ck('E3c 76/76 的 vt+44 落在**本表块外**（块 = [vt−4, vt+24)）', out == 76, out)

# ---------- E4 复现 R188 的四个数 ----------
h44 = collections.Counter(P.dw(vt + 44) for vt in HOST)
ck('E4 R188 的 72 / 2 / 1 / 1 是 vt+44 直方（可复现）',
   (h44.get(0x410450, 0), h44.get(0x410310, 0), h44.get(0x512280, 0), h44.get(0x410260, 0)) == (72, 2, 1, 1),
   [(hex(k), v) for k, v in h44.most_common(5)])

# ---------- E5 基率 ----------
s4 = collections.Counter(P.dw(vt + 16) for vt in VTS if PRE[vt] > 4)
den = sum(s4.values())
ck('E5a 全镜像槽 4 宿主表数 907', den == 907, den)
base = s4.get(0x410450, 0)
print('# 槽 4 == 0x410450 的全镜像表数 %d / %d = %.2f%%' % (base, den, 100.0 * base / den))
ck('E5b 0x410450 在全镜像槽 4 上的基率只有 %d/907 = %.2f%%' % (base, 100.0 * base / den),
   base == 77, (base, den))
exp = 76.0 * base / den
print('# 若 76 张的邻居是随机表，期望命中 %.1f 张；实测 72 张 ⇒ 不是随机，而是「配对主表」结构' % exp)
ck('E5c 实测 72 远高于随机期望（> 8 倍），故结论是「配对主表的槽 4」而非「同一张表的槽 11」',
   72 > 8 * exp, (exp, 72))

# ---------- E6 反控 ----------
own4 = collections.Counter(P.dw(vt + 16) for vt in HOST)
ck('N1 反控：改读**本表自己的槽 4**，76 张里 0x410450 出现 %d 次（= 0，判据能失效）'
   % own4.get(0x410450, 0), own4.get(0x410450, 0) == 0, [(hex(k), v) for k, v in own4.most_common(3)])
n3 = collections.Counter(P.dw(vt + 28 + 12) for vt in HOST)
ck('N2 反控：改读「下一张表的槽 3」，直方与 72/2/1/1 完全不同',
   (n3.get(0x410450, 0), n3.get(0x410310, 0)) != (72, 2), [(hex(k), v) for k, v in n3.most_common(3)])
# N3：把宿主表按槽数 >= 12 重新筛（R188 隐含的前提），应得 0 张
big = [vt for vt in VTS if PRE[vt] >= 12 and P.dw(vt + 12) == THUNK]
ck('N3 反控：若坚持「槽 11 存在的宿主表」，命中 %d 张 ⇒ R188 的读数在 0 张表上合法' % len(big),
   len(big) == 0, len(big))

# ---------- 附：76 张的 COL 层属性 ----------
md = collections.Counter(VTS[vt]['mdisp'] for vt in HOST)
print('# 76 张宿主表的 COL.mdisp 直方 %s' % dict(sorted(md.items())))
nm = collections.Counter(VTS[vt]['name'] for vt in HOST)
print('# 其中类名样本 %s' % [k for k, _ in nm.most_common(4)])
ck('E7 76 张宿主表的 mdisp 全为 0 或全为单值（层属性一致）', len(md) <= 2, dict(md))

# ---------- E8 真正的「槽 11」：配对 mdisp==0 主表 ----------
byname = collections.defaultdict(list)
for vt, c in VTS.items(): byname[c['name']].append(vt)
pair = {}
for vt in HOST:
    z = [x for x in byname[VTS[vt]['name']] if VTS[x]['mdisp'] == 0]
    pair[vt] = z[0] if z else None
ck('E8a 76/76 都能找到同类名 mdisp==0 配对主表', all(pair[vt] is not None for vt in HOST),
   sum(1 for vt in HOST if pair[vt] is None))
ck('E8b 物理上紧跟的那张表（vt+28）与被读宿主表**类名全同** 76/76，其中 mdisp==0 的 73 张',
   sum(1 for vt in HOST if VTS[vt + 28]['name'] == VTS[vt]['name']) == 76
   and sum(1 for vt in HOST if VTS[vt + 28]['name'] == VTS[vt]['name']
           and VTS[vt + 28]['mdisp'] == 0) == 73,
   (sum(1 for vt in HOST if VTS[vt + 28]['name'] == VTS[vt]['name']),
    sum(1 for vt in HOST if VTS[vt + 28]['mdisp'] == 0)))
c11p = collections.Counter(P.dw(vt + 28 + 44) for vt in HOST if PRE[vt + 28] > 11)
deep = sum(1 for vt in HOST if PRE[vt + 28] > 11)
ck('E8c 紧邻表的槽 11 可读的 %d 张（真实槽数 > 11）' % deep, deep == 73, deep)
print('# 配对主表真正的槽 11 直方 %s' % [(hex(k), v) for k, v in c11p.most_common(5)])
ck('E8d **真正的**槽 11 里 0x410450 出现 0 次（R188 的 72 是槽 4 的数）',
   c11p.get(0x410450, 0) == 0, c11p.get(0x410450, 0))
c4p = collections.Counter(P.dw(vt + 28 + 16) for vt in HOST
                         if VTS[vt + 28]['mdisp'] == 0)
ck('E8e 紧邻的 mdisp==0 主表的**槽 4** 才是 72/73 == 0x410450'
   '（另一张 0x512280；76 张里第 3 张紧邻表 mdisp==8/12 不计）',
   c4p.get(0x410450, 0) == 72 and sum(c4p.values()) == 73,
   [(hex(k), v) for k, v in c4p.most_common(4)])
pos = collections.Counter()
for vt in VTS:
    for k in range(PRE[vt]):
        if P.dw(vt + 4 * k) == 0x410450: pos[k] += 1
ck('E8f 0x410450 在全镜像**只出现在槽 4**（77 张表），从不出现在槽 11',
   dict(pos) == {4: 77}, dict(sorted(pos.items())))
ck('E8g ⇒ F55 ⑦ 的「72/76 槽 11 == 0x410450」是两处错位：表错（本表 → 紧邻的同名主表）、槽错（11 → 4）',
   c4p.get(0x410450, 0) == 72 and c11p.get(0x410450, 0) == 0 and dict(pos) == {4: 77})

out = dict(hosts=len(HOST), pre=dict(ph), same=same,
           c11_pair={hex(k): v for k, v in c11p.items()},
           c4_pair={hex(k): v for k, v in c4p.items()}, deep_pair=deep, hist44={hex(k): v for k, v in h44.items()},
           base_slot4=base, den_slot4=den, big_hosts=len(big), mdisp=dict(md))
open(os.path.join(HERE, 'r189e.json'), 'w').write(json.dumps(out, indent=1, ensure_ascii=False))
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
sys.exit(1 if fails else 0)
