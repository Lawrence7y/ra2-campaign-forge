# -*- coding: utf-8 -*-
"""R219 m2：判别 R218 的「disp//4 = 虚表槽序号 s」口径是否成立。

起因：m1 已证 6 处超域位点里，
  - 0x7bea07/0x7bea0f/0x7c2f17/0x7c301c/0x7c37c7 的 disp 是对象内**函数指针字段**偏移
    (+0x77c/0x780/0x784)，写入端是 mov dword ptr [reg+off], imm32(.text) 共 12 条，
    且同 offset 还被 fmul/fstp qword 当 double 用 => 不是虚表槽；
  - 0x7cde2b 的 esi = edi*12，disp=0x87c488 是 12 字节静态派发表基址，也不是虚表槽。

因此必须检验：disp 落在 0x400..0x55c（R218 认定的 s=256..343 "UnitClass 槽域"）的位点，
到底是 (A) 虚表槽消费 call [vtableptr + 4*s]，还是 (B) 对象内函数指针字段 call [obj + 4*s]。

判别判据（对每个位点看其前驱指令）：
  A 类签名：位点前 <=6 条指令内出现 `mov <r>, dword ptr [<obj>]`（读对象首 dword = vftable），
            且 call 的 base 寄存器与之一致（中间未被覆写）。
  B 类签名：位点前 <=6 条指令内出现 `mov dword ptr [<reg> + <同一 disp>], imm32` 或
            `mov dword ptr [<reg> + <同一 disp>], <reg>`（对同一字段的写入）。
  C 类：两者都不满足。

另外做两条独立的全局判据：
  G1：全 .text 里 `mov dword ptr [reg+disp], imm32(落 .text)` 的 disp 直方图 ——
      若 0x400..0x55c 区间有大量这种写入，则 B 类在这段占主导。
  G2：全 .text 里 `mov reg, dword ptr [reg2]`（读 vftable，即 offset 0）出现次数，
      作为 A 类通道存在性的正控。

正控：0x414471 处 call [edx+0x544]（R218 记为 s=337）必须被本脚本归类并打印其前驱。
反控：把 disp 阈值改成 < 0x400（低槽区）重复 A/B/C 统计，若 A 类占比在低槽区显著更高，
      说明高槽区确实是另一套机制。
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
raw = P.RAW[RAWOFF:RAWOFF + RAWSZ]
CHUNK = 0x10000

MEM_RE = re.compile(r'\bptr\s*\[([^\]]+)\]', re.I)
GPR = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')
SIMPLE = re.compile(r'^(eax|ebx|ecx|edx|esi|edi|ebp)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?$', re.I)

def parse_mem(inner):
    s = inner.strip()
    m = SIMPLE.match(s)
    if not m:
        return None, None
    d = 0
    if m.group(2):
        d = int(m.group(2), 0)
    return m.group(1).lower(), d

# ---------- pass 1: linear sweep, collect (a) indirect call/jmp [reg+disp] ----------
# and keep a small ring buffer of previous instructions for signature checks
insns = []           # (addr, mnem, ops) -- full list (1.39M tuples, lite only)
cur_va, cur_off, remaining = LO, RAWOFF, RAWSZ
nchunks = 0
while remaining > 0:
    n = min(CHUNK, remaining)
    buf = P.RAW[cur_off:cur_off + n]
    last_addr, last_size = None, 0
    for addr, size, mnem, opstr in md.disasm_lite(buf, cur_va):
        insns.append((addr, mnem, opstr))
        last_addr, last_size = addr, size
    if last_addr is None:
        break
    adv = (last_addr + last_size) - cur_va
    if adv <= 0:
        adv = n
    cur_va += adv; cur_off += adv; remaining -= adv
    nchunks += 1
    del buf
print('[1] linear sweep: %d instructions, chunks=%d, va range %#x..%#x'
      % (len(insns), nchunks, insns[0][0], insns[-1][0]))

# ---------- collect indirect call/jmp ----------
calls = []   # (idx, addr, base, disp)
for idx, (addr, mnem, opstr) in enumerate(insns):
    if mnem not in ('call', 'jmp'):
        continue
    mm = MEM_RE.search(opstr)
    if not mm:
        continue
    base, disp = parse_mem(mm.group(1))
    if base is None or base == 'esp':
        continue
    calls.append((idx, addr, base, disp))
print('[2] indirect call/jmp [reg+disp] (base in GPR, esp excluded) = %d' % len(calls))
print('    positive control 0x414471 present: %s'
      % any(c[1] == 0x414471 for c in calls))

# ---------- signature classification ----------
def classify(idx, base, disp):
    """Look back <=8 instructions for A/B signatures."""
    lo = max(0, idx - 8)
    win = insns[lo:idx]
    A = B = None
    for a2, m2, o2 in reversed(win):
        # B: write to the same field
        if m2 == 'mov' and o2.startswith('dword ptr') or (m2 == 'mov' and 'dword ptr [' in o2 and ',' in o2):
            dst, _, src = o2.partition(',')
            mm = MEM_RE.search(dst)
            if mm:
                bo, dd = parse_mem(mm.group(1))
                if bo in GPR and dd == disp:
                    src = src.strip()
                    if src.startswith('0x') or src in GPR:
                        B = '%#x %s %s' % (a2, m2, o2)
                        break
        # A: vftable load
        if m2 == 'mov' and 'dword ptr [' in o2 and o2.split(',')[0].strip() == base:
            mm = MEM_RE.search(o2)
            if mm:
                bo, dd = parse_mem(mm.group(1))
                if bo in GPR and dd == 0:
                    A = '%#x %s %s' % (a2, m2, o2)
                    break
    return A, B

hi = [c for c in calls if c[3] >= 0x400]
lo_ = [c for c in calls if c[3] < 0x400]
stat = {}
for label, grp in (('disp>=0x400', hi), ('disp<0x400', lo_)):
    cnt = collections.Counter()
    samples = collections.defaultdict(list)
    for idx, addr, base, disp in grp:
        A, B = classify(idx, base, disp)
        k = 'A_vtable' if (A and not B) else 'B_field' if (B and not A) else \
            'AB_both' if (A and B) else 'C_neither'
        cnt[k] += 1
        if len(samples[k]) < 6:
            samples[k].append((hex(addr), base, hex(disp), A, B))
    stat[label] = dict(cnt)
    print('\n[3] %s  n=%d' % (label, len(grp)))
    tot = len(grp)
    for k, v in cnt.most_common():
        print('    %-10s %5d  (%.1f%%)' % (k, v, 100.0 * v / tot))
    for k in ('A_vtable', 'C_neither'):
        for s in samples[k]:
            print('      sample %-9s %s base=%s disp=%s A=%s B=%s' % (k, s[0], s[1], s[2], s[3], s[4]))

# ---------- G1: writes of .text imm32 into [reg+disp] ----------
wcnt = collections.Counter()
wex = collections.defaultdict(list)
for addr, mnem, opstr in insns:
    if mnem != 'mov' or ',' not in opstr:
        continue
    dst, _, src = opstr.partition(',')
    if 'dword ptr [' not in dst:
        continue
    src = src.strip()
    if not src.startswith('0x'):
        continue
    try:
        imm = int(src, 16)
    except ValueError:
        continue
    if P.where(imm) != '.text':
        continue
    mm = MEM_RE.search(dst)
    if not mm:
        continue
    bo, dd = parse_mem(mm.group(1))
    if bo is None:
        continue
    wcnt[dd] += 1
    if len(wex[dd]) < 3:
        wex[dd].append('%#x' % addr)
hiw = {d: c for d, c in wcnt.items() if 0x400 <= d <= 0x560}
print('\n[G1] mov dword ptr [reg+disp], imm32(.text) : total distinct disp=%d, total=%d'
      % (len(wcnt), sum(wcnt.values())))
print('    in 0x400..0x560 : %d distinct disp, %d sites' % (len(hiw), sum(hiw.values())))
for d in sorted(hiw)[:30]:
    print('      disp=%#05x s=%3d  n=%d  at %s' % (d, d // 4, hiw[d], wex[d]))

# ---------- G2: vftable loads (mov reg, [reg2+0]) ----------
nvt = 0
for addr, mnem, opstr in insns:
    if mnem != 'mov':
        continue
    dst, _, src = opstr.partition(',')
    if 'dword ptr [' not in src:
        continue
    mm = MEM_RE.search(src)
    if not mm:
        continue
    bo, dd = parse_mem(mm.group(1))
    if bo in GPR and dd == 0 and dst.strip() in GPR:
        nvt += 1
print('\n[G2] positive control: `mov reg, dword ptr [reg2]` (vftable load) count = %d' % nvt)

json.dump(dict(calls=len(calls), hi=len(hi), stat=stat,
               g1_distinct=len(wcnt), g1_total=sum(wcnt.values()),
               g1_hi_distinct=len(hiw), g1_hi_total=sum(hiw.values()),
               g1_hi={hex(k): v for k, v in hiw.items()}, g2=nvt),
          open('/home/t628/projects/ra2-campaign-forge/_r219/m2.json', 'w'), indent=1)
print('\n[done] -> _r219/m2.json')
