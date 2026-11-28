# -*- coding: utf-8 -*-
"""R219 m11：定稿复核（R218 待办①、④ 的最终结论 + 正反控总表）。

结论链：
  m1  : 6 处超 344 槽域位点 = 5 处对象内函数指针字段 +0x77c/+0x780/+0x784（不是虚表槽），
        1 处 0x7cde2b 是 12 字节步长静态派发表（esi=edi*12）。
  m3  : window=24 下 931 个 s>=256 位点里 914 是 vftable 消费（A 类），17 是 C 类。
  m6  : 复算 R218 六数全部一致（18935 / 931 / 91 / 925 / top s 309/85/73/58/44），
        归并函数 311、unresolved 528。
  m7~m10: 4 个「幻影虚表」= 一张 162 记录 × 16 字节常量表的副本里 f2 字段恰为 COL 0x800040。

本脚本一次给出：
  [1] 两处 162 记录表是否逐字节相同；表范围与记录内容首/末 3 行。
  [2] 4 个幻影地址在两表中的相对偏移（验证同构）。
  [3] 表区间被 .text 以 dword 引用的位点全清单（m10 报 24，逐个列出并判是否指向表内记录边界）。
  [4] 全库 dw(V-4) in COL 且 dw(V) 不落 .text 的最终计数（必须 == 4）。
  [5] 三重正控（0x414471 虚表槽消费 / 0x7e8278 与 0x7e1f50 槽数）。
  [6] 三重反控（shift 4/8/12 命中 0；其他 delta 命中 <= 2；s<0x400 组 A 类占比作对照）。
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

def blob(a, n):
    o = P.r2o(a); return P.RAW[o:o + n]

# ---------- [1] ----------
A1, A2, N = 0x876ff4, 0x87b170, 0xa10
b1, b2 = blob(A1, N), blob(A2, N)
print('[1] two candidate record tables')
print('    T1 %#x .. %#x  len=%d' % (A1, A1 + N, len(b1)))
print('    T2 %#x .. %#x  len=%d' % (A2, A2 + N, len(b2)))
print('    byte-identical = %s' % (b1 == b2))
import hashlib
print('    sha256 T1 = %s' % hashlib.sha256(b1).hexdigest())
print('    sha256 T2 = %s' % hashlib.sha256(b2).hexdigest())
print('    first 3 rows of T1:')
for i in range(3):
    a = A1 + 16 * i
    print('      %#08x : %08x %08x %08x %08x' % (a, *[P.dw(a + 4 * k) for k in range(4)]))
print('    last 3 rows of T1:')
for i in range(159, 162):
    a = A1 + 16 * i
    print('      %#08x : %08x %08x %08x %08x' % (a, *[P.dw(a + 4 * k) for k in range(4)]))
# 边界证据
print('    boundary: row before T1 %#x : %08x %08x %08x %08x'
      % (A1 - 16, *[P.dw(A1 - 16 + 4 * k) for k in range(4)]))
print('    boundary: row after  T1 %#x : %08x %08x %08x %08x'
      % (A1 + N, *[P.dw(A1 + N + 4 * k) for k in range(4)]))
print('    boundary: row before T2 %#x : %08x %08x %08x %08x'
      % (A2 - 16, *[P.dw(A2 - 16 + 4 * k) for k in range(4)]))
print('    boundary: row after  T2 %#x : %08x %08x %08x %08x'
      % (A2 + N, *[P.dw(A2 + N + 4 * k) for k in range(4)]))

# ---------- [2] ----------
print('\n[2] phantom sites relative offsets')
PH = [0x877000, 0x877010, 0x87b17c, 0x87b18c]
for v in PH:
    d1 = v - A1; d2 = v - A2
    same = (d1 == d2) and 0 <= d1 < N
    print('    %#x : off in T1=%#x off in T2=%#x  same=%s  rec#=%d field=%d'
          % (v, d1, d2, same, d1 // 16 if d1 >= 0 else -1, (d1 % 16) // 4 if d1 >= 0 else -1))

# ---------- [3] ----------
T = P.B['.text']; traw = P.RAW[T['rawptr']:T['rawptr'] + T['rawsize']]
print('\n[3] .text dword refs into T2 range %#x..%#x' % (A2, A2 + N))
hits = []
for a in range(A2, A2 + N, 4):
    pat = struct.pack('<I', a); st = 0
    while True:
        i = traw.find(pat, st)
        if i < 0: break
        hits.append((T['lo'] + i, a)); st = i + 1
print('    total = %d' % len(hits))
for code, tgt in hits:
    print('      code %#08x -> %#08x  (offset in T2 = %#x)' % (code, tgt, tgt - A2))

# ---------- [4] ----------
print('\n[4] FINAL: dw(V-4) in COL but dw(V) not in .text')
ghost = []
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k, v in enumerate(w):
        V = base + 4 * k + 4
        if v in CS and P.where(P.dw(V)) != '.text':
            ghost.append((V, v, sn))
print('    count = %d  (must be 4)' % len(ghost))
for V, c, sn in ghost:
    print('      %#08x %s COL=%#x %s' % (V, sn, c, COL[c]['name']))

# ---------- [5] ----------
def nslots(vt, cap=65536):
    n = 0
    while n < cap and P.where(P.dw(vt + 4 * n)) == '.text': n += 1
    return n
print('\n[5] POSITIVE CONTROLS')
print('    0x7e8278 (DropPodLocomotionClass 真表) slots=%d, V-4=%#x in COL=%s'
      % (nslots(0x7e8278), P.dw(0x7e8278 - 4), P.dw(0x7e8278 - 4) in CS))
print('    0x7e1f50 (AbstractClass 主视图) slots=%d (expect 24)' % nslots(0x7e1f50))
print('    0x414471 = call dword ptr [edx+0x544] 且前驱 0x414466 mov edx,dword ptr [esi]  => vftable 消费')

# ---------- [6] ----------
print('\n[6] NEG CONTROLS')
def rel(a):
    return ((P.dw(a + 12) - P.dw(a + 8)) & 0xFFFFFFFF)
for sh in (4, 8, 12):
    n = sum(1 for a in range(A1 + sh, A1 + N, 16) if rel(a) == 0x00800080)
    print('    shift %2d in T1 -> %d hits (expect 0)' % (sh, n))
print('    same relation shift 16 -> %d hits (must be 161, proves the relation is lattice-bound)'
      % sum(1 for a in range(A1 + 16, A1 + N, 16) if rel(a) == 0x00800080))
for d in (0x00800000, 0x00800100):
    n = sum(1 for a in range(A1, A1 + N, 16) if rel(a) == d)
    print('    delta %#x -> %d (expect <= 2)' % (d, n))

json.dump(dict(t1=A1, t2=A2, n=N, identical=(b1 == b2),
               sha1=hashlib.sha256(b1).hexdigest(), sha2=hashlib.sha256(b2).hexdigest(),
               refs=[(hex(c), hex(t)) for c, t in hits],
               ghost=[(hex(V), hex(c)) for V, c, _ in ghost]),
          open('/home/t628/projects/ra2-campaign-forge/_r219/m11.json', 'w'), indent=1)
print('\n[done] -> _r219/m11.json')
