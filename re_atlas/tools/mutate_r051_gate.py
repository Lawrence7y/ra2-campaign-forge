# -*- coding: utf-8 -*-
"""R-051 mutation suite -- exact-set scoring (shape = R-047/R-048/R-050).

Offsets derived from the authoritative window dumps (probe run this round);
every case carries a pre-run "current byte == expect" mechanical assertion
(G-67). Shared-byte kill lists enumerated exhaustively:

  M1: block1's `b9 70f6b000` is a X2 window byte AND the only X8 census entry
      for 0xB0F670's b9 form => no; X8 counts imm32 dwords, so flipping the b9
      opcode at 0x726016 kills X2 (window) and X3? No (893481 untouched).
      X8 counts the imm32 (70f6b000) not the opcode => {X2} only.
  M3: block3's global imm low byte (A8EAE8 -> A8EAE9) kills X2 window AND X4?
      X4 reads RTTI of the *literal* vt addresses, not the ctor immediate =>
      {X2} plus nothing; but X8's census uses the literal global too => {X2}.
      => keep expectation {X2}.
  M4: A8EAE8's vptr install imm byte kills X5 (install pattern) => {X5}.
  M5: A8EAE8 RTTI TD pointer kills X4 => {X4}.
  M6: dtor's first Find call slot byte (ff 52 10) kills X6 => {X6}.
  M7: tail SIB in block3 kills X2 and X3 (pattern count) => {X2, X3}.
"""
import io, os, runpy, contextlib, sys, struct

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r051_trigger_three_registries" + chr(46) + "py")

CASES = [
    # block1 (0x725FE9..0x72603A): b9 opcode at idx 0x2D -> VA 0x726016
    ("M1 block1 b9->b8",            {0x726016: 0xB8}, {"X2"},       {0x726016: 0xB9}),
    # block1 add-slot byte ff 52 08 at 0x72601B..1D -> slot 0x72601D
    ("M2 block1 addslot 08->09",    {0x72601D: 0x09}, {"X2"},       {0x72601D: 0x08}),
    # block2 (0x72603A..0x72608D): `b9 08f7b000` = bytes ...ff 52 08 84 c0 74 18 | b9 08 f7 b0 00
    #   tail of window: b9 at idx 0x2F (0x72603A+0x2F = 0x726069)
    ("M3 block2 b9->b8",            {0x726069: 0xB8}, {"X2"},       {0x726069: 0xB9}),
    # block3 (0x72608D..0x7260E0): b9 at idx 0x2F -> 0x7260BC
    ("M4 block3 b9->b8",            {0x7260BC: 0xB8}, {"X2"},       {0x7260BC: 0xB9}),
    # A8EAE8 install vptr imm low byte at 0x4E65FD+6 = 0x4E6603 (E4->E5)
    ("M5 A8EAE8 vptr install imm",  {0x4E6603: 0xE5}, {"X5"},       {0x4E6603: 0xE4}),
    # A8EAE8 dyn TD name leading '.' at TD+8 = 0x822EA8+8 = 0x822EB0
    ("M6 A8EAE8 TD name .->X",      {0x822EB0: 0x58}, {"X4"},       {0x822EB0: 0x2E}),
    # dtor first unregister: ff 52 10 at 0x72698A..8C -> slot byte 0x72698C
    ("M7 dtor slot 10->11",         {0x72698C: 0x11}, {"X6"},       {0x72698C: 0x10}),
    # block3 tail store 89 34 81 ends 0x7260DD/DE/DF -> SIB base byte at 0x7260DF
    ("M8 block3 tail SIB 81->80",   {0x7260DF: 0x80}, {"X2", "X3"}, {0x7260DF: 0x81}),
    # ctor head call e8 at 0x725FA4 -> nop: breaks X1 (head byte window) only.
    #   X7 asserts the SET of addresses writing esi == [0x725FA2]; killing the
    #   following call does not move or remove that mov => X7 must stay green.
    #   (Expected set measured, not guessed: first draft wrote {X1,X7} and the
    #   suite reported the mismatch -- expectation corrected, assertion kept.)
    ("M9 ctor head e8->nop",        {0x725FA4: 0x90}, {"X1"},       {0x725FA4: 0xE8}),
    # ctor epilogue ret imm (c2 04 00) low byte at 0x726131
    ("M10 ctor ret imm 04->05",     {0x726131: 0x05}, {"X1"},       {0x726131: 0x04}),
    # B0F670 demote pattern imm low (0x725398+6=0x72539E: 0C->0D)
    ("M11 B0F670 demote imm",       {0x72539E: 0x0D}, {"X5"},       {0x72539E: 0x0C}),
    # WhatAmI imm 26->27 (structural S1)
    ("M12 WhatAmI 26->27",          {0x726941: 0x27}, {"S1"},       {0x726941: 0x26}),
    # ---- R-061 aux batch 2: X7/X8 had ZERO killers under M1..M12 ----
    # X7 = esi-writer address set in ctor body == {0x725FA2}. The head modrm
    # F1 at 0x725FA3 selects reg=esi; flip reg field to edi (F9) => the mov is
    # no longer an esi writer. Byte sits inside X1's 5-byte head window => dies
    # too. (First-draft expectation {X1,X7} per byte-reading algebra; measured
    # below, G-82.)
    ("M13 head modrm esi->edi",     {0x725FA3: 0xF9}, {"X1", "X7"}, {0x725FA3: 0xF1}),
    # X8 = census len(raw_hits(e8eaa800))==8. Block3's b9 imm low byte at
    # 0x7260BD is one of the 8; flipping it also breaks X2's byte-exact window.
    # (M3/M4 flip the b9 OPCODE which the imm32 census does not read -- that's
    # why X8 stayed alive until now.)
    ("M14 block3 b9-imm e8->e0",    {0x7260BD: 0xE0}, {"X2", "X8"}, {0x7260BD: 0xE8}),
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
    os.environ["R051_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
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
        if parts and parts[0].startswith(("X", "S")) and len(parts) > 1 and parts[1] == "FAIL:":
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

print(f"\n== R-051 mutation {n_ok}/{len(CASES)} 精确集合击杀 ==")
# G-79 machine reconciliation (R-059 pattern; R-061 aux batch 2): counted
# assertions X1..X8 must each have >=1 killer in the measured union. X7/X8 were
# ZERO-killer under M1..M12 (M3/M4 flipped the b9 OPCODE, which the imm32 census
# X8 does not read; nothing touched the esi-writer set X7) -- closed by M13/M14.
# S1 structural (RTTI JSON) excluded from denominator; M12 still kills it.
COUNTED = tuple("X%d" % i for i in range(1, 9))
uncovered = [x for x in COUNTED if x not in killed_union]
if uncovered:
    print("\nG-79 COVERAGE RED: counted assertions with ZERO killer: %s" % uncovered)
    sys.exit(1)
print("\nG-79 coverage: all %d counted assertions have >=1 killer" % len(COUNTED))
sys.exit(0 if ok_all and n_ok == len(CASES) else 1)
