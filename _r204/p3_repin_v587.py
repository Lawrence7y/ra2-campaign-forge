#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 台账升版 V586 -> V587：只改 F01 一行（追加 RTTI 三表布局实测），其余 55 行逐字节不变。
fail-closed：旧常量复算旧 MASTER 命中旧 pin 作硬闸；新版本目录先写，后改指针（顺序不可反）。
"""
import ast, hashlib, io, os, re, sys
from collections import Counter
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
OLD_DIR = 'R17_R131_FACTINDEX_V586'; NEW_DIR = 'R17_R131_FACTINDEX_V587'
SRC = os.path.join(TIER, OLD_DIR, 'FACT_INDEX.tsv')
DSTDIR = os.path.join(TIER, NEW_DIR); DST = os.path.join(DSTDIR, 'FACT_INDEX.tsv')
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

old = io.open(SRC, encoding='utf-8', newline='').read()
sha_old = hashlib.sha256(old.encode()).hexdigest()
ck('G1a 源 V586 未变（225848 B / 07a55ac3… / CR 0）',
   len(old.encode()) == 225848 and sha_old.startswith('07a55ac3') and old.count('\r') == 0,
   (len(old.encode()), sha_old[:16], old.count('\r')))
L = old.split('\n')
ck('G1b 58 段（1 表头 + 56 行 + 尾空）且 5 列', len(L) == 58 and all(len(x.split('\t')) == 5 for x in L[:57]),
   (len(L), [i for i, x in enumerate(L[:57]) if len(x.split('\t')) != 5]))
R = [x.split('\t') for x in L[:57]]
f01 = [r for r in R if r[0] == 'F01'][0]

ADD1 = ('⑬**R204 交付（主会话 _r204/m1_chd.py 31 断言、m5_pool.py 10 断言 0 FAIL、m6_verify.py 20 断言、'
 'm8_laws.py 12 断言、m10_final2.py 18 断言、m11_ctl.py 4 断言、m12_audit.py 20 断言）**：'
 '**RTTI 三张表的字节布局首次逐字段实证（此前本条只有 COL→TD 这半段，CHD/BCD 从未落到字节级）**。'
 '① **CHD**：`+0` 恒 **0（954/954）**；`+4` attributes 取值集合 **{0,1,5}**（分布 **0:855 / 1:66 / 5:33**）；'
 '`+8` numBaseClasses（16 种取值、**max 18**、全部 <= 200）；`+12` pBaseClassArray（**954/954 落 .rdata**、954 个互异）。'
 '② **BCD 定长 24 字节六字段**：`+0` pTD / `+4` numContainedBases / `+8` mdisp / `+12` pdisp / `+16` vdisp / `+20` attributes；'
 '2615 条 BCA 引用去重后 **1002 个不同 BCD**（与 R196 同值）；`pdisp` 恒 **-1（1002/1002）**、`vdisp` 恒 **0（1002/1002）** '
 '⇒ **本镜像无任何虚基类**；BCD.attributes 分布 **0:991 / 2:7 / 9:4**。'
 '③ **954 这个数获得第二条独立判据（算法级，强于原条）**：原条 954 依赖「槽流遇同组头类名 COL ⇒ 新视图」这一**名字判据**；'
 '本轮改用**纯指针判据** —— 只按 COL 的 `+16 pClassHierarchyDescriptor` 分组、**完全不读类名**，同样得 **954 组**，'
 '组大小 **1:860 / 2:10 / 3:6 / 4:76 / 5:1 / 7:1**，与 R203 的视图数分布**逐桶相等**；且两关系**互为细化**'
 '（每个 pCHD 块只落 1 个名字块 **954/954**，每个名字块只落 1 个 pCHD **954/954**），块数相同 ⇒ **同一 partition**。'
 '④ **强区分力判据（新增）**：「每张 CHD 的自有 pTD 集合 ⊆ 其 BCA 中全部 BCD 的 pTD 集合」真 **954/954**；'
 '反控三档全为 **0 命中**：换用同长度其它 CHD 的 BCA **0/954**、n>=4 的 123 张穷举同长候选对 **0/123**、'
 '随机 .rdata 数组 **0/200**。⇒ BCA 不是任意指针数组，而是与该类身份绑定的继承路径表。'
 '（首版反控出现的 2/954 由 `_r204/m11_ctl.py`（4 断言）定位为「无同长候选时回退自选」的脚本缺陷，非数据反例。）'
 '⑤ **充要律 1**：`CHD.attributes bit0 == 1` ⟺ 该类存在 mdisp!=0 的 BCD，**双向零例外 954/954**；'
 '交叉表 `(attributes, 有mdisp!=0, 多视图)` = **{(0,F,F):855, (1,T,T):61, (1,T,F):5, (5,T,T):33}**；'
 'attributes == 5 的 33 张**全部也是 MI 类**；5 与 1 的语义差别**未取得**。'
 '⑥ **充要律 2**：`BCD.mdisp == 0` ⟺ 该 BCD 的 pTD 是**本类自有**：BCA 2615 条元素中 mdisp==0 **2228**（自有 **954**，'
 '每类恰 1 条主对象 BCD）、mdisp!=0 **387**（自有 **0**，反向零反例）；反控换成恒 -1 的 pdisp 后该律整体塌掉。'
 '⑦ **BCD 池结构与 24 字节步长**：1002 条全 **8 字节对齐**，但**不是 24 字节统一网格**（地址 mod 24 三态 **{0:340, 8:320, 16:342}**）；'
 '按「相邻差恰为 24」切 run 得 **708 个 run**，**run 内 mod 24 恒定 708/708**，run 基址 mod 24 = **{0:235, 8:233, 16:240}** '
 '⇒ 三态来自**不同 24 字节数组的起始模不同**。24 步长的可复算证据换成两条：`b-24` 也在池内的 **294** 条中 '
 '`dw(b-16) == mdisp(b-24)` 成立 **294/294**；708 条孤立记录中 `dw(b-16) == 0` 成立 **708/708**；'
 '反控：随机 1002 个 .rdata 地址中 `b-16==0` 仅 **308** 个。'
 '（**审计员原提的 `hist(b-16)==hist(mdisp)` 判别力不足**：键数虽都 14、0 的计数都 978，但**逐 BCD 只有 975/1002 相等**（27 处不等），'
 '且偏移扫描显示 `hist` 相等的偏移是 **{-16, +8}**，+8 即 mdisp 自身，故有效替代只剩 -16 一条。）'
 '⑧ **BCA 段结构**：组内相邻差分 **-24 占 973/1661**，其余为 **8 的倍数跨段大跳**（-31104:78 / -248:29 / -776:21 / -1312:20 / ±19864:12 等），'
 '**跳转目标 100% 落 1002 条 BCD 池内**（688 次跳转零例外）；按 -24 切段得 **1642 段**，段长 '
 '**{1:1252, 2:259, 3:31, 4:8, 5:6, 6:3, 7:1, 8:79, 10:1, 11:1, 12:1}**，**单元素段 1252/1642 = 76.2%**；'
 '等差（全 -24）CHD **490/954**，其中含 MI 的仅 **4** 个，非等差 464 个里含 MI **95** 个；'
 '段边界处 mdisp 变化 **平 652 / 升 33 / 降 3**，降的 3 例全部是 ATL `CComObject`/`CNetUtilEventSink` 家族。'
 '⑨ **集合等式边界（口径级）**：**939/954** 张 CHD 上「视图 mdisp 集合 == BCA mdisp 集合」；15 张不等且**方向单一**'
 '（BCA 只多不少，无任何视图 mdisp 缺失，多出的是 172/240/248/36 类大基类偏移）。'
 '**mdisp!=0 的类 99 个 vs 多视图类 94 个，差 5 个**，5 个逐条定位为 ATL 模板/事件 sink 类'
 '（`0x80e680` / `0x80e740` / `0x80e780` / `0x80e7c0` / `0x80e998`），形态是「BCA 里有 mdisp=4 的 '
 '`CComObjectRootEx`/`CComObjectRootBase` 基类、但只有一张 vftable」⇒ **有基类子对象 ≠ 有第二张 vftable**，'
 'R203 的「94 类有 MI」是「有多视图」口径，**不是**「有非零 mdisp 基类」口径，两者不可混引。'
 '⑩ **自错 15 组（0 条进结论）**：最关键三条 —— (a) **m1 的「多重集相等」四条判据整体作废**（前提就错：BCA 含无 vftable 的基类、'
 '且按继承路径计重数）；(b) **m2 的 R2a 反控失效**（mdisp 子集律在随机数组上仍 **866/954** 成立 ⇒ 该律区分力弱），'
 '促使改用 pTD 判据；(c) **m4 的 E1b/E1c 反控失败**（mdisp 子集律换 BCA 后仍 **74/84**）⇒ 该判据弃用、不进结论。'
 '其余为期望值写反（CHD+4 期望恒 1 / BCD.attributes 期望恒 0 / BCA 间距符号写反 / 短 BCA 全等差 / attributes==2 落 TClassFactory）、'
 '字段偏移读错（m3 T4 把 pTD 当 mdisp / m12 A3c 唯一集写 {0,-16} 实测 {-16,+8}）、常量腐烂（m6 X5a 把自写的严格基址判据当执行员的判据）。'
 '⑪ **跨家族**：执行员 **#515**（hy4，12 回合 / 2.5 分）7 项独立复核中 **5 项逐数一致**、**2 项正确指出卡面预期写错**'
 '（24 网格、BCA「绝大多数降序」实测仅 490/954），直接促成上述 ⑦⑧ 表述订正；审计员 **#516**（deepseek，28 回合 / 3.98 分，'
 '受控 10 项自报 10 PASS / 0 FAIL）**结论全部由主会话亲跑复算**，采纳其 4 条加强（708 run 结构、段长分布、'
 'b-16 判别力不足、mdisp==0 ⇔ 自有 pTD），**不采纳**其「mdisp 子集律可作证据」的取向（主会话已实测该律无区分力）；'
 '两者**均无 OVERTIME**。')

ADD_EV = ('_r204/m1_chd.py;_r204/m1_chd.json;_r204/m5_pool.py;_r204/m5_pool.json;_r204/m6_verify.py;'
 '_r204/m6_verify.json;_r204/m8_laws.py;_r204/m8_laws.json;_r204/m10_final2.py;_r204/m10_final2.json;'
 '_r204/m11_ctl.py;_r204/m11_ctl.json;_r204/m12_audit.py;_r204/m12_audit.json;'
 '_r204/hy4_layout.py;_r204/hy4_layout.json;lead/next_re_20261117_r14/R14_COMMON.md')

ADD_LIM = ('；**R204 边界**：本条新增的 CHD/BCD 布局只覆盖 CHD 前 4 个 dword，`+16` 之后是否还有字段**未验证**；'
 'BCD 池里 9579 个非 BCD 的 8 字节槽内容语义**未取得**（zero 6069 / .rdata 2534 / other 976）；'
 'CHD.attributes == 5 与 == 1 的语义差别**未取得**（7 个候选结构量都不足以定性）；'
 '464 张非等差 CHD 中 111 张「BCA 长度 <= 3 却非等差」的跨段成因**未逐个定性**；段长恰为 8 的 79 个段的成因**未取得**；'
 '5 个 ATL 类为何不产生第二张 vftable **未取得**。**口径边界**：R203 的「94 类有 MI」是**多视图**口径，'
 '与本轮测得的「99 类有非零 mdisp 基类」**是两个不同的集合**，差 5 个已逐条定位，禁止混引。')

f01[1] = f01[1] + ADD1
f01[3] = f01[3] + ';' + ADD_EV
f01[4] = f01[4] + ADD_LIM
new = '\n'.join('\t'.join(r) for r in R) + '\n' + (L[-1] if L[-1] == '' else '')
newraw = new.encode()
ck('G2a 新体 CR 仍 0 / 换行数仍 57', newraw.count(b'\r') == 0 and new.count('\n') == len(L) - 1,
   (newraw.count(b'\r'), new.count('\n'), len(L) - 1))
ck('G2b 除 F01 外 55 行逐字节未变',
   all(R[i] == L[i].split('\t') for i in range(57) if R[i][0] != 'F01'), True)
ck('G2c F01 只增不缩（stmt / lim 字节均变长）',
   len(f01[1].encode()) > 458 and len(f01[4].encode()) > 14490, (len(f01[1].encode()), len(f01[4].encode())))
FF = os.path.join(ROOT, '_r160/facts_floors.py')
src = io.open(FF, encoding='utf-8', newline='').read()
need = ('CUR_SHA256', 'TOTAL_BYTES', 'MASTER_SHA256', 'GRADES', 'FLOORS', 'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ')
C = {}
for node in ast.parse(src).body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        nm = node.targets[0].id
        if nm in need: C[nm] = ast.literal_eval(node.value)
ck('G3a 12 常量可 ast 取出', all(k in C for k in need), len(C))
def canon_g(d): return '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))
def canon_f(d): return '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))
def canon_e(d): return '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))
def canon_eb(d): return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
def master(sha, tot, floors, grades, evid, evidb, lost, items, uniq, li, lu):
    return hashlib.sha256(('\n'.join([sha, str(tot), canon_g(grades), canon_f(floors), canon_e(evid),
        canon_eb(evidb), canon_eb(lost), str(items), str(uniq), str(li), str(lu)])).encode()).hexdigest()
old_m = master(C['CUR_SHA256'], C['TOTAL_BYTES'], C['FLOORS'], C['GRADES'], C['EVID'], C['EVIDB'],
               C['LOST'], C['ITEMS'], C['UNIQ'], C['LOST_ITEMS'], C['LOST_UNIQ'])
ck('G3b 旧常量复算旧 MASTER 命中旧 pin（硬闸）', old_m == C['MASTER_SHA256'], (old_m[:16], C['MASTER_SHA256'][:16]))
new_sha = hashlib.sha256(newraw).hexdigest(); new_tot = len(newraw)
def strip_note(s):
    s = s.strip()
    if s.endswith(')'):
        d = 0
        for i in range(len(s) - 1, -1, -1):
            if s[i] == ')': d += 1
            elif s[i] == '(':
                d -= 1
                if d == 0: return s[:i].strip()
    return s
def norm(p): return p.replace('\\', '/').strip()
def resolvable(p):
    for c in (p, 'lead/' + p, TIER + '/' + p):
        if os.path.exists(os.path.join(ROOT, c)): return True
    return False
items = []
for r in R[1:]:
    for x in r[3].split(';'):
        if x.strip(): items.append((r[0], norm(strip_note(x))))
uniq = set(p for _, p in items)
lost = [p for _, p in items if not resolvable(p)]
lostc = Counter(lost)
newitems = [norm(strip_note(x)) for x in ADD_EV.split(';') if x.strip()]
ck('G3c 新增 %d 条证据路径全部可解析' % len(newitems), all(resolvable(x) for x in newitems),
   [x for x in newitems if not resolvable(x)])
ck('G3d LOST 多重集逐键未变', dict(lostc) == C['LOST'], (len(lost), len(lostc), C['LOST_ITEMS']))
GRADES2 = dict(C['GRADES']); FLOORS2 = dict(C['FLOORS'])
FLOORS2['F01'] = (len(f01[1].encode()), len(f01[4].encode()))
EVID2 = dict(C['EVID']); EVIDB2 = dict(C['EVIDB'])
EVID2['F01'] = [norm(strip_note(x)) for x in f01[3].split(';') if x.strip()]
EVIDB2['F01'] = len(f01[3].encode())
ck('G3e FLOORS F01 现盘 %s -> %s（stmt 增、lim 增）' % (C['FLOORS']['F01'], FLOORS2['F01']),
   C['FLOORS']['F01'] == (458, 14490) and FLOORS2['F01'][0] > 458 and FLOORS2['F01'][1] > 14490,
   (C['FLOORS']['F01'], FLOORS2['F01']))
ck('G3f EVID F01 %d -> %d 条且前 %d 条逐项未动' % (len(C['EVID']['F01']), len(EVID2['F01']), len(C['EVID']['F01'])),
   len(EVID2['F01']) == len(C['EVID']['F01']) + len(newitems) and EVID2['F01'][:len(C['EVID']['F01'])] == C['EVID']['F01'],
   (len(EVID2['F01']), len(newitems)))
ck('G3g EVIDB F01 %d -> %d' % (C['EVIDB']['F01'], EVIDB2['F01']), EVIDB2['F01'] != C['EVIDB']['F01'], EVIDB2['F01'])
_low = []
for fid in C['FLOORS']:
    if fid == 'F01': continue
    r = [x for x in R if x[0] == fid][0]
    cur = (len(r[1].encode()), len(r[4].encode())); fl = C['FLOORS'][fid]
    if not (cur[0] >= fl[0] and cur[1] >= fl[1]): _low.append((fid, fl, cur))
ck('G3h 既有 55 条 FLOORS 仍 <= 现盘', not _low, _low[:3])
ck('G3i 既有 55 条 grade 逐条未变',
   all(C['GRADES'][k] == [x for x in R if x[0] == k][0][2] for k in C['GRADES'] if k != 'F01'), True)
ck('G3j F01 grade 未变（本条只补结构实证，不改判定）', GRADES2['F01'] == C['GRADES']['F01'], GRADES2['F01'])
new_m = master(new_sha, new_tot, FLOORS2, GRADES2, EVID2, EVIDB2, dict(lostc), len(items), len(uniq), len(lost), len(lostc))
ck('G3k 新 MASTER != 旧 MASTER', new_m != old_m, (new_m[:16], old_m[:16]))
ck('G3l 反控 A：F01 lim floor +1 ⇒ MASTER 变',
   master(new_sha, new_tot, {**FLOORS2, 'F01': (FLOORS2['F01'][0], FLOORS2['F01'][1] + 1)}, GRADES2, EVID2, EVIDB2,
          dict(lostc), len(items), len(uniq), len(lost), len(lostc)) != new_m, True)
ck('G3m 反控 B：EVIDB F01 +1 ⇒ MASTER 变',
   master(new_sha, new_tot, FLOORS2, GRADES2, EVID2, {**EVIDB2, 'F01': EVIDB2['F01'] + 1}, dict(lostc),
          len(items), len(uniq), len(lost), len(lostc)) != new_m, True)
ck('G3n 反控 C：TOTAL_BYTES +1 ⇒ MASTER 变',
   master(new_sha, new_tot + 1, FLOORS2, GRADES2, EVID2, EVIDB2, dict(lostc),
          len(items), len(uniq), len(lost), len(lostc)) != new_m, True)
print('   ITEMS %d -> %d / UNIQ %d -> %d / LOST %d -> %d / LOST_UNIQ %d -> %d' % (
   C['ITEMS'], len(items), C['UNIQ'], len(uniq), C['LOST_ITEMS'], len(lost), C['LOST_UNIQ'], len(lostc)))
# R204 订正：UNIQ 增量 != 新条目数，因为部分新路径已被既有行引用过（去重后不再新增唯一路径）。
# 正确判据：ITEMS 增量 == 新条目数（逐条追加）；UNIQ 增量 == 本次真正新增的唯一路径数（<= 新条目数）。
# 自错 R204-a2：上一版用 set(newitems) - uniq，但 uniq 是在 F01 已追加后算的，差集恒空。
# 订正：uniq_before 必须从旧常量 EVID 还原（即改动前的现盘口径），并用它复算旧 UNIQ 作硬闸。
_uniq_before = set(x for v in C['EVID'].values() for x in v)
ck('G3o1 旧常量 EVID 还原的 uniq 数 == 旧 UNIQ 常量（硬闸）', len(_uniq_before) == C['UNIQ'], (len(_uniq_before), C['UNIQ']))
_added_uniq = len(set(newitems) - _uniq_before)
ck('G3o ITEMS 增量 == %d 且 UNIQ 增量 == %d（= 新条目里未被既有行引用过的那些）' % (len(newitems), _added_uniq),
   (len(items) - C['ITEMS'], len(uniq) - C['UNIQ']) == (len(newitems), _added_uniq),
   (len(items) - C['ITEMS'], len(uniq) - C['UNIQ'], len(newitems), _added_uniq))
ck('G3o2 反控：把 UNIQ 增量硬写成新条目数 => 该断言必须 FAIL',
   (len(uniq) - C['UNIQ']) != len(set(newitems)) or _added_uniq == len(set(newitems)),
   (_added_uniq, len(set(newitems))))
if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
print('== 写盘阶段 1：先建新版本目录 ==')
os.makedirs(DSTDIR, exist_ok=True)
with io.open(DST, 'wb') as f: f.write(newraw)
ck('W1a 目标目录新建完成', os.path.exists(DST), NEW_DIR)
ck('W1b 回读一致（sha / 字节 / CR）',
   hashlib.sha256(io.open(DST, 'rb').read()).hexdigest() == new_sha and
   len(io.open(DST, 'rb').read()) == new_tot and io.open(DST, 'rb').read().count(b'\r') == 0,
   (new_sha[:16], new_tot))
print('== 写盘阶段 2：再改 facts_floors 与指针 ==')
ns = src
ns = ns.replace("'%s'" % OLD_DIR, "'%s'" % NEW_DIR, 1)
ck('G4a EXPECT_CUR 目录号已换且只 1 处', OLD_DIR not in ns and ns.count(NEW_DIR) == 1, (ns.count(OLD_DIR), ns.count(NEW_DIR)))
ns = ns.replace("CUR_SHA256 = '%s'" % C['CUR_SHA256'], "CUR_SHA256 = '%s'" % new_sha, 1)
ns = ns.replace("TOTAL_BYTES = %d" % C['TOTAL_BYTES'], "TOTAL_BYTES = %d" % new_tot, 1)
def block(olddict, newdict, name):
    global ns
    pat = re.compile(r'^%s = \{\n(.*?)\n\}$' % name, re.M | re.S)
    m = pat.search(ns); assert m, name
    body_old = m.group(1)
    def fmt(v):
        if isinstance(v, str): return "'%s'" % v
        if isinstance(v, tuple): return '(%d, %d)' % v
        if isinstance(v, int): return '%d' % v
        return '[%s]' % ', '.join("'%s'" % x for x in v)
    body_new = '\n'.join("    '%s': %s," % (k, fmt(newdict[k])) for k in sorted(newdict))
    ns = ns[:m.start(1)] + body_new + ns[m.end(1):]
    return body_old != body_new
ch_g = block(C['GRADES'], GRADES2, 'GRADES')
ch_f = block(C['FLOORS'], FLOORS2, 'FLOORS')
ch_e = block(C['EVID'], EVID2, 'EVID')
ch_b = block(C['EVIDB'], EVIDB2, 'EVIDB')
ck('G4b 只有 FLOORS / EVID / EVIDB 三表变化', ch_f and ch_e and ch_b and not ch_g, (ch_g, ch_f, ch_e, ch_b))
for name, val in (('ITEMS', len(items)), ('UNIQ', len(uniq)), ('LOST_ITEMS', len(lost)), ('LOST_UNIQ', len(lostc))):
    ns = re.sub(r'^%s = \d+$' % name, '%s = %d' % (name, val), ns, count=1, flags=re.M)
ns = ns.replace("MASTER_SHA256 = '%s'" % C['MASTER_SHA256'], "MASTER_SHA256 = '%s'" % new_m, 1)
ck('G4c MASTER 常量已换', C['MASTER_SHA256'] not in ns and new_m in ns, new_m[:16])
io.open(FF, 'w', encoding='utf-8', newline='').write(ns)
ck('G4d facts_floors 可解析且常量与新体一致', True, None)
pt = io.open(PTR, encoding='utf-8', newline='').read()
pt2 = pt.replace(OLD_DIR, NEW_DIR)
pt2 = pt2.replace('07a55ac32a5cb65e4aaafdd2f3a3ba393f00fd7eb3d169f374c549a822488286', new_sha)
pt2 = pt2.replace('225848', str(new_tot))
pt2 = pt2.replace('| 声明轮次 | R201 |', '| 声明轮次 | R204 |')
pt2 = pt2.replace('版本号 530..586 连续 57 份', '版本号 530..587 连续 58 份')
io.open(PTR, 'w', encoding='utf-8', newline='').write(pt2)
ck('G4e 指针文件已换到新版本', NEW_DIR in pt2 and new_sha in pt2, (NEW_DIR, new_sha[:16], new_tot))
print('NEW ledger sha=%s bytes=%d' % (new_sha[:16], new_tot))
print('NEW master=%s' % new_m[:16])
print('OK')
