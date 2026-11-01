# -*- coding: utf-8 -*-
"""R-050 mutation suite -- exact-set scoring (shape = R-047/R-048).

Offsets derived from the authoritative window dump with explicit byte arithmetic
(TD name byte = TD+8 per probe's tdname()). The PRE-RUN mechanical gate below
asserts every target's current byte before any mutation runs (G-67: 偏移禁心算，
现值断言先行)——first draft had M4/M6 landing on the TD's spacer dword and M3 on
the wrong imm byte; the pre-run is exactly what forces the re-derivation into
the code.

Shared-byte kill lists (enumerated exhaustively):
  M1: install-pattern bytes live inside the W1 window AND form the W2 raw-find
      pattern => {W1, W2}.
  M7: demote-pattern bytes inside W4 window AND the W2 second pattern => {W2, W4}.
  M9: b9 opcode is a W5 window byte AND the W7 census entry => {W5, W7}.
"""
import io, os, runpy, contextlib, sys, struct

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r050_trigger_registry" + chr(46) + "py")

CASES = [
    # install pattern 0x72536D: c7 05 70f6b000 EC 917e00 -> imm low byte @0x725373
    ("M1 W1/W2 vptr imm EC->ED",   {0x725373: 0xED}, {"W1", "W2"}, {0x725373: 0xEC}),
    # atexit call 0x725386: e8 [FF430A00] -> rel b0 @0x725387
    ("M2 atexit rel b0 FF->FE",    {0x725387: 0xFE}, {"W1"},       {0x725387: 0xFF}),
    # cap store idx 0x2D in W1 window (c7 05 84f6b000 [0A]000000) -> 0x725350+0x2D
    ("M3 cap imm 0A->0B",          {0x72537D: 0x0B}, {"W1"},       {0x72537D: 0x0A}),
    # AbstractClass-dyn TD = 0x8225E8, name string at TD+8 = 0x8225F0 (leading '.')
    ("M4 dyn-name .->X",           {0x8225F0: 0x58}, {"W3"},       {0x8225F0: 0x2E}),
    # dyn COL@0x8009B0, TD-ptr field @COL+12 = 0x8009BC holds E8 25 82 00
    ("M5 COL TD-ptr b0 E8->00",    {0x8009BC: 0x00}, {"W3"},       {0x8009BC: 0xE8}),
    # House dyn name string @0x8233b0 (fileoff 0x4233b0): control for the method
    ("M6 house name .->X (CTRL)",  {0x8233B0: 0x58}, {"W3"},       {0x8233B0: 0x2E}),
    # demote pattern 0x725398: c70570f6b000 [0C]927e00
    ("M7 demote imm 0C->0D",       {0x72539E: 0x0D}, {"W2", "W4"}, {0x72539E: 0x0C}),
    # W5 virtual-add call ff 52 08 at 0x72601B..1D -> slot byte @0x72601D
    ("M8 add-slot 08->09",         {0x72601D: 0x09}, {"W5"},       {0x72601D: 0x08}),
    # b9 70f6b000 at 0x726016: W5 window byte + W7 census entry (shared)
    ("M9 b9 opcode B9->B8",        {0x726016: 0xB8}, {"W5", "W7"}, {0x726016: 0xB9}),
    # tail store 89 34 81 at 0x726037/38/39 (W5 window idx 0x4E/4F/50, ends at 0x726039)
    #   flip SIB base byte 81->80 at 0x726039
    ("M10 tail SIB 81->80",        {0x726039: 0x80}, {"W5"},       {0x726039: 0x81}),
    # ctor head 8B F1 (mov esi,ecx) modrm @0x725FA3 (F1->F0 src=eax): head_ok byte only
    ("M11 head src ecx->eax",      {0x725FA3: 0xF0}, {"W6"},       {0x725FA3: 0xF1}),
    # WhatAmI imm 26->27 (structural S1)
    ("M12 WhatAmI 26->27",         {0x726941: 0x27}, {"S1"},       {0x726941: 0x26}),
]

# ---- pre-run mechanical byte verify (G-67) ----
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
    os.environ["R050_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
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
        if parts and parts[0].startswith(("W", "S")) and len(parts) > 1 and parts[1] == "FAIL:":
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

print(f"\n== R-050 mutation {n_ok}/{len(CASES)} 精确集合击杀 ==")
# G-79 machine reconciliation (R-059 pattern; R-061 aux batch 2): counted
# assertions W1..W7 must each have >=1 killer in the measured union. S1 is
# structural (RTTI JSON; still gated on red, M12 kills it) -> excluded from
# denominator, same discipline as R-053/054/055 suites.
COUNTED = tuple("W%d" % i for i in range(1, 8))
uncovered = [x for x in COUNTED if x not in killed_union]
if uncovered:
    print("\nG-79 COVERAGE RED: counted assertions with ZERO killer: %s" % uncovered)
    sys.exit(1)
print("\nG-79 coverage: all %d counted assertions have >=1 killer" % len(COUNTED))
sys.exit(0 if ok_all and n_ok == len(CASES) else 1)
