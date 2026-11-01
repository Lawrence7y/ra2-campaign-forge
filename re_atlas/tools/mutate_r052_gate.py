# -*- coding: utf-8 -*-
"""R-052 mutation suite -- exact-set scoring (shape = R-047/048/050/051).

Every offset carries a pre-run "current byte == expect" mechanical assertion
(G-67). Kill lists enumerated exhaustively from the window membership:

  M1 flips the Y1 c6453501 write-site opcode -> Y1 only (window bytes elsewhere intact).
  M2 flips +0x34 byte-write at 0x6E4E01 -> Y3 only (it's inside the Y3 0x42 window).
  M3 flips Y5 link-head 8b5628 opcode -> Y5 only (not in Y3; window is +0x17 tail).
  M4 flips Y5 rel32 low byte (0x725FA0->0x725F9F) -> Y5 only.
  M5 flips Y6 rel32 low byte (0x7264C0->0x7264BF) -> Y6 only.
  M6 flips Y1 byte-read 8a4534 -> Y1 only.
  M7 flips Y7 positive-control slot (TagClass slot10 fn ptr) -> Y7 only.
  M8 flips ctor tail-SIB base (0x6E4F18) -> Y8 only (pattern 893481 census, list membership).
  M9 flips 0xB0E720 install imm low byte -> Y8 only (install uniqueness).
  M10 flips 0x8B40C8 install imm low byte -> Y9 only.
  M11 flips TagClass WhatAmI imm 2C->2D -> Y10 only (read window) — S1 unaffected.
  M12 flips TagClass TD name leading '.' -> Y10 only (rtti chain decode).
  M13 flips 0xB0F698 install imm low byte -> S1 only (structural, uncounted).
"""
import io, os, runpy, contextlib, sys, struct

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r052_tagclass_host" + chr(46) + "py")

CASES = [
    ("M1 byte-flag-set op",      {0x6E53E8: 0x89}, {"Y1"},       {0x6E53E8: 0xC6}),
    ("M2 ctor +0x34 byte-write", {0x6E4E01: 0x89}, {"Y3"},       {0x6E4E01: 0x88}),
    ("M3 link-head 8b5628->38",  {0x6E4F41: 0x38}, {"Y5"},       {0x6E4F41: 0x8B}),
    ("M4 rel32 low 63->62",      {0x6E4F39: 0x62}, {"Y5"},       {0x6E4F39: 0x63}),
    ("M5 harvest rel32 a7->a6",  {0x6E5415: 0xA6}, {"Y6"},       {0x6E5415: 0xA7}),
    ("M6 8a4534->8a4544",        {0x6E53C9: 0x44}, {"Y1"},       {0x6E53C9: 0x34}),
    ("M7 slot10 fnptr lo 10->11",{0x7F4508: 0x11}, {"Y7"},       {0x7F4508: 0x10}),
    ("M8 tail SIB 81->80",       {0x6E4F18: 0x80}, {"Y8"},       {0x6E4F18: 0x81}),
    ("M9 B0E720 install imm",    {0x6E4D83: 0xA5}, {"Y8"},       {0x6E4D83: 0xA4}),
    ("M10 8B40C8 install imm",   {0x4E7FD3: 0xA5}, {"Y9"},       {0x4E7FD3: 0xA4}),
    ("M11 WhatAmI 2C->2D",       {0x6E58A1: 0x2D}, {"Y10"},      {0x6E58A1: 0x2C}),
    ("M12 TD name .->X",         {0x8249F0: 0x58}, {"Y10"},      {0x8249F0: 0x2E}),
    ("M13 B0F698 install imm",   {0x725873: 0xED}, {"S1"},       {0x725873: 0xEC}),
    # ---- R-061 aux batch 2: Y2/Y4 had ZERO killers under M1..M13 ----
    # Y2 pins head 22 bytes incl. `a0 6beda800` mov al,[0xA8ED6B]; flip disp
    # low byte idx2 6B->6C at 0x6E53A2. Y1's [ebp+disp] census is unchanged
    # (same insn boundaries, absolute disp) => expected {Y2}; G-82 decides.
    ("M14 head idx2 6B->6C",     {0x6E53A2: 0x6C}, {"Y2"},       {0x6E53A2: 0x6B}),
    # Y4 pins TriggerClass ctor +0x34 store as DWORD 894e34 @0x725FC4. Flip
    # opcode 89->C6: pinned 3-byte read breaks; census patterns c6463400/
    # c6463500 (modrm 46/47 vs produced 4e) stay [] => expected {Y4}.
    ("M15 +0x34 89->c6",         {0x725FC4: 0xC6}, {"Y4"},       {0x725FC4: 0x89}),
]

BLOB = open(os.path.join(ROOT, "ra2youli", "gamemd.exe"), "rb").read()
e = struct.unpack_from("<I", BLOB, 0x3C)[0]; nsec = struct.unpack_from("<H", BLOB, e + 6)[0]
optsz = struct.unpack_from("<H", BLOB, e + 20)[0]; opt = e + 24
IB = struct.unpack_from("<I", BLOB, opt + 28)[0]; tab = opt + optsz
SEC = []
for i in range(nsec):
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", BLOB, tab + i * 40 + 8)
    SEC.append((vaddr, vsize, rawptr, rawsize))
def cur(va):
    rva = va - IB
    for s, vs, rp, rs in SEC:
        if s <= rva < s + vs:
            fo = rp + (rva - s)
            if fo < rp + rs:
                return BLOB[fo]
    raise SystemExit(f"VERIFY-FAIL: 0x{va:08X} unmapped")
vbad = []
for name, mut, exp, cur_exp in CASES:
    for va, want in cur_exp.items():
        got = cur(va)
        if got != want:
            vbad.append(f"{name}: VA 0x{va:08X} cur={got:02X} want={want:02X}")
if vbad:
    print("PRE-RUN BYTE VERIFY FAILED (G-67 gate):")
    for x in vbad:
        print("  " + x)
    sys.exit(2)
print("pre-run byte verify: all offsets' current bytes match expectations\n")

def run(mut):
    os.environ["R052_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
    buf = io.StringIO()
    rc = None
    try:
        with contextlib.redirect_stderr(buf):
            runpy.run_path(GATE, run_name="__main__")
        rc = 0
    except SystemExit as ex:
        rc = ex.code
    killed = set()
    for line in buf.getvalue().splitlines():
        parts = line.split()
        if parts and parts[0].startswith(("Y", "S")) and len(parts) > 1 and parts[1] == "FAIL:":
            killed.add(parts[0])
    return rc, killed

ok_all = True
n_ok = 0
killed_union = set()
for name, mut, expect, _ in CASES:
    rc, killed = run(mut)
    killed_union |= killed
    score_ok = (killed == expect) and (rc != 0)
    n_ok += 1 if score_ok else 0
    print("%-30s expect=%s killed=%s rc=%s %s" % (
        name, sorted(expect), sorted(killed), rc, "OK" if score_ok else "MISMATCH"))
    if not score_ok:
        ok_all = False

print(f"\n== R-052 mutation {n_ok}/{len(CASES)} 精确集合击杀 ==")
# G-79 machine reconciliation (R-059 pattern; R-061 aux batch 2): counted
# assertions Y1..Y10 must each have >=1 killer in the measured union. Y2/Y4
# were ZERO-killer under M1..M13 (M1/M6 land inside Y1's read set, Y2's
# byte-exact head window was never touched; nothing flipped Y4's 894e34)
# -- closed by M14/M15. S1 structural (RTTI JSON) excluded; M13 kills it.
# NOTE (honest register): the gate's fingerprint used to hash the POST-injection
# buffer, so every mutation run self-exited 2 (rc carried no assertion meaning;
# exact-set scoring still judged). Fixed in R-061 aux batch 2: gate now attests
# PRISTINE (file bytes at load) -- mutation runs exit 1 exactly when assertions
# go red, like the r047-r051 siblings. Same G-84-family ordering root cause.
COUNTED = tuple("Y%d" % i for i in range(1, 11))
uncovered = [x for x in COUNTED if x not in killed_union]
if uncovered:
    print("\nG-79 COVERAGE RED: counted assertions with ZERO killer: %s" % uncovered)
    sys.exit(1)
print("\nG-79 coverage: all %d counted assertions have >=1 killer" % len(COUNTED))
sys.exit(0 if ok_all and n_ok == len(CASES) else 1)
