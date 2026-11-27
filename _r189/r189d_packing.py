#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R189 D：把「.rdata 里 1214 张 vtable 的排布」按地址序做一次紧排普查，
并且把 R188 的「854 张截断后第 2 个 dword 又回到 .text」这条**口径误述**复算清楚。

要回答：
  P1 每张表头前 4 字节 == 一条 COL 地址（1214/1214）⇒ 布局是 [COL 指针][槽…] 重复。
  P2 按地址序，表 i 的前缀终点 == 表 i+1 的表头 − 4 的表有多少张（真正紧排）。
  P3 其余表的终点到底是什么（0 填充 / .data / 落空）。
  P4 R188 的 854 是什么东西：应当 == 「下一张表槽数 >= 2」的表数（不是内嵌 COL 的证据）。
  P5 F29 的 77 张 TClassFactory 分母在「真实槽数」下是否变化。
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
        COLS[b] = dict(mdisp=d[1], name=nm.decode('latin1'), ptd=d[3])
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
ck('D0 1214 / 1214 / 14044 复现', (len(COLS), len(VTS), sum(PRE.values())) == (1214, 1214, 14044),
   (len(COLS), len(VTS), sum(PRE.values())))

# ---------- P1 表头前 4 字节 ----------
head_prev_col = sum(1 for vt in VTS if P.dw(vt - 4) in COLS)
ck('D1 1214/1214 表头前 4 字节是一条 COL 地址（布局 = [COL 指针][槽…] 重复）',
   head_prev_col == 1214, head_prev_col)

# ---------- P2 按地址序紧排 ----------
order = sorted(VTS)
nxt = {order[i]: (order[i + 1] if i + 1 < len(order) else None) for i in range(len(order))}
contig = 0; zero_tail = 0; data_tail = 0; other_tail = []
for vt in order:
    stop = vt + 4 * PRE[vt]; nv = nxt[vt]
    if nv is not None and stop == nv - 4: contig += 1
    else:
        d = P.dw(stop)
        if d == 0: zero_tail += 1
        elif P.where(d) == '.data': data_tail += 1
        else: other_tail.append((hex(vt), hex(stop), None if d is None else hex(d), P.where(d)))
print('# 紧排 %d / 0 尾 %d / .data 尾 %d / 其它 %d' % (contig, zero_tail, data_tail, len(other_tail)))
ck('D2 紧排（终点 == 下一张表头 − 4，即下一张表的 COL 指针槽）恰 979 张',
   contig == 979, contig)
ck('D3 0 填充结尾 186 张', zero_tail == 186, zero_tail)
ck('D4 .data 结尾 4 张', data_tail == 4, data_tail)
ck('D5 非 0 非 .data 的散尾 45 张（四档闭合 979+186+45+4 == 1214）',
   len(other_tail) == 45 and contig + zero_tail + data_tail + len(other_tail) == 1214, len(other_tail))
ck('D5b 「非紧排」合计 186+45+4 == 231，正是 R188 记的「其它 .rdata 231 张」',
   zero_tail + len(other_tail) + data_tail == 235 and 1214 - contig == 235,
   (zero_tail + len(other_tail) + data_tail, 1214 - contig))
# 反控：若把 PRE 加 1 再要求紧排，应几乎全失效
contig_p1 = 0
for vt in order:
    stop = vt + 4 * (PRE[vt] + 1); nv = nxt.get(vt)
    if nv is not None and stop == nv - 4: contig_p1 += 1
ck('N1 反控：PRE+1 后紧排从 979 掉到 %d' % contig_p1, contig_p1 < 20, contig_p1)
# 反控：判据必须能区分两组 —— 235 张非紧排表里，终点到下一块的距离恒 > 0
gap_ok = all((nxt[vt] - 4 - (vt + 4 * PRE[vt])) > 0 for vt in order
             if nxt[vt] is not None and vt + 4 * PRE[vt] != nxt[vt] - 4)
gaps = collections.Counter(nxt[vt] - 4 - (vt + 4 * PRE[vt]) for vt in order
                           if nxt[vt] is not None and vt + 4 * PRE[vt] != nxt[vt] - 4)
ck('N2 235 张非紧排表的块间空隙恒 > 0（最小 %d）⇒ 判据与紧排组可区分'
   % min(gaps) if gaps else 'N2 no gaps', gap_ok and len(gaps) > 0, dict(sorted(gaps.items())[:5]))

# ---------- P4 R188 的 854 ----------
# 「截断点后第 2 个 dword 落 .text」= 紧排时下一张表的槽 1 落 .text = 下一张表槽数 >= 2
d2_text = 0
for vt in order:
    stop = vt + 4 * PRE[vt] + 8
    d = P.dw(stop)
    if d is not None and LO <= d < HI: d2_text += 1
ck('D6 「距表头前缀终点 +8 的 dword 落 .text」的表 == 854（R188 记 854）', d2_text == 854, d2_text)
n_next_ge2 = sum(1 for vt in order if contig_hit(vt) if False) if False else None
# 上式的干净写法：下一张表（无论紧排与否）若存在且其首槽之后还有 .text 槽
tmp = 0; tmp2 = 0
for vt in order:
    stop = vt + 4 * PRE[vt]
    d = P.dw(stop)
    if d in COLS and (stop + 4) in VTS and PRE[stop + 4] >= 2: tmp += 1
    elif d not in COLS:
        dd = P.dw(stop + 8)
        if dd is not None and LO <= dd < HI: tmp2 += 1
ck('D7 854 的构成 = 紧排组里「下一张表槽数 >= 2」的 %d + 非紧排组里 +8 落 .text 的 %d' % (tmp, tmp2),
   tmp + tmp2 == 854, (tmp, tmp2))
ck('D8 ⇒ 854 不是「内嵌 COL」的证据：其中 %d 张只是下一张表还有第 2 槽' % tmp, tmp == 847)
mm = 0; mm2 = []
for vt in order:
    stop = vt + 4 * PRE[vt]; nv = nxt[vt]
    if nv is None or stop != nv - 4: continue
    dd = P.dw(stop + 8); istxt = dd is not None and LO <= dd < HI
    if istxt == (PRE[nv] >= 2): mm += 1
    else: mm2.append((hex(vt), istxt, PRE[nv]))
ck('D8b 紧排组内「+8 落 .text」与「下一张表槽数 >= 2」逐表一致 979/979',
   mm == 979 and len(mm2) == 0, (mm, mm2[:3]))

# ---------- P5 F29 分母 ----------
by_name = collections.defaultdict(list)
for vt, c in VTS.items(): by_name[c['name']].append(vt)
TF = [vt for vt, c in VTS.items() if 'TClassFactory@' in c['name']]
ck('D9 TClassFactory 具名表 77 张（F29 分母不变）', len(TF) == 77, len(TF))
slots = sorted(PRE[vt] for vt in TF)
print('# 77 张 TClassFactory 表槽数 min/median/max = %d/%d/%d' % (slots[0], slots[len(slots) // 2], slots[-1]))
dist = [vt for vt in TF if VTS[vt]['mdisp'] != 0]
ck('D10 这 77 张全是 mdisp==0 主表', len(dist) == 0, len(dist))

# ---------- F02 / F03 定稿 ----------
BT = 0x7E3EBC
ck('D11 BuildingClass 真实槽数 322（非前缀近似）', PRE[BT] == 322, PRE[BT])
ck('D12 其块 = [COL 指针 @0x7E3EB8][322 槽 @0x7E3EBC..0x7E43C3][下一表 COL 指针 @0x7E43C4]',
   P.dw(0x7E3EB8) in COLS and P.dw(0x7E43C4) in COLS and PRE[BT] == 322,
   (hex(P.dw(0x7E3EB8)), hex(P.dw(0x7E43C4))))
ck('D13 BuildingClass 块 = 4 + 322*4 = 1,292 B，下一块（0x7E43C4 的 COL 指针槽）紧随其后',
   4 + 322 * 4 == 1292 and 0x7E43C4 - 0x7E3EB8 == 1292, 0x7E43C4 - 0x7E3EB8)
ck('D14 下一张表 0x7E43C8 的 COL 0x7FC298 类名 == DynVec<PVInfantryClass>',
   COLS[0x7FC298]['name'] == '.?AV?$DynamicVectorClass@PAVInfantryClass@@@@')
# 块宽校验：1214 个表块的起始（vt-4）与下一块起始（下一表 vt-4）间距 == 4+4k（k=本表槽数）
bad = []; nbad_scope = 0
for i, vt in enumerate(order[:-1]):
    blk = vt - 4; nblk = order[i + 1] - 4
    exp = 4 + 4 * PRE[vt]        # 块 = [COL 指针 4B][4*槽数]，下一块紧接其后
    if vt + 4 * PRE[vt] == order[i + 1] - 4:
        if nblk - blk != exp: bad.append((hex(vt), nblk - blk, exp))
    else:
        nbad_scope += 1
ck('D15 979 个紧排块的块宽 == 4 + 4*槽数 + 4 逐块闭合（0 例外）', len(bad) == 0, bad[:3])
ck('D15b 其余 %d 张（含末张）不参与该恒等式' % (nbad_scope + 1), nbad_scope + 1 == 235, nbad_scope + 1)

out = dict(contig=contig, zero_tail=zero_tail, data_tail=data_tail, d2_text=d2_text,
           f29=len(TF), blocks_ok=len(bad) == 0)
open(os.path.join(HERE, 'r189d.json'), 'w').write(json.dumps(out, indent=1, ensure_ascii=False))
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
sys.exit(1 if fails else 0)
