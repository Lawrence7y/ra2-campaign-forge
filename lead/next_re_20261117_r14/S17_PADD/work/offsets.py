"""Print entry-relative offsets for key ③b instructions of the 3 chosen rows."""
import re_lib as R

TARGETS = {
    0x006CF240: [0x80004003, 0x80004002, 0, "cmpsd", "backedge"],
    0x006CF430: [0x80004003, 0x80004002, 0, "cmpsd", "addref"],
    0x004A2990: [0x80004003, 0x80004002, 0, "cmpsd", "addref"],
}
for va, keys in TARGETS.items():
    print("="*90)
    print("0x%08X" % va)
    size = 0xC0
    for a, mn, op, sz, bh in R.disasm(va, size):
        off = a - va
        flags = []
        if mn == "mov" and op.startswith("eax, 0x"):
            try:
                iv = int(op[7:],16)
                if iv in (0x80004003,0x80004002,0x80004005,0x8000FFFF): flags.append("HRESULT=0x%08X"%iv)
            except ValueError: pass
        if mn == "xor" and op == "eax, eax": flags.append("S_OK=0")
        if "cmpsd" in mn: flags.append("GUID16-cmp")
        if mn == "call" and "+ 4]" in op: flags.append("AddRef-call")
        if mn == "mov" and "dword ptr [edx + eax*8" in op: flags.append("8byte-pair-write")
        if mn == "mov" and op.endswith("], 0"): flags.append("zero-mark")
        if flags:
            print("  +0x%02X  %-18s %-8s %-28s %s" % (off, bh, mn, op, "; ".join(flags)))
