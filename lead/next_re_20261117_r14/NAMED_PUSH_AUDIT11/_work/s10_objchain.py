import sys, json, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

ENTRIES = ["006C2B10", "006C2C90", "006C2E10", "006C2F90", "006C3110", "006C3290",
           "006C3410", "006C3590", "006C3890", "006C3A10", "006C3B90"]


def body(va, maxb=400):
    out = []
    for i in dis(va, maxb):
        if i.mnemonic == "nop":
            break
        out.append(i)
    return out


def is_vt_val(v):
    return v is not None and 0x7E0000 <= v < 0x810000 and (v % 4 == 0)


def ctor_vt_writes(fn_va, depth=0, seen=None, maxdepth=3):
    """collect c7 /0 writes of a plausible vtable constant, with the dest operand text"""
    if seen is None:
        seen = set()
    if fn_va in seen or depth > maxdepth:
        return []
    seen.add(fn_va)
    out = []
    for i in body(fn_va, 600):
        if i.mnemonic != "mov":
            continue
        m = re.match(r"dword ptr \[([^\]]+)\], (0x[0-9a-f]+)$", i.op_str)
        if not m:
            continue
        v = int(m.group(2), 16)
        if is_vt_val(v):
            out.append({"at": f"{i.address:08X}", "dst": m.group(1), "vt": f"{v:08X}",
                        "bytes": i.bytes.hex(" "), "fn": f"{fn_va:08X}", "depth": depth})
    return out


def callees(fn_va, maxb=600):
    res = []
    for i in body(fn_va, maxb):
        if i.mnemonic in ("call", "jmp") and i.op_str.startswith("0x"):
            t = int(i.op_str, 16)
            s = sec_of(t)
            if s and s[0] == ".text":
                res.append(t)
    return res


def resolve_chain(fn_va, maxdepth=3):
    """BFS over call tree, return all vtable writes found anywhere"""
    frontier = [(fn_va, 0)]
    seen = set()
    res = []
    while frontier:
        f, d = frontier.pop(0)
        if f in seen or d > maxdepth:
            continue
        seen.add(f)
        res.extend(ctor_vt_writes(f, d, set(), 0))
        for c in callees(f):
            frontier.append((c, d + 1))
    return res


def vt_info(vt):
    return {
        "vt": f"{vt:08X}",
        "slot0": f"{u32(vt):08X}" if u32(vt) else None,
        "slot0_is_410260": u32(vt) == 0x410260,
        "rtti": rtti_class(vt),
    }


def rtti_class(vt_va):
    d = {}
    col = u32(vt_va - 4)
    d["col"] = f"{col:08X}" if col else None
    if not col:
        return d
    s = sec_of(col)
    d["col_sec"] = s[0] if s else None
    td = u32(col + 0xC)
    d["td"] = f"{td:08X}" if td else None
    if not td:
        return d
    nm = cstr(td + 8, 300)
    d["name"] = nm
    d["name_ok"] = bool(nm and nm.startswith(".?A"))
    return d


print("### per-row object-constructor chain vt writes")
for e in ENTRIES:
    va = int(e, 16)
    ins = body(va)
    ctor = None
    for i in ins:
        if i.mnemonic == "call" and i.op_str.startswith("0x") and i.op_str != "0x7c8e17":
            ctor = int(i.op_str, 16)
            break
    print("=" * 112)
    print(f"ENTRY {e}  obj_ctor={ctor:08X}")
    writes = resolve_chain(ctor, 3)
    # dedupe by (at)
    seenat = set()
    w2 = []
    for w in writes:
        if w["at"] in seenat:
            continue
        seenat.add(w["at"])
        w2.append(w)
    for w in w2:
        info = vt_info(int(w["vt"], 16))
        print(f"   {w['at']}  dst=[{w['dst']}]  vt={w['vt']}  slot0={info['slot0']} "
              f"slot0_410260={info['slot0_is_410260']}  rtti={info['rtti'].get('name')} "
              f"name_ok={info['rtti'].get('name_ok')}  bytes={w['bytes']}  (from {w['fn']} d{w['depth']})")
    if not w2:
        print("   !! no vtable write found in chain")
