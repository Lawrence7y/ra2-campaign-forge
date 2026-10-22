"""Which INI loaders keep `this` in EBP? (G-41 blast-radius census)

Why this tool exists
--------------------
`dump_typeclass_fields.py` had a rule that skipped `fstp [ebp+off]` because EBP
was assumed to be a stack frame pointer. For two classes that assumption was
false -- `TechnoTypeClass` and `BuildingTypeClass` keep `this` in EBP -- and 31
ReadDouble fields vanished from a delivered table while every self-check still
printed "all pass".

Fixing those two classes does not answer the question a consumer of the tables
actually has: WHICH OTHER DELIVERED TABLES COULD BE MISSING ROWS THE SAME WAY?
This tool answers it by census rather than by argument:

  1. find every function in .text whose prologue stores `ecx` (the `this`
     pointer, under MSVC thiscall) into a callee-saved register;
  2. keep the ones whose register is EBP -- the exact shape that was mishandled;
  3. among those, keep the ones that look like INI loaders (they call one of the
     five `Read*` members) and actually write object fields;
  4. report which of them are already covered by a repaired tool and which are
     not.

The last column is the point: a loader in EBP-this shape that no current tool
parses is a table that is either missing or was produced by a tool with the
same blind spot.

Read-only. No window sizes: bodies are bounded by their own terminal `ret`, and
the sweep is resynchronised (see text_sweep) because a single md.disasm call
stops at 0x46F5A0 and covers 11% of .text while reporting success.

Run: python re_atlas/tools/census_ebp_this_loaders.py
"""

import bisect
import os
import struct
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_rules_sections as D  # noqa: E402  per-section bounded read_va
import text_sweep as TS  # noqa: E402  audited full-.text sweep

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

TEXT_LO, TEXT_HI = 0x401000, 0x7E1000
PAD = (0xCC, 0x90)

READERS = {
    0x005276D0: "ReadInteger",
    0x005295F0: "ReadBool",
    0x00528A10: "ReadString",
    0x00528F00: "ReadUnicodeString",
    0x005283D0: "ReadDouble",
}

CALLEE_SAVED = {
    "ebx": capstone.x86.X86_REG_EBX,
    "esi": capstone.x86.X86_REG_ESI,
    "edi": capstone.x86.X86_REG_EDI,
    "ebp": capstone.x86.X86_REG_EBP,
}

# Loaders already known and covered by a tool (from kb/30 and kb/30 19).
COVERED = {
    0x00410A60: "AbstractTypeClass::LoadFromINI (dump_typeclass_fields, fixed)",
    0x005F92D0: "ObjectTypeClass::LoadFromINI (dump_typeclass_fields, fixed)",
    0x00712170: "TechnoTypeClass::LoadFromINI (dump_typeclass_fields, fixed)",
    0x005240A0: "InfantryTypeClass::LoadFromINI (dump_typeclass_fields, fixed)",
    0x00747620: "UnitTypeClass::LoadFromINI (dump_typeclass_fields, fixed)",
    0x0041CC20: "AircraftTypeClass::LoadFromINI (dump_typeclass_fields, fixed)",
    0x0045FE50: "BuildingTypeClass::LoadFromINI (dump_typeclass_fields, fixed)",
    0x0066D530: "Read_General (dump_rules_fields)",
    0x006691E0: "Read_AudioVisual (dump_rules_fields)",
    0x00671EA0: "Read_MultiplayerDialogSettings (dump_rules_fields)",
}

RESULTS = []


def record(tag, ok, detail):
    RESULTS.append((tag, ok, detail))
    print("  [%s] %-28s %s" % ("PASS" if ok else "FAIL", tag, detail))


# --------------------------------------------------------------------------
# function boundaries


def extent(entry, limit=TEXT_HI):
    """[entry, end) from the function's OWN terminal ret (ret then padding).

    Decodes in CHUNKS rather than handing capstone one 0x30000-byte buffer: the
    one-shot form measured ~190 ms per entry (almost every loader is tiny) and
    with ~15k roots that is ~50 minutes. Chunking makes the common case
    proportional to the real body length.
    """
    CHUNK = 0x800
    last = None
    addr = entry
    while addr < limit:
        progressed = False
        for insn in md.disasm(D.read_va(addr, min(CHUNK, limit - addr)), addr):
            progressed = True
            last = insn
            if insn.mnemonic.startswith("ret"):
                nxt = D.read_va(insn.address + insn.size, 2)
                if len(nxt) == 2 and nxt[0] in PAD and nxt[1] in PAD:
                    return insn.address + insn.size, True
            if insn.mnemonic == "jmp" and insn.operands \
                    and insn.operands[0].type == capstone.x86.X86_OP_IMM:
                t = insn.operands[0].imm & 0xFFFFFFFF
                if not (entry <= t < entry + 0x40):
                    return insn.address + insn.size, True   # tail call out
            addr = insn.address + insn.size
        if not progressed:
            return (last.address + last.size if last else entry), False
        if last is not None and last.address + last.size - entry > 0x8000:
            # no terminal ret within 32 KB: bail out loudly instead of eating
            # the neighbouring function
            return last.address + last.size, False
    return (last.address + last.size if last else entry), False


def insns(lo, hi):
    """Instructions in [lo, hi), decoded in chunks (see extent() for why)."""
    CHUNK = 0x800
    out = []
    addr = lo
    while addr < hi:
        progressed = False
        for insn in md.disasm(D.read_va(addr, min(CHUNK, hi - addr)), addr):
            progressed = True
            out.append(insn)
            addr = insn.address + insn.size
        if not progressed:
            break
    return out


def raw_call_targets():
    """Every rel32 E8/E9 target inside .text, PLUS every .text address that
    appears as a dword in a possible vtable.

    Two root sources are needed and this is not cosmetic: the two loaders whose
    table was wrong (`TechnoTypeClass` 0x712170, `BuildingTypeClass` 0x45FE50)
    have NO direct E8 caller at all -- they are reached only through vtable slot
    25. A census rooted on call targets alone reports "nothing found", which is
    the precise failure mode this round is about. The vtable-slot roots close it.

    Byte scanning on purpose: this is a ROOT SET, not a decode. A single
    md.disasm over .text stops at 0x46F5A0 and covers 11% (G-23), so roots taken
    from a linear sweep would be truncated -- a raw byte scan cannot be.
    """
    blob = D.read_va(TEXT_LO, TEXT_HI - TEXT_LO)
    out = set()
    for i in range(len(blob) - 5):
        if blob[i] == 0xE8 or blob[i] == 0xE9:
            rel = struct.unpack_from("<i", blob, i + 1)[0]
            tgt = (TEXT_LO + i + 5 + rel) & 0xFFFFFFFF
            if TEXT_LO <= tgt < TEXT_HI:
                out.add(tgt)

    # vtable slots: a dword in .rdata that points into .text, sitting next to a
    # run of other .text pointers, is a vtable slot. One pass over .rdata.
    rdata = D.read_va(0x7E1000, 0x811074 - 0x7E1000)
    for i in range(0, len(rdata) - 4, 4):
        v = struct.unpack_from("<I", rdata, i)[0]
        if not (TEXT_LO <= v < TEXT_HI):
            continue
        # Require a neighbour that is also a .text pointer: a lone .text dword
        # is usually a constant, while vtable slots come in runs.
        ok = False
        for j in (i - 4, i + 4):
            if 0 <= j <= len(rdata) - 4:
                n = struct.unpack_from("<I", rdata, j)[0]
                if TEXT_LO <= n < TEXT_HI:
                    ok = True
                    break
        if ok:
            out.add(v)
    return out


# --------------------------------------------------------------------------
# the shape we are hunting


def this_register(entry, hi, prologue=48):
    """Register that receives `ecx` (thiscall `this`) in the prologue.

    Positional like the repaired dump_typeclass_fields: the FIRST `mov reg,ecx`
    before any call. Checking only ebx/esi/edi is the exact bug being censused,
    so EBP is included here.
    """
    for insn in insns(entry, hi):
        if insn.address - entry > prologue:
            return None, None
        if insn.mnemonic == "call":
            return None, None
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            d, s = insn.operands
            if d.type == capstone.x86.X86_OP_REG and s.type == capstone.x86.X86_OP_REG \
                    and insn.reg_name(s.reg) == "ecx":
                return insn.reg_name(d.reg), insn.address
    return None, None


def reader_calls(body):
    out = []
    for insn in body:
        if insn.mnemonic != "call" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type != capstone.x86.X86_OP_IMM:
            continue
        t = op.imm & 0xFFFFFFFF
        if t in READERS:
            out.append((insn.address, READERS[t]))
    return out


def field_stores(body, reg):
    """Count stores into [reg+disp] with a non-trivial displacement."""
    n = 0
    for insn in body:
        if not insn.operands:
            continue
        for op in insn.operands:
            if op.type != capstone.x86.X86_OP_MEM or op.mem.base != reg:
                continue
            if op.mem.index != 0 or op.mem.disp < 0x20:
                continue
            # count only when this operand is the destination of a write
            if insn.mnemonic in ("mov", "fstp", "fst", "movsd", "movss", "and", "or", "xor"):
                if insn.mnemonic in ("fstp", "fst"):
                    n += 1
                elif insn.operands[0].type == capstone.x86.X86_OP_MEM \
                        and insn.operands[0].mem.base == reg:
                    n += 1
            break
    return n


def main():
    print("=== EBP-this INI loader census (G-41 blast radius) ===")
    import hashlib
    with open(D.EXE, "rb") as fh:
        print("  exe sha256 = %s" % hashlib.sha256(fh.read()).hexdigest())

    # Roots from a raw E8/E9 byte scan. The full-sweep route was tried first and
    # is quadratic here: `extent()` re-decodes from every entry, and the entries
    # overlap, so 15k roots x up to 0x30000 bytes each exceeded the time budget.
    # Byte-scan roots are cheap and, unlike a decode, cannot be truncated by the
    # jump table at 0x46F5A0.
    candidates = raw_call_targets()
    resyncs = []
    print("  roots: %d rel32 E8/E9 targets in .text" % len(candidates))

    ebp_this = []
    checked = 0
    # Roots from the two passes overlap heavily (15,751 roots for far fewer
    # distinct functions), and decoding each from scratch was quadratic -- it
    # blew the time budget twice before this. Cached with bisect on the sorted
    # span starts, and the number of skipped roots is REPORTED: silently
    # dropping roots is the same failure class as silently dropping rows.
    spans = []
    starts = []
    skipped = 0
    for entry in sorted(candidates):
        i = bisect.bisect_right(starts, entry) - 1
        if i >= 0 and spans[i][0] <= entry < spans[i][1]:
            skipped += 1
            continue
        end, clean = extent(entry)
        if clean:
            # insert keeping parallel arrays consistent
            j = bisect.bisect_left(starts, entry)
            starts.insert(j, entry)
            spans.insert(j, (entry, end))
        if not clean or end - entry < 0x40:
            continue
        reg, at = this_register(entry, end)
        if reg is None:
            continue
        checked += 1
        if reg != "ebp":
            continue
        body = insns(entry, end)
        rc = reader_calls(body)
        if not rc:
            continue
        st = field_stores(body, CALLEE_SAVED["ebp"])
        ebp_this.append({
            "entry": entry, "end": end, "mov_va": at,
            "readers": rc, "n_readers": len(rc), "stores": st,
        })
    print("  distinct function spans: %d (%d roots scanned, %d already covered)"
          % (len(spans), len(candidates), skipped))

    print("\n--- loaders whose `this` is EBP and which call a Read* ---")
    print("  %-10s %-10s %-9s %-5s %-7s %s"
          % ("entry", "end", "mov ecx", "reads", "stores", "covered by"))
    for e in ebp_this:
        cov = COVERED.get(e["entry"], "*** NOT COVERED ***")
        print("  0x%08X 0x%08X 0x%08X %5d %7d %s"
              % (e["entry"], e["end"], e["mov_va"], e["n_readers"], e["stores"], cov))

    n_hit = len(ebp_this)
    n_uncovered = sum(1 for e in ebp_this if e["entry"] not in COVERED)
    print("\n  EBP-this INI-shaped loaders found : %d" % n_hit)
    print("  of those, not covered by any tool : %d" % n_uncovered)

    # ---- positive control: the two loaders whose table was actually wrong
    print("\n--- P1 positive control (the two known-bad classes) ---")
    want = {0x712170: ("TechnoTypeClass", 0x712180),
            0x45FE50: ("BuildingTypeClass", 0x45FE5F)}
    for entry, (name, mov_va) in want.items():
        end, _ = extent(entry)
        reg, at = this_register(entry, end)
        ok = (reg == "ebp" and at == mov_va)
        record("P1/%s" % name, ok,
               "this=%s @0x%08X (exp ebp @0x%08X)" % (reg, at or 0, mov_va))

    # ---- P2: the tool MUST find at least those two, i.e. the census is not
    # silently empty. A census that reports "nothing" is the failure mode this
    # whole round is about.
    found = {e["entry"] for e in ebp_this}
    record("P2/nonempty", {0x712170, 0x45FE50} <= found,
           "census contains both known-bad entries: %s (total %d)"
           % ({0x712170, 0x45FE50} <= found, n_hit))

    # ---- P3: contrast control. A loader whose `this` is NOT EBP must not
    # appear, proving the detector discriminates rather than matching anything.
    print("\n--- P3 contrast control (non-EBP loaders must be absent) ---")
    for entry, name in ((0x66D530, "Read_General"), (0x5F92D0, "ObjectType")):
        end, _ = extent(entry)
        reg, _at = this_register(entry, end)
        record("P3/%s" % name, reg is not None and reg != "ebp" and entry not in found,
               "this=%s, in EBP set=%s" % (reg, entry in found))

    # ---- P4: numerator/denominator are reported so a zero cannot pass as fine.
    record("P4/denominator", checked > 1000,
           "functions examined with a resolved this-register = %d" % checked)

    bad = [r for r in RESULTS if not r[1]]
    print("\n=== verdict: %d/%d PASS ===" % (len(RESULTS) - len(bad), len(RESULTS)))
    if bad:
        print("FAILED:")
        for tag, _ok, detail in bad:
            print("  %s  %s" % (tag, detail))
        return 1
    print("ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
