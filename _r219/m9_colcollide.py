# -*- coding: utf-8 -*-
"""R219 m9：R218『4 个幻影虚表』真实定性 —— 数值表常量与 COL 地址撞车。

m7/m8 已证：
  - 4 个候选地址 0x877000 / 0x877010 / 0x87b17c / 0x87b18c 的 dw(V-4) 都等于 0x00800040；
  - 0x00800040 是 DropPodLocomotionClass 的 COL 记录地址（pTD=0x8202f8, mdisp=4）；
  - 但 0x00800040 在 .rdata 只出现 1 次（0x7e8274，即真虚表 0x7e8278 的 V-4）；
    在 .data 出现 4 次，且 4 次都落在一段**数值序列**里。

本脚本要回答：
  A. 0x00800040 所在的 .data 区间是什么数据？（邻域是否构成等差/三角数表）
  B. 「dw(V-4) 等于某个 COL 地址」这个判据在全库有多少误报？
     即：除真虚表 1214 张外，还有多少位置满足 dw(V-4)∈COL 但 dw(V) 不落 .text。
  C. COL 地址里有多少个「小整数」形态（< 0x810000，落在数值常量常见范围），即可被撞车的全集。
  D. 真表 1214 张与 COL 记录是否真的一一对应（双射）？
  E. 反控：把判据换成「dw(V-4)∈COL 且 dw(V) 落 .text」时，把 .data 数值区整段排除后计数必须不变。

正控：真虚表 0x7e8278（DropPodLocomotionClass 唯一真表）必须被 [D] 归到 COL 0x800040；
      真虚表 0x7e1f50（AbstractClass 主视图）槽数必须为 24。
"""
import sys, struct, collections, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def words(sn):
    s = P.B[sn]
    return struct.unpack_from('<%dI' % (s['rawsize'] // 4), P.RAW, s['rawptr']), s['lo']

COL = {}
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k in range(len(w) - 5):
        if w[k] > 2 or w[k + 2] != 0: continue
        if P.where(w[k + 3]) != '.data' or P.where(w[k + 4]) != '.rdata': continue
        nm = P.cstr(w[k + 3] + 8, 512)
        if not nm or nm[:3] != b'.?A' or nm[-2:] != b'@@': continue
        COL[base + 4 * k] = dict(md_=s32(w[k + 1]), pCHD=w[k + 4], name=nm.decode('latin1'))
CS = set(COL)
print('[0] COL records = %d   min=%#x max=%#x' % (len(COL), min(CS), max(CS)))

# ---------- A ----------
print('\n[A] neighbourhood of 0x00800040 occurrences in .data (as integers, signed):')
da = P.B['.data']
for a0 in (0x876ffc, 0x87700c, 0x87b178, 0x87b188):
    seq = [s32(P.dw(a0 + 4 * j)) for j in range(-6, 7)]
    print('   around %#x : %s' % (a0, seq))
    # check arithmetic progression of neighbours (excluding zeros/far)
    diffs = [seq[i + 1] - seq[i] for i in range(len(seq) - 1) if seq[i] and seq[i + 1]]
    print('       nonzero consecutive diffs sample: %s' % diffs[:6])
# 判定：邻域是否存在长等差段
def longest_ap(vals):
    best = 1; cur = 1; d = None
    for i in range(1, len(vals)):
        nd = vals[i] - vals[i - 1]
        if d is not None and nd == d:
            cur += 1; best = max(best, cur)
        else:
            cur = 2; d = nd
    return best
big = [s32(P.dw(x)) for x in range(0x876f00, 0x877400, 4)]
print('   longest arithmetic run in 0x876f00..0x877400 = %d elements (a numeric table, not pointers)'
      % longest_ap([v for v in big if v != 0]))
print('   distinct |value| count in that window: %d of %d slots'
      % (len(set(abs(v) for v in big)), len(big)))

# ---------- B ----------
print('\n[B] FALSE-POSITIVE space of the criterion "dw(V-4) in COL":')
cand_all = []
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k, v in enumerate(w):
        if v in CS:
            cand_all.append((base + 4 * k + 4, v))
real = [(V, c) for V, c in cand_all if P.where(P.dw(V)) == '.text']
ghost = [(V, c) for V, c in cand_all if P.where(P.dw(V)) != '.text']
print('   total V with dw(V-4) in COL = %d   real(dw(V) in .text) = %d   ghost = %d'
      % (len(cand_all), len(real), len(ghost)))
print('   ghost list (V, COL, COLname, dw(V), where(dw(V))):')
for V, c in ghost:
    print('      %#08x  %#x  %-34s  dw(V)=%08x  %s'
          % (V, c, COL[c]['name'], P.dw(V), P.where(P.dw(V))))

# ---------- C ----------
print('\n[C] how many COL addresses are "small integers" (<= 0x810000, i.e. collidable with numeric constants)?')
small = sorted(c for c in CS if c <= 0x810000)
print('   COL <= 0x810000 : %d of %d' % (len(small), len(CS)))
print('   all of them: %s' % [hex(c) for c in small])
# 这些地址在 .data 数值区出现几次（不受 COL 判据约束）
draw = P.RAW[da['rawptr']:da['rawptr'] + da['rawsize']]
print('   their raw dword occurrences in .data:')
for c in small:
    pat = struct.pack('<I', c); n = 0; st = 0; locs = []
    while True:
        i = draw.find(pat, st)
        if i < 0: break
        n += 1; locs.append(da['lo'] + i); st = i + 1
    print('      %#x %-34s %d occurrences %s' % (c, COL[c]['name'], n, [hex(x) for x in locs]))

# ---------- D ----------
print('\n[D] bijection test real vtables <-> COL:')
byc = collections.defaultdict(list)
for V, c in real:
    byc[c].append(V)
multi = {c: v for c, v in byc.items() if len(v) > 1}
print('   real vtables = %d ; distinct COL covered = %d ; COL with >1 real vtable = %d'
      % (len(real), len(byc), len(multi)))
for c, vs in list(multi.items())[:10]:
    print('      COL %#x %-32s -> %s' % (c, COL[c]['name'], [hex(x) for x in vs]))
print('   COL with 0 real vtable = %d' % len(CS - set(byc)))
print('   POSITIVE CONTROL: COL 0x800040 -> real vtables %s'
      % [hex(v) for v in byc.get(0x800040, [])])

# ---------- D2 positive control slot counts ----------
def nslots(vt, cap=65536):
    n = 0
    while n < cap and P.where(P.dw(vt + 4 * n)) == '.text': n += 1
    return n
print('   POSITIVE CONTROL 0x7e1f50 slots = %d (expect 24)' % nslots(0x7e1f50))
print('   POSITIVE CONTROL 0x7e8278 slots = %d' % nslots(0x7e8278))

# ---------- E ----------
print('\n[E] NEG CONTROL: exclude the whole .data numeric window 0x870000..0x880000 and recount real')
CNT = 0
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k, v in enumerate(w):
        V = base + 4 * k + 4
        if v in CS and P.where(P.dw(V)) == '.text' and not (0x870000 <= V < 0x880000):
            CNT += 1
print('   real vtables outside 0x870000..0x880000 = %d (was %d)  -> delta %d'
      % (CNT, len(real), len(real) - CNT))

json.dump(dict(col=len(COL), cand=len(cand_all), real=len(real), ghost=[(hex(V), hex(c)) for V, c in ghost],
               small=[hex(c) for c in small], multi={hex(c): [hex(x) for x in v] for c, v in multi.items()},
               zero_col=len(CS - set(byc))),
          open('/home/t628/projects/ra2-campaign-forge/_r219/m9.json', 'w'), indent=1)
print('\n[done] -> _r219/m9.json')
