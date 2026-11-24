"""W156 byte-scan channel (independent of Ghidra).
Finds, with verified instruction boundaries:
  (1) all WRITES to absolute [0xA8EB50]  (BuildingClass::Array.Count)
  (2) all call dword ptr [IAT] for HeapFree/HeapAlloc/VirtualFree/LocalFree/HeapReAlloc/VirtualAlloc
  (3) all absolute reads/writes of [0x87F924]
  (4) all direct calls to 0x5687F0
  (5) candidate writes to [reg + 0xE4/0xE8] with non-stack base -> second detach impl check
Also does a raw byte-pattern scan for 50 EB A8 00 as an independent cross-check,
verifying each raw hit lands on a decoded instruction boundary.
"""
import struct
import pefile
import capstone
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM, X86_REG_ESP, X86_REG_EBP
import w156_core as C

EXE = C.EXE
MD = C.MD

TARGET = 0x00A8EB50
TABLE = 0x0087F924
DETACH = 0x005687F0

# ---- parse import table for IAT slots ----
_pe_full = pefile.PE(EXE, fast_load=False)
iat = {}                 # VA -> (dll, funcname)
interest_va = set()
for entry in _pe_full.DIRECTORY_ENTRY_IMPORT:
    dll = entry.dll.decode(errors='replace')
    for imp in entry.imports:
        if imp.address and imp.name:
            fn = imp.name.decode(errors='replace')
            iat[imp.address] = (dll, fn)
            if fn in {'HeapFree','HeapAlloc','HeapReAlloc','LocalFree','VirtualFree',
                      'VirtualAlloc','malloc','free','RtlAllocateHeap','RtlFreeHeap'}:
                interest_va.add(imp.address)

print("=== IAT SLOTS (interesting) ===")
for va in sorted(interest_va):
    print("  IAT %08X  %s!%s" % (va, iat[va][0], iat[va][1]))

WRITE_MN = {'mov','movsx','movzx','inc','dec','add','sub','and','or','xor','adc','sbb',
            'neg','not','shl','shr','sal','sar','rol','ror','xchg','bts','btr','btc','pop','lea'}

def abs_mem_op(op):
    return op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0

hits_a8eb50_write = []
hits_a8eb50_any = []
hits_table = []
hits_detach_call = []
hits_iat_call = []
hits_iat_anyref = []
hits_celle4e8 = []
all_insn_addr = set()

for e in sorted(C.FUNC.keys()):
    insns = C.disas_fn(e, cap=8000)
    if not insns:
        continue
    for ins in insns:
        all_insn_addr.add(ins.address)
        t = ins.mnemonic
        ops = ins.operands
        for i, op in enumerate(ops):
            if abs_mem_op(op) and op.mem.disp in (TARGET, TABLE):
                d = op.mem.disp
                isw = (i == 0 and t in WRITE_MN)
                rec = (ins.address, e, ins.bytes.hex(), C.fmt(ins))
                if d == TARGET:
                    hits_a8eb50_any.append((rec, isw, t))
                    if isw:
                        hits_a8eb50_write.append(rec)
                else:
                    hits_table.append((ins.address, e, ins.bytes.hex(), C.fmt(ins),
                                       'W' if isw else 'R', t))
        if t == 'call' and len(ops) == 1 and ops[0].type == X86_OP_MEM and ops[0].mem.base == 0:
            a = ops[0].mem.disp
            if a in iat:
                dll, fn = iat[a]
                hits_iat_call.append((ins.address, e, a, dll, fn, C.fmt(ins)))
        for op in ops:
            if abs_mem_op(op) and op.mem.disp in interest_va:
                hits_iat_anyref.append((ins.address, e, op.mem.disp, C.fmt(ins)))
        if t == 'call' and len(ops) == 1 and ops[0].type == X86_OP_IMM and ops[0].imm == DETACH:
            hits_detach_call.append((ins.address, e, C.fmt(ins)))
        if t in WRITE_MN and len(ops) >= 1 and ops[0].type == X86_OP_MEM:
            m = ops[0].mem
            if m.disp in (0xE4, 0xE8) and m.base not in (X86_REG_ESP, X86_REG_EBP) and m.base != 0:
                hits_celle4e8.append((ins.address, e, m.disp, m.base, C.fmt(ins)))

# ---- output (1) ----
print("\n=== (1) WRITES to [0x00A8EB50] : %d sites ===" % len(hits_a8eb50_write))
fnset = set()
for site, fn, bb, txt in sorted(hits_a8eb50_write):
    fnset.add(fn)
    print("  site=%08X fn=%s bytes=%s" % (site, C.fn_label(fn), bb))
    print("      " + txt)
print("  --- distinct owning functions: %d ---" % len(fnset))
for fn in sorted(fnset):
    sites = [h[0] for h in hits_a8eb50_write if h[1] == fn]
    print("  %s  writes@ %s" % (C.fn_label(fn), ",".join("%08X"%s for s in sites)))

print("\n=== (1b) ALL refs to [0x00A8EB50] (W or R): %d ===" % len(hits_a8eb50_any))
for rec, isw, t in sorted(hits_a8eb50_any):
    site, fn, bb, txt = rec
    print("  %s %s site=%08X fn=%s  %s" % ('W' if isw else 'R', t, site, C.fn_label(fn), txt))

# ---- raw byte cross-check for 50 EB A8 00 ----
print("\n=== (1c) RAW byte pattern '50 EB A8 00' scan (independent) ===")
name, vstart, praw, rsize = C.sec_of(0x401000)
# find .text section explicitly
text_sec = None
for (vstart2, vsize, praw2, rsize2, nm) in C._secs:
    if nm == '.text':
        text_sec = (vstart2, praw2, rsize2)
        break
if text_sec is None:
    # fallback first executable
    text_sec = (C._secs[0][0], C._secs[0][2], C._secs[0][3])
tva, praw, rsz = text_sec
blob = C._blob
pat = b'\x50\xeb\xa8\x00'
raw_hits = []
i = 0
while True:
    j = blob.find(pat, praw + i, praw + rsz)
    if j < 0:
        break
    va = tva + (j - praw)
    raw_hits.append(va)
    i = j - praw + 1
onb = [va for va in raw_hits if va in all_insn_addr]
offb = [va for va in raw_hits if va not in all_insn_addr]
print("  raw hits=%d  on-instruction-boundary=%d  off-boundary=%d" % (len(raw_hits), len(onb), len(offb)))
print("  on-boundary: " + ",".join("%08X"%v for v in sorted(onb)))
print("  off-boundary: " + ",".join("%08X"%v for v in sorted(offb)))

# ---- output (2) IAT calls ----
print("\n=== (2) call [IAT] sites : %d ===" % len(hits_iat_call))
for site, fn, a, dll, f, txt in sorted(hits_iat_call):
    print("  site=%08X fn=%s IAT=%08X %s!%s" % (site, C.fn_label(fn), a, dll, f))
    print("      " + txt)
print("  --- count by function ---")
from collections import Counter
cnt = Counter(f for (_,_,_,_,f,_) in hits_iat_call)
for f, n in sorted(cnt.items()):
    print("  %-16s %d" % (f, n))
print("  --- ALL absolute refs to interesting IAT (not just call): %d ---" % len(hits_iat_anyref))
for site, fn, a, txt in sorted(hits_iat_anyref):
    print("  site=%08X fn=%s IAT=%08X (%s)  %s" % (site, C.fn_label(fn), a, iat[a][1], txt))

# ---- output (3) table ----
W = [h for h in hits_table if h[4] == 'W']
R = [h for h in hits_table if h[4] == 'R']
print("\n=== (3) [0x0087F924] : reads=%d writes=%d ===" % (len(R), len(W)))
for site, fn, bb, txt, mode, t in sorted(hits_table):
    if mode == 'W':
        print("  W site=%08X fn=%s  %s" % (site, C.fn_label(fn), txt))
print("  (reads omitted; count only)")

# ---- output (4) detach ----
print("\n=== (4) direct calls to 0x005687F0 : %d ===" % len(hits_detach_call))
for site, fn, txt in sorted(hits_detach_call):
    print("  site=%08X fn=%s  %s" % (site, C.fn_label(fn), txt))

# ---- output (5) cell +E4/E8 ----
print("\n=== (5) writes to [reg+0xE4/+0xE8] non-stack base : %d sites ===" % len(hits_celle4e8))
fnset5 = set(h[1] for h in hits_celle4e8)
print("  distinct fns=%d" % len(fnset5))
for fn in sorted(fnset5):
    sub = [h for h in hits_celle4e8 if h[1] == fn]
    print("  %s :" % C.fn_label(fn))
    for site,_,disp,base,txt in sorted(sub):
        print("      site=%08X +0x%X basereg=%d  %s" % (site, disp, base, txt))
