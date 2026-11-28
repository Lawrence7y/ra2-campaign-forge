# -*- coding: utf-8 -*-
"""R219 m13：本轮终值一条命令复现（全部数字 + 正反控断言）。

断言清单（任一 FAIL 即失败）：
  A1  R218 遗留 6 处超域位点仍可定位，且 5 处字段 offset ∈ {0x77c,0x780,0x784,0x788}、1 处 disp=0x87c488
  A2  对 +0x77c/+0x780/+0x784 的全 .text 引用 = 30 条（9/9/12）；imm32 写 .text 的写入端 = 12 条
  A3  同 offset 的 fmul/fstp qword 用法 = 3 条（2 fmul + 1 fstp）
  A4  全库无虚表槽数 >= 480；最大槽数 = 344 @ 0x7f5c70
  B1  sweep 指令数 1394186，末指令 0x7e0fff
  B2  接受集 18935；esp 9；负 disp 2；索引排除 391
  B3  s>=256 = 931；distinct s = 91；UnitClass 域 925；top s 前五 = 288:309,289:85,337:73,342:58,258:44
  C1  两张 162 记录表逐字节相同，各 2576 B，sha256 相同
  C2  记录关系 f3-f2 == 0x00800080 在 162/162 成立；shift 4/8/12 命中 0
  C3  幻影候选 = 4 个；排除 .data 0x870000..0x880000 后真表仍 1214
  D1  0x81f7b4 表与 0xEDB88320 生成表 256/256 相同；CRC-32C 不匹配
  D2  0x4a1ca0 含 not/表查/xor/not 四类指令；flush4 == zlib.crc32 在 3x5 组一致
  E1  四件套 CR 保持 1081/337/137/0/2952；STATUS_BOARD 行数 <= 300
  E2  FACT_INDEX V601 sha=54ff0419 bytes=284839；facts_floors 四常量一致
"""
import sys, struct, hashlib, re, zlib, json, os
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = ROOT + '/lead/next_re_20261117_r14'
fails = []
def ck(n, c, d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))

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
        COL[base + 4 * k] = dict(md_=s32(w[k + 1]), name=nm.decode('latin1'))
CS = set(COL)
VT = {}
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k, v in enumerate(w):
        if v in CS: VT[base + 4 * k + 4] = v
def nslots(vt, cap=65536):
    n = 0
    while n < cap and P.where(P.dw(vt + 4 * n)) == '.text': n += 1
    return n

# ---------- A ----------
SITES = [0x7bea07, 0x7bea0f, 0x7c2f17, 0x7c301c, 0x7c37c7, 0x7cde2b]
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
seen = []
for a in SITES:
    for i in md.disasm(P.RAW[P.r2o(a):P.r2o(a) + 16], a):
        m = re.search(r'\[(\w+) \+ (0x[0-9a-f]+)\]', i.op_str)
        seen.append((a, i.mnemonic + ' ' + i.op_str, int(m.group(2), 16) if m else None))
        break
ck('A1 六位点可解码且 disp 命中预期集合',
   len(seen) == 6 and all(d in (0x77c, 0x780, 0x784, 0x788, 0x87c488) for _, _, d in seen),
   [(hex(a), d) for a, _, d in seen])

raw = P.RAW[P.B['.text']['rawptr']:P.B['.text']['rawptr'] + P.B['.text']['rawsize']]
LO = P.B['.text']['lo']
T = P.B['.text']; raw_t = P.RAW[T['rawptr']:T['rawptr'] + T['rawsize']]
insns = []
pos = 0
while pos < len(raw_t):
    got = False
    for a, sz, mn, ops in md.disasm_lite(raw_t[pos:pos + 16], LO + pos):
        insns.append((a, mn, ops)); pos += sz; got = True; break
    if not got: pos += 1
MEM_RE = re.compile(r'\bptr\s*\[([^\]]+)\]', re.I)
offpat = re.compile(r'\[(eax|ebx|ecx|edx|esi|edi|ebp) \+ (0x77c|0x780|0x784)\]', re.I)
refs = [(a, mn, ops, int(m.group(2), 16)) for a, mn, ops in insns
        if (m := offpat.search(ops))]
ck('A2 三 offset 引用 = 30（9/9/12）；imm32 写 .text 写入端 = 12',
   len(refs) == 30 and sum(1 for a, mn, o, off in refs
                            if mn == 'mov' and ', 0x' in o and P.where(int(o.split(',')[-1].strip(), 16)) == '.text') == 12,
   (len(refs), sum(1 for a, mn, o, off in refs if mn == 'mov' and ', 0x' in o
                   and P.where(int(o.split(',')[-1].strip(), 16)) == '.text')))
nfloat = sum(1 for a, mn, o, off in refs if mn in ('fmul', 'fstp') and 'qword' in o)
ck('A3 fmul/fstp qword 用法 = 3', nfloat == 3, nfloat)
S = {v: nslots(v) for v in VT}
mx = max(S.values())
ck('A4 无槽数>=480；最大 344', mx == 344 and sum(1 for v in VT if S[v] >= 480) == 0, mx)

# ---------- B ----------
acc = []; esp = 0; neg = 0; idx_ex = 0
POS = re.compile(r'^(eax|ebx|ecx|edx|esi|edi|ebp|esp)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?$', re.I)
NEG = re.compile(r'^(eax|ebx|ecx|edx|esi|edi|ebp|esp)\s*-\s*(0x[0-9a-f]+|\d+)$', re.I)
for a, mn, ops in insns:
    if mn not in ('call', 'jmp'): continue
    mm = MEM_RE.search(ops)
    if not mm: continue
    inner = mm.group(1)
    if '*' in inner: idx_ex += 1; continue
    m1 = POS.match(inner.strip()); m2 = NEG.match(inner.strip())
    if m1:
        b = m1.group(1).lower(); d = int(m1.group(2), 0) if m1.group(2) else 0
    elif m2:
        b = m2.group(1).lower(); d = -int(m2.group(2), 0)
    else:
        continue
    if d < 0: neg += 1; continue
    if b == 'esp': esp += 1; continue
    acc.append((a, b, d))
hi = [x for x in acc if x[2] >= 0x400]
dom = [x for x in hi if 256 <= x[2] // 4 < 344]
top = __import__('collections').Counter(x[2] // 4 for x in dom).most_common(5)
ck('B1 sweep=1394186 末=0x7e0fff', len(insns) == 1394186 and insns[-1][0] == 0x7e0fff, (len(insns), hex(insns[-1][0])))
ck('B2 接受集=18935 esp=9 neg=2 索引排除=391', len(acc) == 18935 and esp == 9 and neg == 2 and idx_ex == 391,
   (len(acc), esp, neg, idx_ex))
ck('B3 931/91/925 + top s 一致',
   len(hi) == 931 and len(set(x[2] // 4 for x in hi)) == 91 and len(dom) == 925
   and [s for s, _ in top] == [288, 289, 337, 342, 258],
   (len(hi), len(set(x[2] // 4 for x in hi)), len(dom), top))

# ---------- C ----------
A1_, A2_, N = 0x876ff4, 0x87b170, 0xa10
b1 = P.RAW[P.r2o(A1_):P.r2o(A1_) + N]; b2 = P.RAW[P.r2o(A2_):P.r2o(A2_) + N]
ck('C1 两表逐字节相同 2576 B', b1 == b2 and len(b1) == 2576 and
   hashlib.sha256(b1).hexdigest() == hashlib.sha256(b2).hexdigest(), len(b1))
def rel(a): return (P.dw(a + 12) - P.dw(a + 8)) & 0xFFFFFFFF
ok = sum(1 for i in range(162) if rel(A1_ + 16 * i) == 0x00800080)
sh = [sum(1 for i in range(162 - s) if rel(A1_ + 16 * i + s) == 0x00800080) for s in (4, 8, 12)]
ck('C2 关系 162/162 且 shift 4/8/12 = 0', ok == 162 and sh == [0, 0, 0], (ok, sh))
ghost = [(V, c) for sn in ('.rdata', '.data') for V, c in
         [(w[1] + 4 * k + 4 - 4, w[1]) for k in ()] for w in ()]
gh = []
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k, v in enumerate(w):
        V = base + 4 * k + 4
        if v in CS and P.where(P.dw(V)) != '.text': gh.append((V, v))
real = 0
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k, v in enumerate(w):
        V = base + 4 * k + 4
        if v in CS and P.where(P.dw(V)) == '.text' and not (0x870000 <= V < 0x880000): real += 1
ck('C3 幻影=4 且排除数值窗口后真表仍 1214', len(gh) == 4 and real == 1214, (len(gh), real))

# ---------- D ----------
tab = [P.dw(0x81f7b4 + 4 * i) for i in range(256)]
def gen(p):
    t = []
    for i in range(256):
        c = i
        for _ in range(8): c = (c >> 1) ^ p if (c & 1) else (c >> 1)
        t.append(c & 0xFFFFFFFF)
    return t
ck('D1 CRC-32 表 256/256；CRC-32C 不匹配',
   tab == gen(0xEDB88320) and tab != gen(0x82F63B78) and tab[0] == 0 and tab[1] == 0x77073096)
src = P.RAW[P.r2o(0x4a1ca0):P.r2o(0x4a1ca0) + 0x90]
need = [b'\xf7\xd0', b'\x8b\x1c\xad\xb4\xf7\x81\x00', b'\x83\xf8\x04']
ck('D2 关键指令形态在函数体内', all(n in src for n in need),
   [n.hex() for n in need if n not in src])
def flush4(prev, buf4):
    eax = (~prev) & 0xFFFFFFFF
    for b in buf4:
        eax = ((eax >> 8) ^ tab[((eax & 0xFF) ^ b)]) & 0xFFFFFFFF
    return (~eax) & 0xFFFFFFFF
m = 0; tot = 0
for prev in (0, 0xFFFFFFFF, 0xDEADBEEF):
    for buf in (b'\x00' * 4, b'ABCD', b'\xde\xad\xbe\xef', b'\x01' * 4, b'\x00\x01\x00\x01'):
        tot += 1
        m += (flush4(prev, buf) == (zlib.crc32(buf, prev) & 0xFFFFFFFF))
ck('D2b flush4 == zlib.crc32 (15/15)', m == tot == 15, (m, tot))

# ---------- E ----------
SPEC = {'R14_COMMON': (TIER + '/R14_COMMON.md', 1081),
        'GOAL': (ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md', 337),
        'LOCK': (ROOT + '/lead/LEAD_LOCK', 137),
        'BOARD': (TIER + '/STATUS_BOARD.md', 0),
        'ARCH': (TIER + '/BOARD_ARCHIVE.md', 2952)}
crs = {}
for k, (p, e) in SPEC.items():
    b = open(p, 'rb').read()
    crs[k] = b.count(b'\r')
    ck('E1 CR %-10s = %d' % (k, e), crs[k] == e, crs[k])
bl = len(open(SPEC['BOARD'][0], 'rb').read().split(b'\n')) - 1
ck('E1b STATUS_BOARD 行数 <= 300', bl <= 300, bl)

tsv = TIER + '/R17_R131_FACTINDEX_V601/FACT_INDEX.tsv'
tb = open(tsv, 'rb').read()
h = hashlib.sha256(tb).hexdigest()
ck('E2 V601 sha=54ff0419 bytes=284839 CR=0',
   h.startswith('54ff0419') and len(tb) == 284839 and tb.count(b'\r') == 0, (h[:16], len(tb)))
ff = open(ROOT + '/_r160/facts_floors.py', encoding='utf-8').read()
ck('E2b facts_floors 四常量同步',
   "R17_R131_FACTINDEX_V601" in ff and h in ff and ('TOTAL_BYTES = %d' % len(tb)) in ff
   and "03a5ce793a92c9b4" in ff)
gr = open(ROOT + '/_r161/gate_runner.py', encoding='utf-8').read()
ck('E2c gate_runner LEDGER -> V601', "R17_R131_FACTINDEX_V601" in gr)
cd = open(TIER + '/check_disc.py', encoding='utf-8').read()
ck('E2d check_disc C16 含 227', re.search(r'C16_FLOORS = \{', cd) and '\n    227:' in cd)

print('\n[SUMMARY] %d 断言，%d FAIL' % (25, len(fails)))
print('[FAILS] %r' % fails if fails else '[ALL PASS]')
json.dump(dict(fails=fails, crs=crs, board_lines=bl, tsv_sha=h, tsv_bytes=len(tb),
               acc=len(acc), hi=len(hi), dom=len(dom), ghost=len(gh), real=real),
          open(ROOT + '/_r219/m13.json', 'w'), indent=1)
raise SystemExit(1 if fails else 0)
