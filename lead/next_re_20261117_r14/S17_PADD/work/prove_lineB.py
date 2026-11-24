"""Full bodies + RTTI holders + vtable install sites for Line B candidates."""
import re_lib as R

CANDS = {
    "004A2990": ("CStreamClass::slot0", 0x004A2990),
    "004A2A20": ("CStreamClass::slot3", 0x004A2A20),
    "004A2CD0": ("CStreamClass::slot4", 0x004A2CD0),
}

for key, (label, va) in CANDS.items():
    print("=" * 100)
    print("[%s] %s @ 0x%08X" % (key, label, va))
    n = 0x180
    for a, mn, op, sz, bh in R.disasm(va, n):
        print("  %08X  %-20s %-8s %s" % (a, bh, mn, op))
        if mn.startswith("ret"):
            break
    print("-- holders --")
    for h in R.holder_scan(va):
        print("  holder dword @ 0x%08X" % h)
        for k in range(0, 20):
            vt = h - k*4
            col = R.read_u32(vt-4)
            if col is None:
                continue
            td = R.read_u32(col+0xC)
            if td is None:
                continue
            nm = R.read_cstr(td+8)
            if nm and (".?AV" in nm or ".?AU" in nm):
                print("    vt=0x%08X slot=%d COL=0x%08X TD=0x%08X name=%r verify=0x%08X" % (
                    vt, k, col, td, nm, R.read_u32(vt+k*4) or 0))
