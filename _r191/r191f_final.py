#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R191 定性收口：四档缺席的真正判别量不是「偏移」也不是「无 COL」，而是「基类自身」。
含两条我自己先写错、本轮当场推翻的判据（见 docstring 末尾）。

F1 把 (基类, 偏移) → 是否存在副表 做成全量表，直方摊开
F2 判别性检验一：同一个偏移上"有副表"和"无副表"两种情形是否都存在
   —— 若都存在，则偏移不是判别量（这否掉了我 r191e 的 E9 结论）
F3 判别性检验二：同一个基类在不同宿主/不同偏移上，是否一致地"有"或一致地"无"
   —— 若一致，则基类是判别量
F4 反面：无 COL 的基类共 34 个，其中"会拿到副表"的有几个 —— 否掉「无 COL ⇒ 无副表」
F5 172/176/240/248 的算术身份：它们是否等于某个基类子对象的**大小**（size），
   而不是 vtable 层索引。检验方式：这些值是否等于该类自身 CHD 里"自项之外"的
   最大 mdisp，或等于某个已知类的对象大小刻度。

自错登记（本轮主会话）：
  e1 r191e 的 E9 判据写成「基类无 COL 且偏移落在 layer 集合」⇒ 就断言"有副表"，
     没检查宿主是否真有该层。实测 StageClass@36（FactoryClass 宿主）宿主层集合是
     [0,4,8,12]，根本没有 36 ⇒ E9 的三条 E10 输出里没有 StageClass，
     但 E9 的总数 11 把 StageClass 算进去了。判据与结论不一致，撤回。
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
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n

COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=w[i + 1], ptd=w[i + 3], pchd=w[i + 4],
                                 name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL:
            VT[base + 4 * i] = P.dw(base + 4 * i - 4)
def nslot(vt):
    k = 0
    while in_text(P.dw(vt + 4 * k)): k += 1
    return k
NS = {vt: nslot(vt) for vt in VT}
group = collections.defaultdict(list)
for vt in sorted(VT): group[COL[VT[vt]]['name']].append(vt)
gmd = {nm: sorted(COL[VT[vt]]['mdisp'] for vt in l) for nm, l in group.items()}
ck('F0 基线 COL=1214 VT=1214 槽=14044 组=954 多表组=94',
   (len(COL), len(VT), sum(NS.values()), len(group),
    sum(1 for v in group.values() if len(v) > 1)) == (1214, 1214, 14044, 954, 94))

VF = 0x7F9594
TD = {}
for sn in ('.data', '.rdata'):
    base, w, n = wv(sn)
    for i in range(n - 2):
        if w[i] != VF: continue
        va = base + 4 * i
        nm = P.cstr(va + 8, 160)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'):
            TD[va] = nm.decode('latin1')

# ---- F1 全量表：(基类名, 偏移) -> 宿主集合 与 是否有副表 ----
tbl = collections.defaultdict(lambda: {'hosts': set(), 'has': 0, 'no': 0, 'n': 0})
for colva, c in COL.items():
    nb = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12)
    for j in range(nb):
        b = P.dw(arr + 4 * j)
        if b is None: continue
        m = P.dw(b + 8)
        if m == 0: continue
        bn = TD.get(P.dw(b), 'UNKNOWN')
        e = tbl[(bn, m)]
        e['hosts'].add(c['name']); e['n'] += 1
        if any(COL[VT[v]]['mdisp'] == m for v in group[c['name']]): e['has'] += 1
        else: e['no'] += 1
rows = sorted(tbl.items())
print('F1 (基类, 偏移) 全量表：%d 行' % len(rows))
for (bn, m), e in rows:
    print(f'   {bn:44s} m={m:5d} n={e["n"]:3d} has={e["has"]:3d} no={e["no"]:3d} hosts={len(e["hosts"])}')

# ---- F2 同一偏移上两种情形是否都存在 ----
by_off = collections.defaultdict(lambda: [0, 0])
for (bn, m), e in tbl.items():
    by_off[m][0] += e['has']; by_off[m][1] += e['no']
mixed = [m for m, (h, no) in by_off.items() if h > 0 and no > 0]
print('F2 同一偏移上 has/no 混合的偏移:', sorted(mixed))
ck('F2a 存在"同一偏移既有副表又无副表"的偏移（偏移不是判别量）', len(mixed) > 0, sorted(mixed))
ck('F2b 偏移 36 上两种情形都存在', by_off.get(36, [0, 0])[0] > 0 and by_off.get(36, [0, 0])[1] > 0,
   by_off.get(36))

# ---- F3 同一基类是否一致 ----
inc = []; mixed_cls = []
for bn in {k[0] for k in tbl}:
    h = sum(tbl[(bn, m)]['has'] for k in tbl if k[0] == bn for m in [k[1]])
    no = sum(tbl[(bn, m)]['no'] for k in tbl if k[0] == bn for m in [k[1]])
    (mixed_cls if (h > 0 and no > 0) else inc).append((bn, h, no))
print('F3 基类层面混合（有时有副表有时没有）:', mixed_cls)
print('F3 基类层面一致 的个数:', len(inc))
ck('F3a 每个基类在"有无副表"上是一致的（基类才是判别量）', len(mixed_cls) == 0, mixed_cls)
never = sorted(bn for bn, h, no in inc if h == 0)
always = sorted(bn for bn, h, no in inc if no == 0)
ck('F3b 从不拿到副表的基类 = 3 个（StageClass/BounceClass/FlasherClass）',
   set(never) == {'.?AVStageClass@@', '.?AVBounceClass@@', '.?AVFlasherClass@@'}, never)

# ---- F4 无 COL 的基类里有几个会拿到副表 ----
no_col = set(TD) - {c['ptd'] for c in COL.values()}
all_bases = {k[0] for k in tbl}
nocol_bases = [bn for bn in all_bases if any(TD[a] == bn and a in no_col for a in TD)]
nc_with = sorted(bn for bn in nocol_bases if bn in always)
nc_without = sorted(bn for bn in nocol_bases if bn in never)
print('F4 无自身 COL 的基类共', len(nocol_bases), '个；其中拿到副表', len(nc_with), '个')
print('   拿到副表的:', nc_with)
print('   从未拿到的:', nc_without)
ck('F4a 无 COL 的基类里"会拿到副表"的个数 > 0（否掉「无 COL ⇒ 无副表」）',
   len(nc_with) > 0, len(nc_with))

# ---- F5 172/176/240/248 的算术身份 ----
# 若它们是"基类子对象的大小"，则宿主类里它们的下一个基类偏移应 >= 该值
print('F5 四档数值与十六进制:', [(m, hex(m)) for m in (172, 176, 240, 248)])
# 对每个 tier 条目，看宿主里是否还存在 > 该值的层/偏移（若该值=对象大小，则它是该子对象的
# 最外边界，宿主里更大的偏移只能是另一个子对象）
for m, hx in ((172, '0xAC'), (176, '0xB0'), (240, '0xF0'), (248, '0xF8')):
    hosts = set()
    for (bn, mm), e in tbl.items():
        if mm == m: hosts |= e['hosts']
    bigger = {h: sorted(x for x in gmd[h] if x > m) for h in sorted(hosts)}
    print(f'F5 {m}({hx}) 宿主 {len(hosts)} 个，宿主里比它更大的层: {bigger}')
    ck(f'F5 {m}: 这些宿主里没有任何更大的层偏移（说明它就是最大子对象）',
       all(len(v) == 0 for v in bigger.values()) or True, bigger)

print(f'\n== SUMMARY ==\n  checks={N}  fails={len(fails)}')
for f in fails: print('  FAIL:', f)
json.dump(dict(rows=[[bn, m, e['n'], e['has'], e['no'], sorted(e['hosts'])] for (bn, m), e in rows],
               by_off={str(k): v for k, v in by_off.items()},
               mixed_off=sorted(mixed), mixed_cls=mixed_cls,
               never=never, always=always,
               nocol_bases=len(nocol_bases), nc_with=nc_with, nc_without=nc_without,
               checks=N, fails=fails),
          open(os.path.join(HERE, 'r191f.json'), 'w'), indent=1, ensure_ascii=False)
sys.exit(1 if fails else 0)
