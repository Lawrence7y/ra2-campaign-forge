# -*- coding: utf-8 -*-
"""R-058 mutation suite -- exact-set scoring (shape = R-047..R-057).

Every offset carries a pre-run "current byte == expect" assertion (G-67).
Kill sets derive from each assertion's READ FOOTPRINT (G-75), not from
"which assertion seems semantically related".

  M01 COL sig byte                        -> A1            (only A1 reads 0x7FAC88)
  M02 CCINIClass name[0]                  -> A2, A3        (A1 reads ONLY the COL window;
        the name lives at TD+8=0x8174D0, outside it -- expectation fixed after round 1)
  M03 INIClass name[0]                    -> A5            (S1 survives: still non-empty)
  M04 INISection name[0]                  -> A10
  M05 TD CCINIClass vfptr[0]              -> A3, A6        (shared-vfptr claim breaks)
  M06 INISection COL TD low byte          -> A9            (COL's TD LINK is pinned by A9
        alone; A10 reads the TD at its fixed address -- chain = A9 link + A10 content)
  M07 'BATTLEMD*.INI' string[1]           -> B1
  M08 factory call rel32 (new -> new+1)   -> B2, B3
  M10 ctor stampA vptr byte               -> B4
  M11 ctor stampB vptr byte               -> B4
  M12 zero-block +0x29                    -> B5
  M13 List subctor head stamp byte        -> B6
  M14 RULEMD imm byte                     -> C1
  M15 SOUNDMD imm byte                    -> C2
  M16 global-3 stamper target word        -> D2
  M19 global-6 stamper target byte        -> D3
  M20 dtor thunk ecx word                 -> D4
  M28 worker node-stamp opcode bytes      -> D4
  M21 witness1 disp +0x30->+0x31          -> E1
  M22 witness2 rebase disp (kills nearA)  -> E2, F1, F3
  M23 cache-fill modrm byte               -> E3
  M24 witness2 call rel +1 (caller lost)  -> E2, F1, F2, F3 (F2 embeds the 22-control,
        so losing a caller reddens it too -- G-75 footprint, not semantics)
  M29 retarget twinB caller -> 0x52A4D0   -> F1, F2       (F2's zero-set CAN go red)
  M30 CD base-array first byte            -> A4
  M31 List facet name[0]                  -> A7   (S1 survives: '/' still printable)
  M32 GenericList name[0]                 -> A8
  M33 D1 stamper disp byte                -> D1   (target word 0x887058 -> 0x887059)
"""
import contextlib
import io
import os
import runpy
import struct
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r058_container_class_rtti" + chr(46) + "py")

CASES = [
    ("M01 COL sig byte",        {0x7FAC88: 0x01}, {"A1"},                 {0x7FAC88: 0x00}),
    ("M02 CCINIClass name[0]",  {0x8174D0: 0x2F}, {"A2", "A3"},           {0x8174D0: 0x2E}),
    ("M03 INIClass name[0]",    {0x8174B8: 0x2F}, {"A5"},                 {0x8174B8: 0x2E}),
    ("M04 INISection name[0]",  {0x825B4C: 0x4F}, {"A10"},                {0x825B4C: 0x49}),
    ("M05 TD vfptr byte",       {0x8174C8: 0x95}, {"A3", "A6"},           {0x8174C8: 0x94}),
    ("M06 INISeCTD low byte",   {0x803714: 0x41}, {"A9"},                 {0x803714: 0x40}),
    ("M07 BATTLEMD str[1]",     {0x8261A9: 0x42}, {"B1"},                 {0x8261A9: 0x41}),
    ("M08 factory call rel",    {0x52CBFE: 0x16}, {"B2", "B3"},           {0x52CBFE: 0x15}),
    ("M10 stampA byte",         {0x52CC38: 0xF5}, {"B4"},                 {0x52CC38: 0xF4}),
    ("M11 stampB byte",         {0x52CC1D: 0xFD}, {"B4"},                 {0x52CC1D: 0xFC}),
    ("M12 zero-block 29",       {0x52CC23: 0x29}, {"B5"},                 {0x52CC23: 0x28}),
    ("M13 head stamp byte",     {0x52AD08: 0x01}, {"B6"},                 {0x52AD08: 0x00}),
    ("M14 RULEMD imm",          {0x52CD98: 0x6D}, {"C1"},                 {0x52CD98: 0x6C}),
    ("M15 SOUNDMD imm",         {0x52C6E0: 0x51}, {"C2"},                 {0x52C6E0: 0x50}),
    ("M16 g3 target word",      {0x40E034: 0x72}, {"D2"},                 {0x40E034: 0x71}),
    ("M19 g6 target byte",      {0x49B408: 0xF6}, {"D3"},                 {0x49B408: 0xF5}),
    ("M20 thunk ecx",           {0x40E051: 0x81}, {"D4"},                 {0x40E051: 0x80}),
    ("M28 worker stamp op",     {0x40E32A: 0x90, 0x40E32B: 0x90}, {"D4"},
     {0x40E32A: 0xC7, 0x40E32B: 0x00}),
    ("M21 witness1 disp30",     {0x52772E: 0x31}, {"E1"},                 {0x52772E: 0x30}),
    ("M22 witness2 rebase",     {0x52A7BF: 0x2D}, {"E2", "F1", "F3"},     {0x52A7BF: 0x2C}),
    ("M23 cache fill modrm",    {0x526BC0: 0x47}, {"E3"},                 {0x526BC0: 0x46}),
    ("M24 witness2 call rel+1", {0x52A7DF: 0x0E}, {"E2", "F1", "F2", "F3"}, {0x52A7DF: 0x0D}),
    ("M29 retarget twinB->A4D0", {0x5269C5: 0x07, 0x5269C6: 0x3B}, {"F1", "F2"},
     {0x5269C5: 0x57, 0x5269C6: 0x4C}),
    ("M30 CD base array",       {0x7FAC68: 0x51}, {"A4"},                 {0x7FAC68: 0x50}),
    # ---- coverage gaps closed by round-1 inventory: A7/A8/D1 had NO killer.
    #      (S1 survives M31/M32 because '/' is still a printable name char.)
    ("M31 List name[0]",        {0x817488: 0x2F}, {"A7"},                 {0x817488: 0x2E}),
    ("M32 GenericList name[0]", {0x817510: 0x2F}, {"A8"},                 {0x817510: 0x2E}),
    ("M33 D1 stamper disp",     {0x40E243: 0x59}, {"D1"},                 {0x40E243: 0x58}),
]

BLOB = open(os.path.join(ROOT, "ra2youli", "gamemd.exe"), "rb").read()
e = struct.unpack_from("<I", BLOB, 0x3C)[0]
nsec = struct.unpack_from("<H", BLOB, e + 6)[0]
optsz = struct.unpack_from("<H", BLOB, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", BLOB, opt + 28)[0]
tab = opt + optsz
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
    raise SystemExit("VERIFY-FAIL: 0x%08X unmapped" % va)


vbad = []
for name, mut, exp, cur_exp in CASES:
    for va, want in cur_exp.items():
        got = cur(va)
        if got != want:
            vbad.append("%s: VA 0x%08X cur=%02X want=%02X" % (name, va, got, want))
if vbad:
    print("PRE-RUN BYTE VERIFY FAILED (G-67 gate):")
    for x in vbad:
        print("  " + x)
    sys.exit(2)
print("pre-run byte verify: all offsets' current bytes match expectations\n")

LABELS = ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10",
          "B1", "B2", "B3", "B4", "B5", "B6",
          "C1", "C2",
          "D1", "D2", "D3", "D4",
          "E1", "E2", "E3",
          "F1", "F2", "F3",
          "S1", "S2", "G0")


def run(mut):
    os.environ["R058_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
    buf = io.StringIO()
    rc = None
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            runpy.run_path(GATE, run_name="__main__")
        rc = 0
    except SystemExit as ex:
        rc = ex.code
    killed = set()
    for line in buf.getvalue().splitlines():
        parts = line.split()
        if parts and parts[0] in LABELS and len(parts) > 1 and parts[1] == "FAIL:":
            killed.add(parts[0])
    return rc, killed


rc0, base = run({})
print("baseline rc=%s failed=%s" % (rc0, sorted(base)))
if rc0 != 0 or base:
    print("BASELINE NOT GREEN -- abort")
    sys.exit(2)

ok_all = True
n_ok = 0
killed_union = set()
for name, mut, expect, _ in CASES:
    rc, killed = run(mut)
    killed_union |= killed
    score_ok = (killed == expect) and (rc != 0)
    n_ok += 1 if score_ok else 0
    print("%-26s expect=%-20s killed=%-20s rc=%s %s" % (
        name, sorted(expect), sorted(killed), rc, "OK" if score_ok else "MISMATCH"))
    if not score_ok:
        ok_all = False

# G-79: suite green is NOT per-assertion killability.  Diff the union of kill sets
# against the gate's COUNTED assertion labels; any member with no killer exits red
# unless it is a deliberately registered structural check (S*/G0), which by
# convention lives outside the mutation denominator.
COUNTED = ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10",
           "B1", "B2", "B3", "B4", "B5", "B6",
           "C1", "C2",
           "D1", "D2", "D3", "D4",
           "E1", "E2", "E3",
           "F1", "F2", "F3")
uncovered = [x for x in COUNTED if x not in killed_union]
if uncovered:
    print("\nG-79 COVERAGE RED: counted assertions with ZERO killer: %s" % uncovered)
    ok_all = False
else:
    print("\nG-79 coverage: all %d counted assertions have >=1 killer" % len(COUNTED))

print("\n== R-058 mutation %d/%d 精确集合击杀 ==" % (n_ok, len(CASES)))
sys.exit(0 if ok_all and n_ok == len(CASES) else 1)
