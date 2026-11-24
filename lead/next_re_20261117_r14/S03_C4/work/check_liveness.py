#!/usr/bin/env python3
"""Liveness robustness check (discipline #10 / 错源 ㉓).
NOTE: our ④ witness is direct call, so vtable liveness is NOT required for the four-ring.
This check is only to confirm the vt cited in ② is ctor-installed (live), not atexit-dead.
Method: (1) collect all atexit-registered dtors: pattern `push <fn>; call 0x7C978A`.
(2) for each primary vt, find C7-family `mov [..], imm32=vt` write sites in .text;
    report containing function (atlas interval) and whether it is an atexit dtor."""
import json, struct
from common import DATA, IB, TEXT_VA, TEXT_END, va2off, _pe, disasm_n, _MD

# atlas intervals (entry,size) for containment
atlas = {}
apath = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
with open(apath, encoding='utf-8', errors='replace') as f:
    f.readline()
    for line in f:
        p = line.rstrip('\n').split('\t')
        if len(p) < 2: continue
        try: atlas[int(p[0],16)] = int(p[1])
        except Exception: pass
entries_sorted = sorted(atlas)
import bisect
def containing_fn(va):
    i = bisect.bisect_right(entries_sorted, va) - 1
    if i >= 0:
        e = entries_sorted[i]
        if e <= va < e + atlas[e]: return e
    return None

# (1) atexit dtors: push imm32 <fn>; call 0x7C978A (within 6 bytes)
atexit_fns = set()
n = TEXT_END - TEXT_VA
off = va2off(TEXT_VA)
buf = DATA[off:off+n]
for i in range(len(buf)-10):
    if buf[i] == 0x68 and buf[i+5:i+9] == struct.pack('<I', 0x7C978A):
        fn = struct.unpack_from('<I', buf, i+1)[0]
        atexit_fns.add(fn)
print(f"atexit-registered functions found: {len(atexit_fns)}")
print("  sample:", [hex(x) for x in sorted(atexit_fns)[:8]])

# primary vt per entry (from rtti_chains.json first chain)
rtti = json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C4\EVIDENCE\rtti_chains.json"))
primary_vt = {}
for e, d in rtti.items():
    if d['chains']:
        primary_vt[e] = d['chains'][0]['vt']

def find_vt_writes(vt):
    """Find C7-family mov [..], imm32 where imm32==vt. Scan at instruction boundaries."""
    imm = struct.pack('<I', vt)
    res = []
    for ins in _MD.disasm(buf, TEXT_VA):
        if ins.mnemonic == 'mov' and len(ins.bytes) >= 6:
            # last 4 bytes == imm and operand is memory destination
            if ins.bytes[-4:] == imm and ins.operands and ins.operands[0].type == capstone.x86.X86_OP_MEM:
                res.append((ins.address, ins.bytes.hex(), ins.op_str))
    return res
import capstone

out = {}
for e, vt in primary_vt.items():
    writes = find_vt_writes(vt)
    detail = []
    for addr, raw, ops in writes:
        fn = containing_fn(addr)
        dead = fn in atexit_fns if fn else False
        detail.append({'write_site': hex(addr), 'bytes': raw, 'op': ops,
                       'fn': hex(fn) if fn else None, 'atexit_dtor': dead})
    # live if at least one write not in an atexit dtor
    any_live = any(not d['atexit_dtor'] for d in detail)
    out[e] = {'primary_vt': hex(vt), 'writes': detail, 'any_non_atexit_write': any_live}
    print(f"\n{e}: vt={vt:#x} writes={len(detail)} any_non_atexit={any_live}")
    for d in detail[:6]:
        print(f"    {d['write_site']} fn={d['fn']} atexit={d['atexit_dtor']} {d['op']}")

base = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C4"
json.dump(out, open(base + r"\EVIDENCE\liveness.json",'w',encoding='utf-8'), indent=2)
print("\nwrote liveness.json")
