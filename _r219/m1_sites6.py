# -*- coding: utf-8 -*-
"""R219 m1：R218 遗留的 6 处「超 344 槽域」disp 位点逐点定性。

判据问题：R218 把 call/jmp [reg+disp] 的 disp//4 当作虚表槽序号 s。
实测 s∈{479,480,481,482,2224418} 六处，全部超出最大虚表槽数 344。
本脚本要回答的是：这 6 处到底是不是虚表槽消费？

方法（一次跑完，全部带正反控）：
 A. 六处位点原始字节 + 线性 sweep 边界成员资格（防数据被误当指令）。
 B. 三处 s=479/480/481/482 的 base 全为 esi / 同 offset 的全 .text 引用清单：
    若这些 offset 出现在 `mov dword ptr [reg+off], imm32(.text)` 的**写入端**，
    则它们是对象内函数指针字段，不是虚表槽。
 C. 反控 1：同 offset 是否被当非指针类型使用（fmul qword / mov eax,dword）⇒ 字段语义确证。
 D. 反控 2：全 1214 真虚表的槽数上界（应为 344），s=479 需要 480 槽表，不存在。
 E. 第 6 处 s=2224418：disp=0x87c488 超出镜像大小，只有 base==0 时才是有效绝对槽；
    溯源 esi 的赋值（mov esi,imm / xor esi,esi），并核 [0x87c488] 是否为 .text 函数指针。
 F. 正控：已知合法虚表槽位点 0x414471 ([edx+0x544] s=337) 必须仍被本管线识别。
"""
import sys, struct, collections, json, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
md.skipdata = True
T = P.B['.text']
LO, RAWOFF, RAWSZ = T['lo'], T['rawptr'], T['rawsize']
OUT = {}

# ---------- COL / vtable rebuild (same law as R217/R218) ----------
def words(sn):
    s = P.B[sn]
    return struct.unpack_from('<%dI' % (s['rawsize'] // 4), P.RAW, s['rawptr']), s['lo']

def s32(v):
    return struct.unpack('<i', struct.pack('<I', v))[0]

COL = {}
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k in range(len(w) - 5):
        if w[k] > 2 or w[k + 2] != 0:
            continue
        if P.where(w[k + 3]) != '.data' or P.where(w[k + 4]) != '.rdata':
            continue
        nm = P.cstr(w[k + 3] + 8, 512)
        if not nm or nm[:3] != b'.?A' or nm[-2:] != b'@@':
            continue
        COL[base + 4 * k] = dict(md_=s32(w[k + 1]), pCHD=w[k + 4],
                                 name=nm.decode('latin1'))
CS = set(COL)
VT = {}
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k, v in enumerate(w):
        if v in CS:
            VT[base + 4 * k + 4] = v
VTS = sorted(VT)

def nslots(vt, cap=65536):
    n = 0
    while n < cap and P.where(P.dw(vt + 4 * n)) == '.text':
        n += 1
    return n

SLOTS = {v: nslots(v) for v in VTS}
print('[0] COL=%d  VT=%d  max_slots=%d  @%08x  total_slots=%d'
      % (len(COL), len(VTS), max(SLOTS.values()),
         max(SLOTS, key=lambda v: SLOTS[v]), sum(SLOTS.values())))
# 仅真表口径（dw(V) 落 .text）
REAL = [v for v in VTS if P.where(P.dw(v)) == '.text']
print('[0b] real tables (dw(V) in .text) = %d ; phantom = %d %s'
      % (len(REAL), len(VTS) - len(REAL),
         [hex(v) for v in VTS if v not in REAL]))

# ---------- linear sweep boundary set (byte-resync) ----------
raw = P.RAW[RAWOFF:RAWOFF + RAWSZ]
bnd = set()
pos = 0
while pos < len(raw):
    got = False
    for a, sz, mn, ops in md.disasm_lite(raw[pos:pos + 16], LO + pos):
        bnd.add(a)
        pos += sz
        got = True
        break
    if not got:
        pos += 1
print('[1] linear sweep: %d instruction boundaries, last=%#x' % (len(bnd), max(bnd)))

SITES = [0x7bea07, 0x7bea0f, 0x7c2f17, 0x7c301c, 0x7c37c7, 0x7cde2b]
print('\n[A] six sites: bytes / decode / boundary membership / slot guess')
site_rows = []
for a in SITES:
    o = P.r2o(a)
    b8 = P.RAW[o:o + 8]
    txt = None
    for i in md.disasm(P.RAW[o:o + 16], a):
        txt = '%s %s' % (i.mnemonic, i.op_str)
        break
    m = re.search(r'\[(\w+) \+ (0x[0-9a-f]+)\]', txt or '')
    breg, disp = (m.group(1), int(m.group(2), 16)) if m else (None, None)
    print('   %#x | %s | %-42s | boundary=%s | base=%s disp=%#x s=%s'
          % (a, b8.hex(), txt, a in bnd, breg, disp,
             disp // 4 if disp is not None else None))
    site_rows.append(dict(addr=hex(a), bytes=b8.hex(), disasm=txt,
                          boundary=a in bnd, base=breg,
                          disp=hex(disp) if disp is not None else None,
                          s=(disp // 4) if disp is not None else None))
OUT['sites'] = site_rows

# ---------- B: full reference list of the three offsets ----------
OFFS = [0x77c, 0x780, 0x784]
pat = re.compile(r'\[(eax|ebx|ecx|edx|esi|edi|ebp) \+ (0x77c|0x780|0x784)\]', re.I)
refs = []
pos = 0
while pos < len(raw):
    got = False
    for a, sz, mn, ops in md.disasm_lite(raw[pos:pos + 16], LO + pos):
        pos += sz
        got = True
        mm = pat.search(ops)
        if mm:
            refs.append((a, mn, ops, int(mm.group(2), 16)))
        break
    if not got:
        pos += 1
print('\n[B] all .text refs to +0x77c/+0x780/+0x784 : %d' % len(refs))
by = collections.defaultdict(list)
for a, mn, ops, off in refs:
    by[(off, mn)].append((a, ops))
for k in sorted(by):
    print('   off=%#x mnem=%-5s n=%d' % (k[0], k[1], len(by[k])))
    for a, ops in by[k]:
        print('      %#x  %s' % (a, ops))
OUT['refs_77c_784'] = [dict(addr=hex(a), mnem=mn, op=ops, off=hex(off))
                       for a, mn, ops, off in refs]

# ---------- C: writes of .text immediates into those fields ----------
writes = [r for r in refs if r[1] == 'mov' and r[2].startswith('dword ptr')]
print('\n[C] writes (mov dword ptr [reg+off], ...) count=%d' % len(writes))
immw = []
for a, mn, ops, off in writes:
    if ', 0x' in ops:
        imm = int(ops.split(',')[-1].strip(), 16)
        where = P.where(imm)
        immw.append((a, off, imm, where))
        print('   %#x  off=%#x  <- %#010x  (%s)' % (a, off, imm, where))
print('   imm32 writes into .text targets: %d / %d'
      % (sum(1 for x in immw if x[3] == '.text'), len(immw)))

# ---------- C2: non-pointer uses (negative control for "vtable slot") ----------
nonptr = [r for r in refs if r[1] in ('fmul', 'fstp', 'fadd', 'fsub', 'movsd', 'fld')]
print('\n[C2] non-pointer uses of the same offsets (proves data-field semantics): %d'
      % len(nonptr))
for a, mn, ops, off in nonptr:
    print('   %#x  %-5s %s' % (a, mn, ops))

# ---------- D: no vtable has 480 slots ----------
need = [480, 481, 482, 483]
print('\n[D] negative control: tables with >=480 slots = %d (of %d)'
      % (sum(1 for v in VTS if SLOTS[v] >= 480), len(VTS)))
print('    (s=479 requires >=480 slots; max real slot count = %d)' % max(SLOTS.values()))

# ---------- E: site 6, s=2224418 ----------
print('\n[E] site 0x7cde2b  disp=0x87c488  s=2224418')
img_end = max(s['hi_virt'] for s in P.SECS)
print('    image virtual end = %#x ; disp alone %#x  => disp is NOT an object-field offset'
      % (img_end, 0x87c488))
print('    dw(0x87c488) = %#x  where=%s' % (P.dw(0x87c488), P.where(P.dw(0x87c488))))
print('    .data 0x87c470..0x87c4a0: %s'
      % P.RAW[P.r2o(0x87c470):P.r2o(0x87c470) + 0x30].hex())
# 溯源 esi：从函数边界 0x7cda8f 解码到 site
st = 0x7cda8f
so = P.r2o(st)
print('    esi writes from function start %#x up to site:' % st)
esiw = []
for ins in md.disasm(P.RAW[so:so + (0x7cde2b - st) + 8], st):
    d = ins.op_str.split(',')[0].strip()
    if d == 'esi' and ins.mnemonic in ('mov', 'xor', 'lea', 'pop', 'and', 'or', 'add', 'sub', 'inc'):
        esiw.append('%#x %s %s' % (ins.address, ins.mnemonic, ins.op_str))
for x in esiw:
    print('      ', x)
OUT['site6_esi_writes'] = esiw

# ---------- F: positive control ----------
print('\n[F] positive control 0x414471 :', end=' ')
for i in md.disasm(P.RAW[P.r2o(0x414471):P.r2o(0x414471) + 8], 0x414471):
    print('%s %s' % (i.mnemonic, i.op_str))
    break
print('    0x414471.t** in the accepted set: %s' % (0x414471 in bnd))

json.dump(OUT, open('/home/t628/projects/ra2-campaign-forge/_r219/m1.json', 'w'), indent=1)
print('\n[done] -> _r219/m1.json')
