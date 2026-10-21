"""R2-1: recover the AbstractType ID table and the abstract-class vtable contract.

Three independent recoveries, cross-checked against each other:

  1. vtable[11] -> WhatAmI()  : a `mov eax, imm8; ret` returning the class's
     AbstractType id.  Recovered from every class RTTI found a vtable for.
  2. vtable[12] -> GetSize()  : a `mov eax, imm32; ret` returning the instance size.
  3. the engine's own name table at 0x816EE0 (74 x {char* name, u32 value}).

(1) and (3) must agree; where they do, the id assignment stops being an inference.
Read-only.  Usage: python re_atlas/tools/dump_class_ids.py [--json]
"""

import json
import os
import struct
import sys

import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E1000
RDATA_LO, RDATA_HI = 0x7E1000, 0x812000

NAME_TBL, NAME_N = 0x816EE0, 74

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(HERE, "..", "evidence", "rtti", "classes_meta.json")


def load(path):
    with open(path, "rb") as fh:
        return fh.read()


D = load(EXE)
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)


def u32(va):
    if va is None:
        return None
    off = va - IB
    if off < 0 or off + 4 > len(D):
        return None
    return struct.unpack_from("<I", D, off)[0]


def read_va(va, n):
    off = va - IB
    if off < 0 or off + n > len(D):
        return b""
    return D[off:off + n]


def cstr(va, cap=64):
    raw = read_va(va, cap)
    return raw.split(b"\x00")[0].decode("latin1")


def immediate(fn):
    """Decode `mov eax, imm; ret` and return imm, else None.

    Two traps here, both of which silently produce an EMPTY result set rather
    than an error -- always keep a positive control in the output:

    1. capstone renders operands with a space after the comma ("eax, 0x30").
    2. it renders small immediates in DECIMAL and large ones in hex
       ("eax, 1" vs "eax, 0xd4"). A string test for the "0x" prefix therefore
       skips every id 0x00..0x09 and every size below 10.

    So read the operand structure, not the rendered text.
    """
    if fn is None or not (TEXT_LO <= fn < TEXT_HI):
        return None
    mdi = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    mdi.detail = True
    for insn in list(mdi.disasm(read_va(fn, 16), fn))[:3]:
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            dst, src = insn.operands
            if dst.type == capstone.x86.X86_OP_REG and src.type == capstone.x86.X86_OP_IMM:
                if insn.reg_name(dst.reg) == "eax":
                    return src.imm & 0xFFFFFFFF
        if insn.mnemonic.startswith("ret"):
            break
    return None


def main():
    if not os.path.exists(META):
        sys.exit("missing %s -- run the RTTI extractor first" % META)

    with open(META, encoding="utf-8") as fh:
        classes = json.load(fh)["classes"]

    # --- 3. the engine's own name table -------------------------------------
    names = {}
    for i in range(NAME_N):
        ptr = u32(NAME_TBL + 8 * i)
        val = u32(NAME_TBL + 8 * i + 4)
        if ptr is None or val is None:
            continue
        names[val] = cstr(ptr)

    # --- 1 & 2. per-class vtable[11]/[12] -----------------------------------
    rows = []
    no_vt = 0
    for cls in classes:
        vt = cls.get("vtable")
        if not vt:
            no_vt += 1
            continue
        vt = int(vt, 16) if isinstance(vt, str) else int(vt)
        id_fn, size_fn = u32(vt + 0x2C), u32(vt + 0x30)
        cid, size = immediate(id_fn), immediate(size_fn)
        if cid is None or size is None:
            continue
        # Bounds. The id must be a real AbstractType (name table has 74 entries,
        # 0x00..0x49); anything else means slot 11 holds an accessor that returns
        # a pointer into .rdata, not a type id.
        if not (0 <= cid <= 0x49):
            continue
        # The size must be a plausible allocation. There is NO small upper bound:
        # HouseClass is 0x160B8 (90,296). An earlier 0x4000 cap silently dropped
        # every large class -- which is exactly the 15 "missing" ids L-17 asked
        # about. Filter on the HRESULT shape instead, which is what a failed
        # interface method returns (0x8000xxxx).
        if not (0 < size <= 0x400000):
            continue
        if 0x80000000 <= size <= 0x8000FFFF:
            continue
        rows.append({
            "class": cls["name"],
            "vtable": "0x%08X" % vt,
            "id": cid,
            "id_fn": "0x%08X" % id_fn,
            "size": size,
            "size_fn": "0x%08X" % size_fn,
            "engine_name": names.get(cid),
        })

    rows.sort(key=lambda r: r["id"])

    # --- consistency --------------------------------------------------------
    seen = {}
    for r in rows:
        seen.setdefault(r["id"], []).append(r["class"])
    collisions = {k: v for k, v in seen.items() if len(v) > 1}

    # vtable-index sanity: an id is trustworthy when the engine's table maps the
    # SAME number to a name that is a prefix of (or equal to) the RTTI class name.
    agree, disagree, unknown = [], [], []
    for r in rows:
        nm = r["engine_name"]
        if nm is None:
            unknown.append(r)
            continue
        base = r["class"]
        # engine names drop the Class suffix and use CamelCase variants
        stem = base[:-5] if base.endswith("Class") else base
        if nm.lower() in (stem.lower(), base.lower()) or stem.lower().startswith(nm.lower()):
            agree.append(r)
        else:
            disagree.append(r)

    if "--json" in sys.argv:
        print(json.dumps({
            "classes_with_vtable": len(classes) - no_vt,
            "rows": rows,
            "collisions": collisions,
            "engine_names": {str(k): v for k, v in sorted(names.items())},
        }, indent=1))
        return

    print("classes with a vtable      : %d (no vtable: %d)" % (len(classes) - no_vt, no_vt))
    print("classes with BOTH vtable[11] and vtable[12] immediates: %d" % len(rows))
    print("distinct ids               : %d" % len(seen))
    print("ids claimed by >1 class    : %d %s" % (len(collisions), sorted(collisions) or ""))
    print()
    print("%-5s %-6s %-34s %-11s %s" % ("id", "size", "class", "vtable", "engine name"))
    for r in rows:
        print("0x%02X  %-6d %-34s %-11s %s"
              % (r["id"], r["size"], r["class"], r["vtable"], r["engine_name"]))
    print()
    print("engine table 0x%08X : %d entries, %d distinct ids"
          % (NAME_TBL, NAME_N, len(names)))
    ids_in_tbl = set(names)
    ids_found = set(seen)
    print("ids in engine table but no class recovered : %s"
          % sorted("0x%02X(%s)" % (i, names[i]) for i in ids_in_tbl - ids_found))
    print("ids recovered but absent from engine table : %s"
          % sorted("0x%02X(%s)" % (i, seen[i][0]) for i in ids_found - ids_in_tbl))
    print()
    print("name agreement  : %d" % len(agree))
    print("name DISAGREE   : %d -> %s"
          % (len(disagree), [(r["id"], r["class"], r["engine_name"]) for r in disagree] or ""))
    print("no engine name  : %d -> %s"
          % (len(unknown), [(r["id"], r["class"]) for r in unknown] or ""))


main()
