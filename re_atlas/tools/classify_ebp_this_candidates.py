"""Classify each EBP-this candidate from census_ebp_this_loaders.py.

The census reports a raw count. A count is not a verdict: some of those entries
are RulesClass::Init-style dispatchers (they call a loader once) and some are not
INI loaders at all. This tool decides, per entry, which of three shapes it is:

  KEY_FIELD   at least one `push <printable literal>` immediately feeds a Read*
              call whose result is stored into [this+disp]. This is the shape a
              key->field table is built from, and the shape the EBP bug damaged.
  DISPATCH    calls a Read* but never stores the result into this object
              (initialiser / wrapper / one-shot lookup).
  NO_KEY      calls a Read* only through registers already loaded elsewhere, no
              literal key immediately before the call.

Only KEY_FIELD entries can have been silently under-reported by an
`fstp [ebp+off]`-skipping parser, so only they widen the blast radius.

Run: python re_atlas/tools/classify_ebp_this_candidates.py
"""

import os
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dump_rules_sections as D  # noqa: E402
from census_ebp_this_loaders import extent, insns, READERS  # noqa: E402

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

THIS_REG = capstone.x86.X86_REG_EBP

CANDIDATES = [
    0x0041B110, 0x0041F580, 0x004ACE70, 0x005009B0, 0x0051FB00,
    0x006686C0, 0x006980C0, 0x006B4C80, 0x006CEA20, 0x006E6080,
    0x00727240,
]


def cstr(va, n=48):
    return D.read_va(va, n).split(b"\x00")[0].decode("latin1", "replace")


def classify(entry):
    end, clean = extent(entry)
    body = insns(entry, end)
    reader_idx = []
    for i, insn in enumerate(body):
        if insn.mnemonic == "call" and insn.operands \
                and insn.operands[0].type == capstone.x86.X86_OP_IMM \
                and (insn.operands[0].imm & 0xFFFFFFFF) in READERS:
            reader_idx.append(i)

    keyed_stores = []
    for i in reader_idx:
        # key = nearest printable literal push before this call, within 12 insns
        key = None
        for j in range(max(0, i - 12), i):
            k = body[j]
            if k.mnemonic != "push" or not k.operands \
                    or k.operands[0].type != capstone.x86.X86_OP_IMM:
                continue
            s = cstr(k.operands[0].imm & 0xFFFFFFFF)
            if s and 2 <= len(s) < 48 and all(0x20 < ord(c) < 0x7F for c in s):
                key = s
        if key is None:
            continue
        # store into [this+disp] within the following 16 insns
        store = None
        for j in range(i + 1, min(i + 16, len(body))):
            k = body[j]
            for op in k.operands:
                if op.type == capstone.x86.X86_OP_MEM and op.mem.base == THIS_REG \
                        and op.mem.index == 0 and op.mem.disp >= 0x20:
                    if k.mnemonic in ("mov", "fstp", "fst", "movsd", "movss", "and", "or", "xor"):
                        if k.mnemonic in ("fstp", "fst"):
                            store = (op.mem.disp, k.mnemonic)
                        elif k.operands[0].type == capstone.x86.X86_OP_MEM:
                            store = (op.mem.disp, k.mnemonic)
                    break
            if store:
                break
        if store:
            keyed_stores.append((key, store[0], store[1], body[i].address))

    if keyed_stores:
        shape = "KEY_FIELD"
    elif reader_idx:
        shape = "DISPATCH" if not any(
            op.type == capstone.x86.X86_OP_MEM and op.mem.base == THIS_REG
            and op.mem.index == 0 and op.mem.disp >= 0x20
            for insn in body for op in insn.operands) else "CALLS_BUT_NO_KEY"
    else:
        shape = "NO_KEY"
    return shape, end, clean, keyed_stores, len(reader_idx)


def main():
    print("=== classify EBP-this candidates ===")
    print("  entry      end        clean reads keys  shape")
    key_field = 0
    for entry in CANDIDATES:
        shape, end, clean, keyed, nread = classify(entry)
        if shape == "KEY_FIELD":
            key_field += 1
        print("  0x%08X 0x%08X %-5s %5d %5d %s"
              % (entry, end, clean, nread, len(keyed), shape))
        for k, off, mn, va in keyed[:4]:
            print("        %-28s -> +0x%04X via %s @0x%08X" % (k, off, mn, va))

    print("\n  KEY_FIELD candidates among the 11 uncovered: %d" % key_field)

    # positive control: the two known loaders must classify as KEY_FIELD
    print("\n--- positive control (known loaders must be KEY_FIELD) ---")
    ok = True
    for entry, want in ((0x712170, True), (0x45FE50, True)):
        shape, _e, _c, keyed, _n = classify(entry)
        good = (shape == "KEY_FIELD") == want
        ok = ok and good
        print("  [%s] 0x%08X shape=%s keys=%d"
              % ("PASS" if good else "FAIL", entry, shape, len(keyed)))

    # negative control: a constructor must NOT be KEY_FIELD (no reader calls)
    print("\n--- negative control (ctor must not be KEY_FIELD) ---")
    shape, _e, _c, keyed, nread = classify(0x710AF0)
    good = shape != "KEY_FIELD" and nread == 0
    ok = ok and good
    print("  [%s] TechnoType ctor shape=%s reads=%d"
          % ("PASS" if good else "FAIL", shape, nread))

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
