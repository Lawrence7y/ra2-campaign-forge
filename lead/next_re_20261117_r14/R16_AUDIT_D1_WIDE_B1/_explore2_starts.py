# -*- coding: utf-8 -*-
"""Independent function-boundary analysis: full linear sweep of .text,
collect direct call/jmp targets => candidate function starts.
Then for each install site, derive the enclosing function by:
  candidate = max(start <= site), start in (atlas starts | direct-call targets)
  validate: linear disasm from candidate reaches site exactly on an
  instruction boundary with no ret/jmp-terminating instruction in between.
Cache result to starts.json.
"""
import io, os, sys, json, bisect, time
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
IB = 0x400000
import pefile, capstone

pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    secs.append((s.Name.rstrip(b"\x00").decode("latin-1"), IB + s.VirtualAddress,
                 s.Misc_VirtualSize, s.SizeOfRawData, s.get_data()))
end = max(va + max(vs, rs) for _nm, va, vs, rs, _d in secs)
buf = bytearray(end - IB + 16)
for nm, va, vs, rs, d in secs:
    buf[va - IB:va - IB + len(d)] = d
text_va = IB + pe.sections[0].VirtualAddress
text_sz = pe.sections[0].Misc_VirtualSize

md_fast = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md_fast.skipdata = True
md_fast.detail = False

t0 = time.time()
call_targets = set()
n = 0
code = bytes(buf[text_va - IB: text_va - IB + text_sz])
for ins in md_fast.disasm(code, text_va):
    n += 1
    b = ins.bytes
    if len(b) >= 5 and b[0] in (0xE8, 0xE9):
        rel = int.from_bytes(b[1:5], "little", signed=True)
        tgt = ins.address + 5 + rel
        if text_va <= tgt < text_va + text_sz:
            call_targets.add(tgt)
    elif b and b[0] == 0x0F and len(b) >= 6 and b[1] in (0x84, 0x85):  # jz/jnz rel32 -> not a start
        pass
print("swept insns=%d  targets=%d  elapsed=%.1fs" % (n, len(call_targets), time.time() - t0), file=sys.stderr)

atlas = {}
for i, ln in enumerate(io.open(ATLAS, encoding="utf-8-sig")):
    if i == 0:
        continue
    c = ln.rstrip("\r\n").split("\t")
    if len(c) < 2:
        continue
    try:
        atlas[int(c[0].strip(), 16)] = int(c[1])
    except ValueError:
        pass

all_starts = sorted(set(atlas) | call_targets)
json.dump({"n": n, "targets": sorted(call_targets), "atlas": {("%08X" % k): v for k, v in atlas.items()}},
          io.open(os.path.join(HERE, "starts.json"), "w", encoding="utf-8"))
print("all_starts=%d atlas=%d targets_only=%d" % (len(all_starts), len(atlas), len(set(call_targets) - set(atlas))))
