# a-S17-ENGFAM audit, script a6: liveness root proof + vtable intersection + ctor probe of sampled vectors
import pefile, capstone, struct, os, bisect
from capstone import *
from collections import deque

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17_ENGFAM\EVIDENCE"
IB = 0x400000
pe = pefile.PE(EXE, fast_load=True)
IBH = pe.OPTIONAL_HEADER.ImageBase
EP = IBH + pe.OPTIONAL_HEADER.AddressOfEntryPoint
print("entry point = 0x%08X" % EP)
d = bytes(pe.__data__)
def va2off(va): return pe.get_offset_from_rva(va - IB)
def read(va, n): return d[va2off(va):va2off(va)+n]
def dw(va): return struct.unpack("<I", read(va, 4))[0]

TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
md = capstone.Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True
code = read(TEXT_LO, TEXT_HI-TEXT_LO)
call_sites = {}
callers_of = {}
imm_refs = {}
for insn in md.disasm(code, TEXT_LO):
    if insn.mnemonic == ".byte": continue
    try: ops = list(insn.operands)
    except capstone.CsError: continue
    if insn.mnemonic == "call" and ops and ops[0].type == capstone.x86.X86_OP_IMM:
        t = ops[0].imm & 0xFFFFFFFF
        call_sites.setdefault(t, []).append(insn.address)
        callers_of.setdefault(t, []).append(insn.address)
    for op in ops:
        if op.type == capstone.x86.X86_OP_IMM:
            v = op.imm & 0xFFFFFFFF
            if 0x800000 <= v <= 0xC00000:  # data/bss range quick filter
                imm_refs.setdefault(v, []).append((insn.address, insn.mnemonic, insn.op_str))

fstarts = sorted(set(call_sites.keys()))
def containing(addr):
    i = bisect.bisect_right(fstarts, addr) - 1
    return fstarts[i] if i >= 0 else None

SCANS = [(0x7E1000, 0x811074), (0x812000, 0x87E000)]
tds = {}
for lo, hi in SCANS:
    buf = read(lo, hi-lo); i = 0
    while True:
        i = buf.find(b".?A", i)
        if i < 0: break
        end = buf.find(b"\x00", i)
        tds[lo+i-8] = buf[i:end].decode(errors="replace"); i += 3
cols = {}
for lo, hi in SCANS:
    buf = read(lo, hi-lo)
    for off in range(0, len(buf)-0x10, 4):
        if struct.unpack_from("<I", buf, off)[0] == 0 and struct.unpack_from("<I", buf, off+0xC)[0] in tds:
            cols[lo+off] = struct.unpack_from("<I", buf, off+0xC)[0]
vts = {}
for lo, hi in SCANS:
    buf = read(lo, hi-lo)
    for off in range(4, len(buf)-4, 4):
        p = lo+off
        if dw(p-4) in cols:
            funcs = []; q = p
            while True:
                try: v = dw(q)
                except Exception: break
                if TEXT_LO <= v < TEXT_HI: funcs.append(v); q += 4
                else: break
            if len(funcs) >= 2: vts[p] = (tds[cols[dw(p-4)]], funcs)
func2vt = {}
for vt, (td, funcs) in vts.items():
    for f in funcs:
        func2vt.setdefault(f, []).append((vt, td, funcs.index(f), len(funcs)))

lines = []
# ---- 1. full reverse closure from 3 roots ----
roots = [0x4C6CB0, 0x559C20, 0x55D360]
closure = set()
q = deque(roots)
while q and len(closure) < 4000:
    fn = q.popleft()
    if fn in closure: continue
    closure.add(fn)
    # callers: every call site whose containing function is fn -> but we need per-function reverse edges.
    # build lazily: for target fn, its callers = containers of call_sites[fn]
    for s in call_sites.get(fn, []):
        c = containing(s)
        if c and c not in closure:
            q.append(c)
print("reverse closure size:", len(closure))
vt_hits = {f: func2vt[f] for f in closure if f in func2vt}
lines.append("== reverse closure of 3 roots: %d functions; vtable-member members: %d ==" % (len(closure), len(vt_hits)))
for f, v in sorted(vt_hits.items())[:40]:
    lines.append("  0x%08X in %s" % (f, v[:2]))
lines.append("")

# ---- 2. entry -> WinMain -> forward reach ----
lines.append("== startup stub ==")
stub = []
for insn in md.disasm(read(EP, 0x60), EP):
    stub.append("  0x%08X  %-18s %s %s" % (insn.address, " ".join("%02X"%b for b in insn.bytes), insn.mnemonic, insn.op_str))
lines.extend(stub)
print("\n".join(stub))

# forward BFS from EP's containing region candidates: take all call targets in stub
stub_targets = []
for insn in md.disasm(read(EP, 0x100), EP):
    if insn.mnemonic == "call":
        try:
            ops = list(insn.operands)
            if ops and ops[0].type == capstone.x86.X86_OP_IMM:
                stub_targets.append(ops[0].imm & 0xFFFFFFFF)
        except capstone.CsError: pass
print("stub call targets:", [hex(x) for x in stub_targets])

# BFS forward from each stub target; does it reach roots?
reach = set()
q = deque([t for t in stub_targets if t])
ROOTS = set(roots)
reached_roots = False
while q and len(reach) < 20000:
    fn = q.popleft()
    if fn in reach: continue
    reach.add(fn)
    # forward edges: any call site contained in fn? approximate: fstarts between fn and next boundary is expensive;
    # use: all targets t such that some site s in call_sites[t] has containing(s)==fn  -> requires reverse index by container
    # build once below instead
    q_break = True
    break
# better: build container->targets index once
cont_targets = {}
for t, sites in call_sites.items():
    for s in sites:
        c = containing(s)
        if c is not None:
            cont_targets.setdefault(c, set()).add(t)
reach = set(); q = deque([t for t in stub_targets if t]); found = []
while q and len(reach) < 30000:
    fn = q.popleft()
    if fn in reach: continue
    reach.add(fn)
    if fn in ROOTS:
        found.append(fn)
    for t in cont_targets.get(fn, ()):
        if t not in reach:
            q.append(t)
print("forward reach from EP: %d functions; roots reached: %s" % (len(reach), [hex(x) for x in found]))
lines.append("== forward reach from entry stub targets: %d fns; 3 roots reached: %s ==" % (len(reach), [hex(x) for x in found]))
lines.append("")

# ---- 3. ctor/insert probe for sampled vector globals ----
for vec, tag in ((0xA83E30, "block#1"), (0x887388, "block#3"), (0xB04BD0, "block#35")):
    lines.append("== imm refs to vector 0x%08X (%s): %d ==" % (vec, tag, len(imm_refs.get(vec, []))))
    for addr, mn, ops in imm_refs.get(vec, [])[:20]:
        c = containing(addr)
        lines.append("  0x%08X in 0x%08X: %s %s" % (addr, c, mn, ops))
    lines.append("")

with open(os.path.join(OUT, "root.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote root.txt")
