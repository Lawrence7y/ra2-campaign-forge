"""Reusable analysis helpers for S07-K2."""
import sys, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
from audit_lib import Bin, md32, load_func_atlas, entry_at_or_before
import capstone

BIN = Bin()
ATLAS_ROWS, ATLAS_HDR = load_func_atlas()
ATLAS_ENTRIES = [va for va, _ in ATLAS_ROWS]
ATLAS_MAP = {va: rec for va, rec in ATLAS_ROWS}

def func_range(va):
    """Return (entry, size) of the atlas function containing va via interval containment, else None."""
    # binary search for greatest entry <= va, then check va < entry+size
    import bisect
    i = bisect.bisect_right(ATLAS_ENTRIES, va) - 1
    if i < 0:
        return None
    e = ATLAS_ENTRIES[i]
    rec = ATLAS_MAP[e]
    try:
        size = int(rec.get("size", "0"))
    except Exception:
        size = 0
    if size and va < e + size:
        return (e, size)
    return None

def disasm(va, nbytes, skipdata=True):
    data = BIN.read(va, nbytes)
    m = md32(skipdata=skipdata)
    out = []
    for insn in m.disasm(data, va):
        out.append(insn)
    return out

def dump(va, nbytes=0x100, skipdata=True):
    for insn in disasm(va, nbytes, skipdata):
        fr = func_range(insn.address)
        tag = ""
        if fr and fr[0] == insn.address:
            tag = "  <== FUNC entry size=%d" % fr[1]
        print("%08X  %-24s %s%s" % (insn.address, insn.bytes.hex(), (insn.mnemonic + " " + insn.op_str).strip(), tag))

if __name__ == "__main__":
    import sys
    va = int(sys.argv[1], 16)
    n = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x100
    dump(va, n)
