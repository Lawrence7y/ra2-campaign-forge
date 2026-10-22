"""R1: function census via recursive traversal from known roots.

A linear capstone sweep decodes only ~11% of .text here (it desyncs on data
embedded in the section), so the denominator must come from a worklist walk
that follows call/jump edges from real entry points. Roots: PE entry point,
the raw E8/E9 target set, and every vtable slot from RTTI.

Read-only; prints a report.
"""

import json
import re
import struct

import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
SYMS = ROOT + r"\re_atlas\evidence\symbol_map.json"
RTTI = ROOT + r"\re_atlas\evidence\rtti\symbols.json"


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
    """Every E8/E9 rel32 that lands in .text; cheap and instruction-agnostic."""
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


VENDORED_IMM32 = re.compile(rb"[\x00-\xff]{4}")


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
    rel = raw_rel32_targets()
    vt = vtable_targets()
    entry = IB + ENTRY_RVA
    print(f"# .text 0x{TLO:08X}..0x{THI:08X}  entry=0x{entry:08X}")
    print(f"# roots: rel32 E8/E9={len(rel)}  vtable slots={len(vt)}  entry=1")
    roots = rel | vt | {entry}
    funcs, insns = walk(roots)
    print(f"# traversal decoded instructions: {insns:,}")
    print(f"# distinct function entries discovered: {len(funcs):,}")

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
