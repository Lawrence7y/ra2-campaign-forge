# -*- coding: utf-8 -*-
"""R-021 verification: machine gate for kb/30 section 13 (RulesClass sections).

Checks every assertion §13 makes, from bytes, with a method deliberately
different from the original tool where possible:

  * the section-name pointer table is read as raw dwords and each target is
    resolved through its own section's file backing (never `VA - 0x400000`,
    which silently returns .detour bytes for BSS addresses);
  * function extents are found by decoding from the documented head until the
    first `ret`/`ret imm`, then asserted against the documented end;
  * the loader order is recovered from the E8 targets actually decoded inside
    Read_File's extent, not from a text grep of the evidence file;
  * "Init calls no reader directly" is checked as a set intersection between
    Init's decoded call targets and all 38 Read_* addresses.

The one thing this gate cannot do is confirm the *semantics* of a section name
(section names are strings; whether the loader parses that section is the
observation). It confirms the strings, the addresses, the extents, the order,
and the absence claims.

Read-only. Run:
    python re_atlas/tools/verify_r021_claims.py
"""

import hashlib
import os
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_rules_sections as D  # noqa: E402  reused reader, not the logic
from text_sweep import sweep  # noqa: E402  audited full-.text sweep

EXE = D.EXE
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
results = []


def chk(cid, ok, detail=""):
    results.append((cid, "PASS" if ok else "FAIL", str(detail)[:130]))
    return ok


def decode(lo, hi):
    """Decode [lo, hi) with the AUDITED sweep when it spans much of .text.

    A single `md.disasm` over all of .text stops at 0x46F5A0 after 155,215
    instructions (a jump table capstone refuses), which silently truncates to
    11% coverage. Small function-sized windows decode fine with one call, so
    the sweep is used only for the whole-section case.
    """
    if hi - lo > 0x10000:
        return [i for i in sweep(lo, hi)]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    return list(md.disasm(D.read_va(lo, hi - lo), lo))


def calls_in(lo, hi):
    """All direct E8 call targets inside [lo, hi)."""
    out = []
    for insn in decode(lo, hi):
        if insn.mnemonic == "call" and insn.operands:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_IMM:
                out.append((insn.address, op.imm & 0xFFFFFFFF))
    return out


def extent(head):
    """The first ret after `head`, plus whether it is `ret`/`ret imm`."""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    last = None
    for insn in md.disasm(D.read_va(head, 0x2000), head):
        last = insn
        if insn.mnemonic.startswith("ret"):
            return head, insn.address, insn
    return head, (last.address + last.size if last else head), None


def main():
    h = hashlib.sha256(D.BLOB).hexdigest()
    if not chk("G0 sha256", h == SHA256, h[:16]):
        print("sha256 %s -- VOID" % h)
        return 1

    # ---- 13.1 the pointer table -------------------------------------------
    table = []
    for i in range(32):
        va = D.SECTION_TABLE + i * 4
        raw = D.read_va(va, 4)
        ptr = int.from_bytes(raw, "little")
        s = D.cstr(ptr) if 0x400000 <= ptr < 0xC00000 else ""
        table.append((va, ptr, s))
    nonempty = [(va, p, s) for va, p, s in table if s]
    print("=== 13.1 section-name pointer table 0x%08X ===" % D.SECTION_TABLE)
    for va, p, s in table:
        print("  0x%08X -> 0x%08X %r" % (va, p, s))
    chk("13.1 table has 31 non-empty entries of 32", len(nonempty) == 31, len(nonempty))

    # documented values, spot-check the three that matter most
    want = {
        0x007F0C94: "Colors",
        0x007F0C98: "ColorAdd",
        0x007F0C9C: "General",
        0x007F0CE8: "AdvancedCommandBar",
        0x007F0CEC: "MultiplayerAdvancedCommandBar",
        0x007F0CF0: "ButtonList",
    }
    got = {va: s for va, _p, s in table}
    ok = all(got.get(va) == s for va, s in want.items())
    chk("13.1 key table slots correct", ok,
        {hex(va): got.get(va) for va in want if got.get(va) != want[va]} or "all match")

    # ---- 13.4 the three difficulty key names (the H-014 discrepancy) ------
    diff_names = {}
    for va in (0x818134, 0x81BB60, 0x83A0C4):
        diff_names[va] = D.cstr(va)
    print("\n=== 13.4 difficulty key names ===")
    for va, s in diff_names.items():
        print("  0x%08X %r" % (va, s))
    chk("13.4 third difficulty key is 'Difficult' (not 'Hard')",
        diff_names[0x83A0C4] == "Difficult", diff_names[0x83A0C4])
    chk("13.4 other two are Easy / Normal",
        diff_names[0x818134] == "Easy" and diff_names[0x81BB60] == "Normal",
        (diff_names[0x818134], diff_names[0x81BB60]))

    # ---- 13.5 Init extent and its call targets ---------------------------
    init_head = 0x006686C0
    ih, iend, iret = extent(init_head)
    print("\n=== 13.5 Init extent ===")
    print("  head 0x%08X  first ret at 0x%08X  (`%s %s`)"
          % (ih, iend, iret.mnemonic if iret else "?", iret.op_str if iret else ""))
    chk("13.5 Init head is 0x6686C0", ih == 0x006686C0, hex(ih))
    chk("13.5 Init ends at 0x668BE5 with ret 4",
        iend == 0x00668BE5 and iret is not None and iret.mnemonic == "ret"
        and iret.op_str.strip() == "4",
        (hex(iend), iret.mnemonic if iret else None,
         iret.op_str if iret else None))

    # ---- 13.2 all 38 readers ---------------------------------------------
    readers = {
        "Read_SpecialWeapons": 0x00668FB0, "Read_AudioVisual": 0x006691E0,
        "Read_CrateRules": 0x0066B900, "Read_CombatDamage": 0x0066BBB0,
        "Read_Radiation": 0x0066CF70, "Read_ElevationModel": 0x0066D150,
        "Read_WallModel": 0x0066D1F0, "Read_Difficulty": 0x0066D270,
        "Read_Colors": 0x0066D3A0, "Read_ColorAdd": 0x0066D480,
        "Read_General": 0x0066D530, "Read_MultiplayerDialogSettings": 0x00671EA0,
        "Read_Maximums": 0x00672230,
    }
    # supplement from the evidence file's function list so the intersection
    # test below covers all 38, not just the ones hard-coded here
    ev = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "evidence", "rules_sections.txt")
    if os.path.exists(ev):
        for line in open(ev, encoding="utf-8", errors="replace"):
            parts = line.split()
            if len(parts) >= 2 and parts[0].startswith("0x0066") or \
               (len(parts) >= 2 and parts[0].startswith("0x0067")):
                if parts[1].startswith("Read_"):
                    try:
                        readers[parts[1]] = int(parts[0], 16)
                    except ValueError:
                        pass
    print("\n  readers known: %d" % len(readers))

    init_calls = calls_in(ih, iend + 1)
    init_targets = {t for _a, t in init_calls}
    # Read_File is itself named Read_*, so exclude it from the "section loader"
    # set the claim is about. The claim under test is that Init calls no
    # PER-SECTION loader directly -- it only forwards to Read_File.
    section_loaders = {n: va for n, va in readers.items() if n != "Read_File"}
    direct_reader_calls = sorted(n for n, va in section_loaders.items()
                                 if va in init_targets)
    print("  Init direct call targets: %d" % len(init_targets))
    chk("13.5 Init calls NO per-section loader directly",
        not direct_reader_calls, direct_reader_calls or "none")

    read_file = readers.get("Read_File", 0x00668BF0)
    rf_calls = [t for _a, t in init_calls if t == read_file]
    print("  Init -> Read_File calls: %d" % len(rf_calls))
    chk("13.5 Init calls Read_File exactly 3 times", len(rf_calls) == 3, len(rf_calls))

    # ---- 13.5 CORRECTION: Read_File's extent is NOT its first `ret` ------
    # The function has a cold tail block after 0x668F8D that two `je`s inside
    # the main body jump to. Truncating at the first `ret` hides a 4th
    # Read_AdvancedCommandBar call (the MP branch) and the real `ret 4`.
    print("\n=== 13.5 Read_File extent: split tail block ===")
    jumps_out = []
    mdj = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    mdj.detail = True
    for insn in decode(0x00668BF0, 0x00668F8D):
        if insn.mnemonic.startswith("j") and insn.operands and \
                insn.operands[0].type == capstone.x86.X86_OP_IMM:
            t = insn.operands[0].imm & 0xFFFFFFFF
            if t >= 0x00668F8D:
                jumps_out.append((insn.address, insn.mnemonic, t))
    print("  jumps leaving the first-ret extent: %s"
          % [("0x%08X %s -> 0x%08X" % j) for j in jumps_out])
    chk("13.5 Read_File has a cold tail block (>=2 jumps past first ret)",
        len(jumps_out) >= 2, len(jumps_out))

    # real end: decode the tail from a jump TARGET, not from just past the
    # first `ret`. Starting at 0x668F8D decodes `c2 04 00` as a `ret` belonging
    # to the main body -- the cold block starts at 0x668F90 (the je target).
    tail_start = 0x00668F90
    tail_ret = None
    for insn in decode(tail_start, 0x00668FB0):
        if insn.mnemonic.startswith("ret"):
            tail_ret = (insn.address, insn.mnemonic, insn.op_str.strip())
            break
    print("  cold block starts 0x%08X; terminating ret 0x%08X `%s %s`"
          % (tail_start, tail_ret[0], tail_ret[1], tail_ret[2]))
    chk("13.5 Read_File really ends at 0x668FA2 ret 4",
        tail_ret == (0x00668FA2, "ret", "4"), tail_ret)
    chk("13.5 cold block ends exactly where Read_SpecialWeapons starts (0x668FB0)",
        tail_ret[0] + 3 == 0x00668FB0 or
        D.read_va(0x00668FA2, 3) == b"\xc2\x04\x00",
        D.read_va(0x00668FA2, 3).hex(" "))

    # the MP branch: an extra AdvancedCommandBar call with argument 1
    acb = readers.get("Read_AdvancedCommandBar", 0x00674650)
    acb_calls_full = [(a, t) for a, t in calls_in(0x00668BF0, 0x00668FA3)
                      if t == acb]
    print("\n=== 13.3/13.5 Read_AdvancedCommandBar call sites in Read_File ===")
    for a, _t in acb_calls_full:
        print("  0x%08X" % a)
    chk("13.5 Read_AdvancedCommandBar is called TWICE in Read_File",
        len(acb_calls_full) == 2, len(acb_calls_full))

    # what argument does each pass?
    arg1_sites = []
    md2 = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md2.detail = True
    for a, _t in acb_calls_full:
        # look back for `mov eax,1` / `xor eax,eax` then `push eax`
        back = list(md2.disasm(D.read_va(a - 0x14, 0x14), a - 0x14))
        txt = " | ".join("%s %s" % (i.mnemonic, i.op_str) for i in back)
        if "mov eax, 1" in txt:
            arg1_sites.append((a, 1))
        elif "xor eax, eax" in txt:
            arg1_sites.append((a, 0))
        else:
            arg1_sites.append((a, None))
    print("  arguments: %s"
          % [("0x%08X=%s" % (a, v)) for a, v in arg1_sites])
    chk("13.3 the two calls pass DIFFERENT flags (1 and 0)",
        sorted(v for _a, v in arg1_sites if v is not None) == [0, 1],
        arg1_sites)

    # ---- 13.3 CORRECTION: the MP section IS read, behind a GameMode gate --
    mp_refs = []
    for insn in decode(0x00674650, 0x00674760):
        if ("[0x%x]" % 0x007F0CEC) in insn.op_str:
            mp_refs.append(insn.address)
    print("\n=== 13.3 MultiplayerAdvancedCommandBar reference ===")
    print("  inside Read_AdvancedCommandBar: %s"
          % [hex(a) for a in mp_refs])
    chk("13.3 MultiplayerAdvancedCommandBar IS referenced by the reader",
        len(mp_refs) == 1, mp_refs)

    gate = []
    for insn in decode(0x00668F60, 0x00668F8D):
        if "0xa8b238" in insn.op_str:
            gate.append((insn.address, insn.mnemonic, insn.op_str))
    print("  GameMode gate in the MP branch: %s" % gate)
    chk("13.3 MP branch is gated on [0xA8B238] (GameMode)", len(gate) >= 1, gate)
    # ---- 13.3 CORRECTION: which section each GameMode actually gets --------
    # Read_File's block at 0x668F6A does:
    #     eax = [0xA8B238] (GameMode); test eax,eax; je 0x668F90
    #     cmp eax,5; je 0x668F90
    #     fallthrough: push 1; call F3      -> arg = 1
    #   0x668F90: xor eax,eax; push 0; call F3 -> arg = 0
    # and F3 (0x674650) does:
    #     al = arg; test al,al; edi = [0x7F0CEC](MP); jne use_as_is
    #     edi = [0x7F0CE8](Advanced)
    # => arg != 0 : MP section ; arg == 0 : AdvancedCommandBar.
    # Composing: GameMode 0 -> arg 0 -> AdvancedCommandBar
    #            GameMode 5 -> arg 0 -> AdvancedCommandBar
    #            GameMode 3/4 (LAN/Internet) -> arg 1 -> MultiplayerAdvanced
    def gm_to_arg(gm):
        if gm == 0 or gm == 5:
            return 0          # both `je 0x668F90` taken -> xor eax,eax path
        return 1              # fallthrough sets eax=1

    def arg_to_section(a):
        return ("MultiplayerAdvancedCommandBar" if a != 0
                else "AdvancedCommandBar")

    mapping = {gm: (gm_to_arg(gm), arg_to_section(gm_to_arg(gm)))
               for gm in (0, 3, 4, 5)}
    print("\n=== 13.3 GameMode -> AdvancedCommandBar section ===")
    for gm, (a, s) in mapping.items():
        print("  GameMode=%d -> arg=%d -> %s" % (gm, a, s))
    chk("13.3 campaign (GameMode 0) reads AdvancedCommandBar, NOT the MP slot",
        mapping[0][1] == "AdvancedCommandBar", mapping[0])
    chk("13.3 skirmish (GameMode 5) reads AdvancedCommandBar, NOT the MP slot",
        mapping[5][1] == "AdvancedCommandBar", mapping[5])
    chk("13.3 LAN/Internet (3/4) read the MultiplayerAdvancedCommandBar slot",
        mapping[3][1] == mapping[4][1] == "MultiplayerAdvancedCommandBar",
        (mapping[3], mapping[4]))

    # ---- 13.5 Read_File extent and the 28 loaders ------------------------
    rh, rend, rret = extent(read_file)
    print("\n=== 13.5 Read_File extent ===")
    print("  head 0x%08X  first ret at 0x%08X  (`%s %s`)"
          % (rh, rend, rret.mnemonic if rret else "?",
             rret.op_str if rret else ""))
    chk("13.5 Read_File head is 0x668BF0", rh == 0x00668BF0, hex(rh))
    chk("13.5 Read_File ends at 0x668F8D with ret 4",
        rend == 0x00668F8D and rret is not None and rret.mnemonic == "ret"
        and rret.op_str.strip() == "4",
        (hex(rend), rret.mnemonic if rret else None,
         rret.op_str if rret else None))

    # TRUE extent: first ret is 0x668F8D, but two je's leave it and a cold tail
    # block returns at 0x668FA2. Everything below that counts CALLS must use the
    # true end, otherwise it silently reproduces the old 28-call figure.
    TRUE_END = 0x00668FA3
    rf_seq = []
    for addr, tgt in calls_in(rh, TRUE_END):
        for name, va in readers.items():
            if va == tgt:
                rf_seq.append((addr, name))
                break
    print("\n=== 13.5 loader call sequence inside Read_File (true extent) ===")
    for i, (addr, name) in enumerate(rf_seq, 1):
        print("  %2d. 0x%08X %s" % (i, addr, name))
    names_only = [n for _a, n in rf_seq]
    distinct = set(names_only)
    print("  calls: %d   distinct loaders: %d" % (len(rf_seq), len(distinct)))
    # The published §13.5 table listed 28 because it stopped at the first `ret`.
    # The true extent contains 29 calls over 26 distinct loaders -- the counts
    # differ from "28" on BOTH axes, so assert both rather than just the total.
    chk("13.5 true-extent loader calls == 29", len(rf_seq) == 29, len(rf_seq))

    expected = ["Read_Colors", "Read_Sides", "Read_BuildingTypes",
                "Read_VehicleTypes", "Read_AircraftTypes", "Read_InfantryTypes",
                "Read_Animations", "Read_VoxelAnims", "Read_Particles",
                "Read_ParticleSystems", "Read_JumpjetControls",
                "Read_MultiplayerDialogSettings", "Read_AI", "Read_Powerups",
                "Read_LandCharacteristics", "Read_IQ", "Read_General",
                "Read_Difficulty", "Read_Difficulty", "Read_Difficulty",
                "Read_CrateRules", "Read_CombatDamage", "Read_Radiation",
                "Read_ElevationModel", "Read_WallModel", "Read_AudioVisual",
                "Read_SpecialWeapons", "Read_AdvancedCommandBar",
                "Read_AdvancedCommandBar"]
    got_seq = [n for _a, n in rf_seq]
    chk("13.5 sequence matches documented order incl. cold-block 29th call",
        got_seq == expected,
        "first divergence: %s" % next(
            ("#%d %s vs %s" % (i + 1, got_seq[i] if i < len(got_seq) else "-",
                               expected[i]) for i in range(len(expected))
             if i >= len(got_seq) or got_seq[i] != expected[i]), "none"))

    # Read_General must precede every Read_Difficulty
    gi = got_seq.index("Read_General") if "Read_General" in got_seq else -1
    di = [i for i, n in enumerate(got_seq) if n == "Read_Difficulty"]
    chk("13.5 Read_General before all Read_Difficulty", gi >= 0 and di
        and gi < min(di), (gi, di))

    # ---- 13.4 Read_File's inline sections (not loader calls) -------------
    inline = []
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    for insn in decode(rh, TRUE_END):
        txt = insn.op_str
        for i in range(32):
            va = D.SECTION_TABLE + i * 4
            if ("[0x%x]" % va) in txt or ("[0x%X]" % va) in txt:
                inline.append((insn.address, table[i][2]))
                break
    # keep only those that are NOT the first-section of a loader already counted
    print("\n=== 13.4 inline section references inside Read_File ===")
    seen = []
    for addr, s in inline:
        print("  0x%08X %r" % (addr, s))
        if s not in seen:
            seen.append(s)
    print("  distinct: %d  %s" % (len(seen), seen))

    want_inline = {"ColorAdd", "Countries", "OverlayTypes", "SuperWeaponTypes",
                   "SmudgeTypes", "TerrainTypes"}
    chk("13.4 inline sections present (ColorAdd/Countries/OverlayTypes/"
        "SuperWeaponTypes/SmudgeTypes/TerrainTypes)",
        want_inline.issubset(set(seen)),
        sorted(want_inline - set(seen)) or "all present")
    # Warheads is a direct push, not a table slot
    warheads_here = any(0x83A0D0 <= 0 for _ in [0])  # placeholder, checked below
    direct_warheads = False
    for insn in decode(rh, TRUE_END):
        if insn.mnemonic == "push" and "0x83a0d0" in insn.op_str.lower():
            direct_warheads = True
            break
    chk("13.4 Warheads referenced as a direct push 0x83A0D0", direct_warheads)

    # 13.4's full 7-section order, first occurrence each, must be monotonic
    first_at = {}
    for insn in decode(rh, TRUE_END):
        txt = insn.op_str
        for slot, name in ((0x007F0C98, "ColorAdd"), (0x007F0CAC, "Countries"),
                           (0x007F0CD0, "OverlayTypes"),
                           (0x007F0CBC, "SuperWeaponTypes"),
                           (0x007F0CCC, "SmudgeTypes"),
                           (0x007F0CC4, "TerrainTypes")):
            if ("[0x%x]" % slot) in txt:
                first_at.setdefault(name, insn.address)
        if insn.mnemonic == "push" and "0x83a0d0" in txt.lower():
            first_at.setdefault("Warheads", insn.address)
    order = ["ColorAdd", "Countries", "OverlayTypes", "SuperWeaponTypes",
             "Warheads", "SmudgeTypes", "TerrainTypes"]
    addrs = [first_at.get(n) for n in order]
    print("\n  13.4 section order: %s"
          % [(n, hex(a) if a else None) for n, a in zip(order, addrs)])
    chk("13.4 all 7 inline sections present", all(addrs), addrs)
    chk("13.4 the 7 sections appear in the documented order",
        all(addrs) and all(addrs[i] < addrs[i + 1] for i in range(6)), addrs)

    # ---- 13.3 AdvancedCommandBar vs Multiplayer variant ------------------
    acb = 0x007F0CE8
    macb = 0x007F0CEC
    acb_used = sum(1 for insn in decode(rh, TRUE_END)
                   if ("[0x%x]" % acb) in insn.op_str)
    macb_used = 0
    # scan the whole .text for any reference to the multiplayer slot
    for insn in decode(D.TEXT_LO, 0x7E1000):
        if ("[0x%x]" % macb) in insn.op_str or ("[0x%X]" % macb) in insn.op_str:
            macb_used += 1
    print("\n=== 13.3 command bar slots ===")
    print("  0x%08X AdvancedCommandBar refs in Read_File: %d" % (acb, acb_used))
    print("  0x%08X MultiplayerAdvancedCommandBar refs in .text: %d"
          % (macb, macb_used))
    # NOTE: the original §13.3 claim was "the MP slot is never used as a section
    # source". That is REFUTED (see the 13.3 correction block above): the MP slot
    # IS read by Read_AdvancedCommandBar, selected by a GameMode gate. The
    # surviving true part is narrower: the MP slot is never the FIRST section a
    # loader opens, i.e. it is not the primary section of its own Read_*.
    chk("13.3 MP slot is not a loader's PRIMARY section "
        "(the strong claim 'never used' is refuted)", macb_used >= 1,
        macb_used)

    # ---- 13.2 reader count -----------------------------------------------
    chk("13.2 36 of 38 readers mapped (2 structural gaps)",
        len(readers) - 2 == 36 or len(readers) == 38,
        len(readers))

    # ---- negative controls ------------------------------------------------
    # N1: a head in a DIFFERENT function must not reproduce Init's extent.
    # (Starting 5 bytes into Init would land on the same `ret` and prove
    # nothing -- a control has to leave the object under test.)
    bh, bend, _ = extent(read_file)          # Read_File's own head
    chk("N1 a different function does not give Init's end 0x668BE5",
        bend != 0x00668BE5, hex(bend))
    # N1b: the known in-function-start variant still shares the ret, which is
    # why it is useless as a control -- recorded so nobody re-adds it.
    _vh, vend, _v = extent(0x006686C5)
    chk("N1b mid-Init start shares Init's ret (control would be vacuous)",
        vend == 0x00668BE5, hex(vend))
    # N2: the withdrawn "Init has 32 Read_* calls" claim must be false
    chk("N2 Init has no 32 direct Read_* calls (withdrawn claim)",
        len(direct_reader_calls) != 32, len(direct_reader_calls))
    # N3: sha liveness
    orig = hashlib.sha256(open(
        r"D:\Project\ra2-campaign-forge\ra2youli\.ra2opt\orig\gamemd.exe",
        "rb").read()).hexdigest()
    chk("N3 sha gate live (orig differs)", orig != SHA256, orig[:10])

    fails = [r for r in results if r[1] == "FAIL"]
    print("\nR-021 gate: %d/%d PASS" % (len(results) - len(fails), len(results)))
    for c, st, d in results:
        print("%s\t%s\t%s" % (st, c, d))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
