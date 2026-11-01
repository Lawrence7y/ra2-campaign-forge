"""R1: function census via recursive traversal from known roots.

A linear capstone sweep decodes only ~11% of .text here (it desyncs on data
embedded in the section), so the denominator must come from a worklist walk
that follows call/jump edges from real entry points. Roots: PE entry point,
the E8 call targets and every vtable slot from RTTI.

R-060 (D-06 option C, 2026-10-25) -- TWO defects fixed at the root set:

  (a) E9 is NOT an entry source.  `jmp rel32` doubles as MSVC's intra-function
      block jump; every E9 target previously promoted to "function entry"
      inflated the count (R-035: 1,445 of 2,042 E9 targets land inside already
      covered bodies).  The walk still FOLLOWS jmp edges, but they no longer
      seed the root/entry set.

  (b) E8 came from a byte scan (`re.finditer(b"\\xe8")`) -- 563 of those bytes
      are operands inside other instructions and their bogus rel32s pointed at
      560 targets NO real call reaches.  The root set now uses the ALIGNED
      reading: a resuming sweep that records exactly the addresses where
      capstone decodes a `call rel32`, and takes their targets.  Both readings
      are printed so the byte-scan figure stays reproducible as an UPPER bound.

  Verified numbers (sha256 73201cc0...f67476): aligned roots = 12,792,
  byte-scan-with-E9 roots (the old broken build) = 15,224, aligned walk entries
  = 12,792 (the CFG discovers nothing new -- roots already close under calls).

Read-only; prints a report.
"""

import hashlib
import json
import re
import struct

import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
SYMS = ROOT + r"\re_atlas\evidence\symbol_map.json"
RTTI = ROOT + r"\re_atlas\evidence\rtti\symbols.json"
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"


def load_pe(path):
    with open(path, "rb") as fh:
        blob = fh.read()
    e = struct.unpack_from("<I", blob, 0x3C)[0]
    nsec = struct.unpack_from("<H", blob, e + 6)[0]
    opt_size = struct.unpack_from("<H", blob, e + 20)[0]
    opt = e + 24
    image_base = struct.unpack_from("<I", blob, opt + 28)[0]
    entry_rva = struct.unpack_from("<I", blob, opt + 16)[0]
    tab = opt + opt_size
    secs = []
    for i in range(nsec):
        o = tab + i * 40
        name = blob[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", blob, o + 8)
        secs.append({"name": name, "va": image_base + vaddr, "vsize": vsize,
                     "rawptr": rawptr, "rawsize": rawsize})
    return blob, image_base, entry_rva, secs


BLOB, IB, ENTRY_RVA, SECS = load_pe(EXE)
TEXT = next(s for s in SECS if s["name"] == ".text")
TLO, THI = TEXT["va"], TEXT["va"] + TEXT["rawsize"]
CODE = BLOB[TEXT["rawptr"]: TEXT["rawptr"] + TEXT["rawsize"]]
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True


def raw_rel32_targets():
    """BYTE-SCAN reading (upper bound only): every E8/E9 rel32 landing in .text.

    Kept for historical reproducibility of the old numbers; NOT used for roots
    any more (docstring defects a+b)."""
    out = set()
    for op in (b"\xe8", b"\xe9"):
        for m in re.finditer(op, CODE):
            i = m.start()
            if i + 5 > len(CODE):
                continue
            d = struct.unpack_from("<i", CODE, i + 1)[0]
            t = TLO + i + 5 + d
            if TLO <= t < THI:
                out.add(t)
    return out


def aligned_call_targets():
    """RESUMING aligned sweep (R-060): only 0xE8 bytes at addresses where capstone
    decodes `call rel32` count.  On a decode failure advance 1 byte and retry --
    .text holds embedded data and a purely linear sweep desyncs (this file's own
    docstring says so).  This is the same engine r038/verify_r035 P2b uses; the
    production census must not be looser than its own gate."""
    outs = set()
    starts = 0
    cur = TLO
    while cur < THI:
        off = cur - TLO
        got = None
        for insn in MD.disasm(CODE[off:off + 16], cur):
            got = insn
            break
        if got is None:
            cur += 1
            continue
        if (got.mnemonic == "call" and got.operands
                and got.operands[0].type == capstone.x86.X86_OP_IMM):
            starts += 1
            t = got.operands[0].imm
            if TLO <= t < THI:
                outs.add(t)
        cur += got.size
    return outs, starts


def vtable_targets():
    d = json.load(open(RTTI, encoding="utf-8"))
    out = set()
    for _k, c in d["classes"].items():
        for s in c.get("vfuncs") or []:
            try:
                v = int(s, 16)
            except (TypeError, ValueError):
                continue
            if TLO <= v < THI:
                out.add(v)
    return out


def walk(roots, limit_insns=4_000_000):
    """Recursive traversal: follow calls and intra-function jumps."""
    seen = set()
    funcs = set()
    work = [(r, "func") for r in roots]
    insns = 0
    while work:
        addr, kind = work.pop()
        if not (TLO <= addr < THI):
            continue
        if kind == "func":
            if addr in funcs:
                continue
            funcs.add(addr)
        elif addr in seen:
            continue
        cur = addr
        for _step in range(20000):
            if not (TLO <= cur < THI):
                break
            off = cur - TLO
            for insn in MD.disasm(CODE[off:off + 16], cur):
                insns += 1
                if insns > limit_insns:
                    return funcs, insns
                nxt = insn.address + insn.size
                seen.add(insn.address)
                mn = insn.mnemonic
                if mn == "call" and insn.operands and insn.operands[0].type == capstone.x86.X86_OP_IMM:
                    work.append((insn.operands[0].imm, "func"))
                    cur = nxt
                    continue
                if mn.startswith("j"):
                    if insn.operands and insn.operands[0].type == capstone.x86.X86_OP_IMM:
                        tgt = insn.operands[0].imm
                        if mn == "jmp":
                            if TLO <= tgt < THI:
                                cur = tgt
                            else:
                                break
                            continue
                        if TLO <= tgt < THI:
                            work.append((tgt, "jump"))
                        cur = nxt
                        continue
                    cur = nxt
                    continue
                if mn in ("ret", "retf", "hlt", "ud2"):
                    break
                if mn == "jmp" or mn in ("iretd",):
                    break
                cur = nxt
                break  # only one instruction per disasm() call slice
            else:
                break
            if cur == nxt:
                continue
            break
    return funcs, insns


def main():
    h = hashlib.sha256(BLOB).hexdigest()
    if h != SHA256:
        print(f"!! fingerprint drift: {h} != {SHA256}  (refusing to publish)")
        raise SystemExit(2)
    aligned, call_sites = aligned_call_targets()
    rel_bs = raw_rel32_targets()
    vt = vtable_targets()
    entry = IB + ENTRY_RVA
    print(f"# .text 0x{TLO:08X}..0x{THI:08X}  entry=0x{entry:08X}")
    print(f"# fingerprint OK sha256={h[:16]}…")
    print(f"# ALIGNED call rel32: {call_sites:,} call sites -> {len(aligned):,} "
          f"in-.text targets  [R-060 primary]")
    print(f"# (byte-scan E8∪E9 would yield {len(rel_bs):,} targets -- upper bound "
          f"only, NOT used as roots)")
    print(f"# roots: aligned-E8 {len(aligned):,} ∪ vtable {len(vt):,} ∪ PE 1")
    roots = aligned | vt | {entry}
    funcs, insns = walk(roots)
    print(f"# traversal decoded instructions: {insns:,}")
    print(f"# distinct function entries discovered: {len(funcs):,} "
          f"(LOWER-aligned reading; UPPER adds unreachable prologue heads -- "
          f"see verify_r035_claims R1..R6)")

    smap = json.load(open(SYMS, encoding="utf-8"))["map"]
    named = {int(k, 16) for k in smap}
    hit = funcs & named
    print(f"# entries with a corpus name: {len(hit):,} "
          f"({100.0 * len(hit) / max(1, len(funcs)):.2f}%)")
    named_in_text = {v for v in named if TLO <= v < THI}
    print(f"# corpus names landing on an entry: {len(named_in_text & funcs):,} "
          f"of {len(named_in_text):,}")
    orphan = sorted(named_in_text - funcs)
    print(f"# corpus names NOT on a discovered entry: {len(orphan):,} "
          f"(mid-function sites or data)")


main()
