"""Per-row structural analysis: all holding tables, TD->all COLs, all vt write sites with
ctor/dtor classification, and ③b sentinel candidates in the body."""
import sys
import struct
from pe import (SECTIONS, RAW, TEXT_LO, TEXT_HI, u32, u8, read, cstr, fmt, dis, win,
                find_imm32, rtti, slots, tables_holding, func_extent, in_text, sec_of,
                BY, ORDER, MDD)

ATEXIT = 0x7C978A


def all_cols():
    out = []
    for s in SECTIONS:
        if s["ch"] & 0x20000000:
            continue
        blob = RAW[s["rawptr"]: s["rawptr"] + s["rawsize"]]
        for k in range(0, len(blob) - 16, 4):
            va = s["va"] + k
            sig = struct.unpack_from("<I", blob, k)[0]
            if sig not in (0, 1):
                continue
            td = struct.unpack_from("<I", blob, k + 12)[0]
            if not (0x7E1000 <= td < 0xB8C000):
                continue
            nm = cstr(td + 8, 80)
            if nm.startswith(".?"):
                out.append(dict(col=va, td=td, name=nm))
    return out


COLS = None


def cols_of_td(td):
    global COLS
    if COLS is None:
        COLS = all_cols()
    return [c for c in COLS if c["td"] == td]


def vtables_of_td(td):
    """For each COL, find the vtable that points at it: a dword equal to COL followed by
    code pointers. Returns list of (vt, col)."""
    out = []
    for c in cols_of_td(td):
        for occ in find_imm32(c["col"]):
            vt = occ + 4
            p = u32(vt)
            if p is not None and in_text(p):
                out.append((vt, c["col"]))
    return sorted(set(out))


def classify_fn(entry, body=None):
    if body is None:
        body = func_extent(entry)
    calls = [i for i in body if i.mnemonic == "call"]
    freed = [i for i in calls if i.op_str in ("0x7c8b3d", "0x7c8b1f", "0x7c8a37", "0x7c8b9c")]
    news = [i for i in calls if i.op_str in ("0x7c8e17", "0x7c8e05")]
    rets = [i for i in body if i.mnemonic.startswith("ret")]
    return dict(size=(body[-1].address + body[-1].size - entry) if body else 0,
                ncalls=len(calls), nfree=len(freed), nnew=len(news), nret=len(rets),
                body=body)


def enclosing_fn(vt_write_site):
    """Find the containing function start by scanning back for a start whose linear
    decode lands exactly on the write site."""
    cands = []
    a = vt_write_site
    back = 0
    # walk backwards through BY map last<=... simple: test starts in [site-0x800, site)
    for s in range(vt_write_site - 0x800, vt_write_site):
        if s < TEXT_LO:
            continue
        i = BY.get(s)
        if i is None:
            continue
        cur = s
        n = 0
        ok = True
        while cur < vt_write_site and n < 3000:
            j = BY.get(cur)
            if j is None:
                ok = False
                break
            cur += j.size
            n += 1
        if ok and cur == vt_write_site:
            # prefer starts preceded by padding/ret
            prevbyte = u8(s - 1)
            score = 1 if prevbyte in (0xCC, 0x90, 0xC3) else 0
            cands.append((score, s))
    if not cands:
        return None
    cands.sort()
    return cands[-1][1]


def report(entry_s, name):
    entry = int(entry_s, 16)
    print("=" * 100)
    print("ROW %s  %s" % (entry_s, name))
    th = tables_holding(entry)
    print("  [2] holding tables: %d" % len(th))
    tds = []
    for t in th:
        r = t["rtti"]
        print("      vt=%08X slot=%2d (+0x%02X) slot_at=%08X COL=%08X TD=%08X %s" % (
            t["base"], t["slot"], 4 * t["slot"], t["slot_at"], r["col"], r["td"], r["name"]))
        tds.append(r["td"])
    print("  [2b] every COL per involved TD (does the class have several vtables?):")
    for td in sorted(set(tds)):
        vs = vtables_of_td(td)
        nm = cstr(td + 8, 80)
        print("      TD %08X %s -> %d vtable(s): %s" % (
            td, nm, len(vs), " ".join("%08X(col %08X)" % (v, c) for v, c in vs)))
    print("  [4] vt write sites per holding table:")
    for t in th:
        vt = t["base"]
        occ = find_imm32(vt)
        print("      vt %08X : %d dword occurrence(s)" % (vt, len(occ)))
        for o in occ:
            if not in_text(o):
                print("        DATA %08X (%s) -- static initialiser" % (o, sec_of(o)["name"]))
                continue
            ins = None
            for base in range(o - 12, o + 8):
                b = read(base, 16)
                if b is None:
                    break
                for i in MDD.disasm(b, base):
                    if i.address > o:
                        break
                    if i.id == 0:
                        continue
                    if any(op.type == 2 and op.imm == vt for op in i.operands):
                        ins = i
            fn = enclosing_fn(o)
            cl = classify_fn(fn) if fn else None
            print("        TEXT %08X  %s" % (o, fmt(ins) if ins else "(?)"))
            if fn:
                print("             in_func=%08X size=%d calls=%d free=%d new=%d rets=%d" % (
                    fn, cl["size"], cl["ncalls"], cl["nfree"], cl["nnew"], cl["nret"]))
            else:
                print("             in_func=?")
    print("  [3] body (%d insns):" % len(func_extent(entry)))
    for i in func_extent(entry):
        print("      " + fmt(i))
    print()


if __name__ == "__main__":
    import rows
    want = sys.argv[1:]
    for e, sub, nm in rows.ROWS:
        if not want or e in want:
            report(e, nm)
