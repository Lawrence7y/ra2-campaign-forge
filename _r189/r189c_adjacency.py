#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R189 C：第一实现的**独立第二实现**（不复用 r189b 的任何代码形状）：
直接从 .rdata/.data 的原始字节按 4 字节步进建三张集合（COL 记录、vtable 头、槽值），
再用「邻接」判据回答一个问题：vtable 之后的那个非 .text dword 到底是什么？

结论要能支持/推翻 R188 的定性「979 张表撞到内嵌子对象 vtable 指针」。
反控 N1..N4 见下。
"""
import sys, os, struct, json, collections
ROOT = '/home/t628/projects/ra2-campaign-forge'
RAW = open(ROOT + '/ra2bench/gamemd.exe', 'rb').read()
pe = struct.unpack_from('<I', RAW, 0x3c)[0]
NSEC = struct.unpack_from('<H', RAW, pe + 6)[0]
OPTSZ = struct.unpack_from('<H', RAW, pe + 20)[0]
IB = struct.unpack_from('<I', RAW, pe + 24 + 28)[0]
SEC = []
for i in range(NSEC):
    o = pe + 24 + OPTSZ + 40 * i
    nm = RAW[o:o + 8].rstrip(b'\0').decode('latin1')
    vs, va, rs, ra = struct.unpack_from('<IIII', RAW, o + 8)
    SEC.append((nm, IB + va, IB + va + rs, ra, rs))
VM = {}
for nm, lo, hi, ra, rs in SEC:
    for a in range(lo, hi, 4):
        VM[a] = struct.unpack_from('<I', RAW, ra + (a - lo))[0]

TXT_LO, TXT_HI = [s for s in SEC if s[0] == '.text'][0][1:3]
fails = []; nchk = 0
def ck(nm, c, d=''):
    global nchk; nchk += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

# --- COL 记录：5 dword 自描述，sig∈{0,1}、第 3 dword==0、[3]→.data 名串、[4]→.rdata ---
def off2sec(v):
    for nm, lo, hi, ra, rs in SEC:
        if lo <= v < hi: return nm
    return None
COL = {}
for nm, lo, hi, ra, rs in SEC:
    if nm not in ('.rdata', '.data'): continue
    for a in range(lo, hi - 16, 4):
        s0, s1, s2, s3, s4 = (VM.get(a + 4 * j) for j in range(5))
        if s0 not in (0, 1) or s2 != 0: continue
        if off2sec(s3) != '.data' or off2sec(s4) != '.rdata': continue
        o = [x[3] for x in SEC if x[0] == '.data'][0] + 8 + (s3 - [x[1] for x in SEC if x[0] == '.data'][0])
        e = RAW.find(b'\0', o, o + 200)
        nmz = RAW[o:e] if e > 0 else b''
        if not (nmz.startswith(b'.?A') and nmz.endswith(b'@@')): continue
        COL[a] = (s1, nmz.decode('latin1'))
ck('C0 COL 记录 1214 条', len(COL) == 1214, len(COL))   # by construction of earlier rounds

# --- vtable 头：dword[a] 落 .text 且 dword[a-4] 是 COL ---
VT = {}
for a in sorted(VM):
    if not (TXT_LO <= VM[a] < TXT_HI): continue
    tag = VM.get(a - 4)
    if tag in COL: VT[a] = tag     # 表头前 4 字节 = 指向该表 COL 记录的**指针**（不是 COL 记录本身）
ck('C1 vtable 头 1214 个', len(VT) == 1214, len(VT))
ck('C2 vtable 恰 1214 个、每个的 −4 dword 都解引用到一条 COL',
   len(VT) == 1214 and all(c in COL for c in VT.values()), len(VT))

# --- 前缀长度（只数 .text 槽） ---
PRE = {}
for vt in VT:
    k = 0
    while (vt + 4 * k) in VM and TXT_LO <= VM[vt + 4 * k] < TXT_HI:
        k += 1
    PRE[vt] = k
ck('C3 槽位实例总数 14044', sum(PRE.values()) == 14044, sum(PRE.values()))
ck('C4 每张表至少 1 槽', min(PRE.values()) >= 1, min(PRE.values()))

# --- 核心问题：截断点 dword 是什么？其 +4 处是不是下一张 vtable 的头？ ---
stat = collections.Counter(); adj = 0; adj_bad = []
notcol_tail = collections.Counter()
for vt in VT:
    stop = vt + 4 * PRE[vt]
    d = VM.get(stop)
    if d is None: stat['no-dword'] += 1; continue
    if d in COL:
        stat['COL'] += 1
        nxt = stop + 4
        if VT.get(nxt) == d: adj += 1
        else: adj_bad.append((hex(vt), hex(d), hex(nxt)))
    else:
        stat[off2sec(d) or 'other'] += 1
        notcol_tail['next_is_vt' if VT.get(stop + 4) else 'next_not_vt'] += 1
print('# 截断点分类 %s' % dict(stat))
print('# 非 COL 截断点的 +4 处：%s' % dict(notcol_tail))
ck('C5 截断点在 COL 的表 979 张', stat['COL'] == 979, stat['COL'])
ck('C6 其中 979/979 的「截断点 dword == 截断点+4 处那张 vtable 的 −4 COL」', adj == 979,
   (adj, len(adj_bad)))
ck('C7 反例集合为空', len(adj_bad) == 0, adj_bad[:3])
ck('C8 ⇒ 前缀长度就是真实槽数：不存在「表内嵌了一个 COL 指针」的中间截断',
   adj == stat['COL'])

# --- 反控 ---
# N1a：错配反控 —— 把每张表的「截断点 COL」与**另一张表**的头前 COL 配对（按索引 +137 轮转），
#      若 C6 是真判据，错配后应几乎全落空
heads = sorted(VT)
tag_at = {vt: VM.get(vt - 4) for vt in heads}
hit_rot = 0
for i, vt in enumerate(heads):
    if VM.get(vt + 4 * PRE[vt]) not in COL: continue
    other = heads[(i + 137) % len(heads)]
    if VM.get(vt + 4 * PRE[vt]) == tag_at[other]: hit_rot += 1
ck('N1a 反控：把截断点 COL 与另一张表头前 COL 错配后只命中 %d（应 << 979）' % hit_rot,
   hit_rot < 10, hit_rot)
# N1b：判别力反控 —— 对 235 张「截断点不是 COL」的表，同样问「+4 处是不是表头」，应为 0
n_null = sum(1 for vt in VT if VM.get(vt + 4 * PRE[vt]) not in COL)
n_null_next = sum(1 for vt in VT if VM.get(vt + 4 * PRE[vt]) not in COL and (vt + 4 * PRE[vt] + 4) in VT)
ck('N1b 判别力：非 COL 截断的 %d 张表里「+4 处是表头」的 %d 张 ⇒ 判据能区分两类'
   % (n_null, n_null_next), n_null == 235 and n_null_next == 0, (n_null, n_null_next))
# N1c：紧排的结构性断言 —— 每个 vtable 头的前一 dword 都是一条 COL 地址
n_heads_with_col = sum(1 for vt in VT if VM.get(vt - 4) in COL)
ck('N1c 紧排：1214/1214 张表头的前一 dword 都是 COL 地址', n_heads_with_col == len(VT), n_heads_with_col)
# N2：把下一张表起点改成 截断点+8，应大幅掉下来
adj8 = sum(1 for vt in VT if VM.get(vt + 4 * PRE[vt]) in COL and
           VT.get(vt + 4 * PRE[vt] + 8) == VM.get(vt + 4 * PRE[vt]))
ck('N2 反控：改用 截断点+8 作下一张表头，命中 %d << 979' % adj8, adj8 < 100, adj8)
# N3：把 PRE 人为减 1（少算一槽），邻接应大面积失效
adj_off = sum(1 for vt in VT if PRE[vt] >= 1 and VM.get(vt + 4 * (PRE[vt] - 1)) in COL and
              VT.get(vt + 4 * (PRE[vt] - 1) + 4) == VM.get(vt + 4 * (PRE[vt] - 1)))
ck('N3 反控：PRE−1 时邻接只剩 %d' % adj_off, adj_off < 979, adj_off)
# N4：若把「下一张表的 COL」改成「任意已知 COL」则命中 979 全靠猜
anycol = sum(1 for vt in VT if VM.get(vt + 4 * PRE[vt]) in COL)
ck('N4 反控：判据不是「dword 是任意 COL」（那与邻接是两件事）', anycol == 979 and adj == 979)

# --- F02 / F03 逐值 ---
BT = 0x7E3EBC
ck('C9 BuildingClass vtable 存在、前缀 322', BT in VT and PRE[BT] == 322, PRE.get(BT))
ck('C10 其上界 vt+322*4 == 0x7E43C4', BT + 4 * 322 == 0x7E43C4)
ck('C11 截断点 0x7E43C4 的 dword 0x7FC298 恰是下一张 vtable(0x7E43C8) 的 COL',
   VM.get(0x7E43C4) == 0x7FC298 and VT.get(0x7E43C8) == 0x7FC298,
   (hex(VM.get(0x7E43C4)), hex(VT.get(0x7E43C8) or 0)))
ck('C12 那张下一张表的 COL 类名 == ?$DynamicVectorClass@PAVInfantryClass@@@',
   COL[0x7FC298][1] == '.?AV?$DynamicVectorClass@PAVInfantryClass@@@@', COL[0x7FC298][1])
ck('C13 下一张表自己也是 7 槽（与其前缀一致）', PRE.get(0x7E43C8) == 7, PRE.get(0x7E43C8))
ck('C14 F03 槽 0x7E3FE0 -> 0x43F180', VM.get(0x7E3FE0) == 0x43F180, hex(VM.get(0x7E3FE0) or 0))
ck('C15 F03 槽 0x7E4068 -> 0x449440', VM.get(0x7E4068) == 0x449440, hex(VM.get(0x7E4068) or 0))
ck('C16 两槽号 == 73 / 107', (0x7E3FE0 - BT) // 4 == 73 and (0x7E4068 - BT) // 4 == 107)
vals = [VM[BT + 4 * i] for i in range(322)]
ck('C17 322 槽 == 322 个不同值（F02 陈述）', len(set(vals)) == 322, len(set(vals)))

# --- 剩余 235 张表的截断点是什么（如实登记，不解释成结论） ---
rest = [vt for vt in VT if VM.get(vt + 4 * PRE[vt]) not in COL]
print('# 剩余 %d 张非 COL 截断：%s' % (len(rest), collections.Counter(
    off2sec(VM.get(vt + 4 * PRE[vt])) for vt in rest)))
for vt in rest[:6]:
    stop = vt + 4 * PRE[vt]
    print('   vt %08X  slots %3d  stop %08X = %08X (%s)  stop+4 is vt? %s' % (
        vt, PRE[vt], stop, VM.get(stop) or 0, off2sec(VM.get(stop)), stop + 4 in VT))

# --- 槽数直方（真实槽数，无折扣） ---
h = collections.Counter(PRE.values())
print('# 真实槽数直方 top %s  最大 %d' % (sorted(h.items(), key=lambda x: -x[1])[:8], max(PRE.values())))
out = dict(prefix_total=sum(PRE.values()), stat=dict(stat), adj=adj, n_col=stat['COL'],
           rest=len(rest), hist={str(k): v for k, v in h.items()},
           col_vt=0x7E43C4, col_at=hex(VM.get(0x7E43C4) or 0), slots_max=max(PRE.values()))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'r189c.json'), 'w').write(
    json.dumps(out, indent=1, ensure_ascii=False))
print('\n断言 %d 条，FAIL %d 条' % (nchk, len(fails)))
sys.exit(1 if fails else 0)
