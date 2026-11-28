# -*- coding: utf-8 -*-
"""R219 m3：① 0x77c/0x780/0x784 三个字段的宿主类定位；② C_neither 71 扩展窗口复核；
③ 0x87c488 所在 12 字节静态派发表的结构与项数。

正控：
  - 已知写入端 0x7be6c9/0x7be6dd/0x7be6e9/0x7be6f3/0x7be6ff/0x7be709/0x7be741/0x7be75a/0x7be773/
    0x7be7c1/0x7be7df/0x7be7f8/0x7c3234/0x7c323c 共 14 条必须全部找回。
反控：
  - 把「宿主类」判据放宽到「任意虚表任一槽落在 [f, f+0x400)」必须给出多解（证明需要更严的判据）；
  - 0x87c488 表的项数按 cmp edi, 0x87c4c0 上界与步长 12 计算必须为整数项数。
"""
import sys, struct, collections, json, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

def words(sn):
    s = P.B[sn]
    return struct.unpack_from('<%dI' % (s['rawsize'] // 4), P.RAW, s['rawptr']), s['lo']
def s32(v):
    return struct.unpack('<i', struct.pack('<I', v))[0]

# ---- vtable rebuild (same law) ----
COL = {}
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k in range(len(w) - 5):
        if w[k] > 2 or w[k + 2] != 0: continue
        if P.where(w[k + 3]) != '.data' or P.where(w[k + 4]) != '.rdata': continue
        nm = P.cstr(w[k + 3] + 8, 512)
        if not nm or nm[:3] != b'.?A' or nm[-2:] != b'@@': continue
        COL[base + 4 * k] = dict(md_=s32(w[k + 1]), pCHD=w[k + 4], name=nm.decode('latin1'))
CS = set(COL); VT = {}
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k, v in enumerate(w):
        if v in CS: VT[base + 4 * k + 4] = v

def nslots(vt, cap=65536):
    n = 0
    while n < cap and P.where(P.dw(vt + 4 * n)) == '.text': n += 1
    return n
SLOTS = {v: nslots(v) for v in VT}
print('[0] vtables=%d max_slots=%d' % (len(VT), max(SLOTS.values())))

# ---- (1) which vtable owns the function that writes +0x77c/+0x780/+0x784 ----
WRITERS = [0x7be6c9, 0x7be6dd, 0x7be6e9, 0x7be6f3, 0x7be6ff, 0x7be709, 0x7be741,
           0x7be75a, 0x7be773, 0x7be7c1, 0x7be7df, 0x7be7f8, 0x7c3234, 0x7c323c]
# caller function start for each writer: nearest >=2x0xCC padding before, else after last 0xC3
def func_start(va, window=1024):
    o = P.r2o(va)
    lo = max(P.r2o(P.B['.text']['lo']), o - window)
    best = None
    i = o - 1
    while i > lo:
        if P.RAW[i - 1] == 0xCC and P.RAW[i] == 0xCC:
            j = i
            while j < o and P.RAW[j] == 0xCC: j += 1
            best = j; break
        i -= 1
    if best is None:
        i = o - 1
        while i > lo:
            if P.RAW[i] == 0xC3 and P.RAW[i + 1] != 0xCC:
                best = i + 1; break
            i -= 1
    if best is None: return None, 'unresolved'
    return best + (P.B['.text']['lo'] - P.B['.text']['rawptr']), 'ok'

BASE = P.B['.text']['lo'] - P.B['.text']['rawptr']
fstarts = {}
for w in WRITERS:
    f, why = func_start(w)
    fstarts[w] = f
    print('[1] writer %#x -> func_start %s (%s)' % (w, hex(f) if f else None, why))
# which vtables contain any slot pointing into each func range
def hosts_of_funcs(fs):
    out = collections.defaultdict(list)
    for vt in sorted(VT):
        n = SLOTS[vt]
        for k in range(n):
            t = P.dw(vt + 4 * k)
            if t in fs:
                out[vt].append((k, t))
    return out
fset = set(f for f in fstarts.values() if f)
print('[1b] distinct writer func starts = %d : %s' % (len(fset), [hex(x) for x in sorted(fset)]))
hosts = hosts_of_funcs(fset)
print('[1c] vtables with a slot hitting one of those func starts: %d' % len(hosts))
for vt, lst in sorted(hosts.items()):
    print('     %08x %-30s slots=%d hits=%s'
          % (vt, COL[VT[vt]]['name'], SLOTS[vt], [(k, hex(t)) for k, t in lst][:8]))
# negative control: allow any slot target within [f, f+0x400)
fc = collections.defaultdict(list)
for vt in sorted(VT):
    for k in range(SLOTS[vt]):
        t = P.dw(vt + 4 * k)
        for f in fset:
            if f <= t < f + 0x400:
                fc[vt].append((k, t))
print('[1d] NEGATIVE CONTROL (slot target only within [f,f+0x400), not equal to f): %d vtables' % len(fc))

# ---- (2) C_neither recheck with a 24-instruction window ----
T = P.B['.text']; LO, RAWOFF, RAWSZ = T['lo'], T['rawptr'], T['rawsize']
raw = P.RAW[RAWOFF:RAWOFF + RAWSZ]
insns = []
pos = 0
while pos < len(raw):
    got = False
    for a, sz, mn, ops in md.disasm_lite(raw[pos:pos + 16], LO + pos):
        insns.append((a, mn, ops)); pos += sz; got = True; break
    if not got: pos += 1
print('\n[2] sweep %d insns' % len(insns))
MEM_RE = re.compile(r'\bptr\s*\[([^\]]+)\]', re.I)
SIMPLE = re.compile(r'^(eax|ebx|ecx|edx|esi|edi|ebp)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?$', re.I)
GPR = ('eax','ebx','ecx','edx','esi','edi','ebp')
def parse_mem(s):
    m = SIMPLE.match(s.strip())
    if not m: return None, None
    return m.group(1).lower(), (int(m.group(2), 0) if m.group(2) else 0)
calls = []
for idx, (a, mn, ops) in enumerate(insns):
    if mn not in ('call', 'jmp'): continue
    mm = MEM_RE.search(ops)
    if not mm: continue
    b, d = parse_mem(mm.group(1))
    if b is None or b == 'esp': continue
    calls.append((idx, a, b, d))
hi = [c for c in calls if c[3] >= 0x400]
print('[2b] hi(disp>=0x400) = %d' % len(hi))

def cls(idx, base, disp, win=24):
    lo = max(0, idx - win)
    A = B = None
    for a2, m2, o2 in reversed(insns[lo:idx]):
        if B is None and m2 == 'mov' and 'dword ptr [' in o2 and ',' in o2:
            dst, _, src = o2.partition(',')
            mm = MEM_RE.search(dst)
            if mm:
                bo, dd = parse_mem(mm.group(1))
                src = src.strip()
                if bo in GPR and dd == disp and (src.startswith('0x') or src in GPR):
                    B = '%#x %s %s' % (a2, m2, o2)
        if A is None and m2 == 'mov' and 'dword ptr [' in o2 and o2.split(',')[0].strip() == base:
            mm = MEM_RE.search(o2)
            if mm:
                bo, dd = parse_mem(mm.group(1))
                if bo in GPR and dd == 0:
                    A = '%#x %s %s' % (a2, m2, o2)
        if A and B: break
    return A, B
cnt = collections.Counter(); cnei = []
for idx, a, b, d in hi:
    A, B = cls(idx, b, d)
    k = 'A_vtable' if (A and not B) else 'B_field' if (B and not A) else 'AB_both' if (A and B) else 'C_neither'
    cnt[k] += 1
    if k == 'C_neither': cnei.append((a, b, d))
print('[2c] window=24 classification:', dict(cnt))
print('     C_neither n=%d  first 20:' % len(cnei))
for a, b, d in cnei[:20]:
    print('       %#x base=%s disp=%#x s=%d' % (a, b, d, d // 4))
# positive control on window=24: 0x414471 must still be A
for idx, a, b, d in hi:
    if a == 0x414471:
        print('     POSITIVE CONTROL 0x414471 ->', cls(idx, b, d))

# ---- (3) the 12-byte static dispatch table at 0x87c488 ----
print('\n[3] static dispatch table around 0x87c488')
start = 0x87c488
end_bound = 0x87c4c0
n = (end_bound - start) // 12
print('    cmp edi, 0x87c4c0 upper bound; step 12 from %#x => (0x%x)/12 = %d rem %d'
      % (start, end_bound - start, (end_bound - start) // 12, (end_bound - start) % 12))
for i in range((end_bound - start) // 12 + 1):
    a = start + 12 * i
    w = [P.dw(a + 4 * j) for j in range(3)]
    print('    [%d] %#x : %08x %08x %08x   (where: %s %s %s)'
          % (i, a, *w, P.where(w[0]), P.where(w[1]), P.where(w[2])))
# also check the alternate start 0x87c484
print('    alt start 0x87c484:')
for i in range((end_bound - 0x87c484) // 12 + 1):
    a = 0x87c484 + 12 * i
    w = [P.dw(a + 4 * j) for j in range(3)]
    print('    [%d] %#x : %08x %08x %08x' % (i, a, *w))

json.dump(dict(writer_funcs={hex(k): (hex(v) if v else None) for k, v in fstarts.items()},
               hosts={hex(k): v for k, v in hosts.items()},
               negctl_vtables=len(fc),
               cls24=dict(cnt), cneither=[(hex(a), b, hex(d)) for a, b, d in cnei]),
          open('/home/t628/projects/ra2-campaign-forge/_r219/m3.json', 'w'), indent=1)
print('\n[done] -> _r219/m3.json')
