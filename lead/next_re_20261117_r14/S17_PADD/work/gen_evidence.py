"""Generate EVIDENCE/disasm_<entry>.txt for the 3 delta rows (bounded by atlas size)."""
import re_lib as R

TAB = chr(9)
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
asize = {}
for ln in open(ATLAS, encoding="utf-8", errors="replace").read().splitlines()[1:]:
    c = ln.split(TAB)
    if len(c) >= 2:
        try: asize[c[0].upper()] = int(c[1])
        except ValueError: pass

ROWS = ["006CF240", "006CF430", "004A2990"]
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17_PADD\EVIDENCE"
for e in ROWS:
    va = int(e, 16); sz = asize.get(e, 0x80)
    lines = []
    lines.append("S17-PADD byte evidence for entry 0x%s" % e)
    lines.append("target ra2youli\\gamemd.exe SHA-256 73201CC0...F67476; ImageBase 0x400000")
    lines.append("capstone 5.0.7 skipdata=True; atlas size=0x%X (0x%08X..0x%08X)" % (sz, va, va+sz))
    lines.append("")
    b = R.read_bytes(va, sz)
    lines.append("RAW BYTES (%d): %s" % (len(b), b.hex() if b else ""))
    lines.append("")
    lines.append("DISASM (entry-relative offset, bytes, mnemonic, operands):")
    for a, mn, op, s, bh in R.disasm(va, sz):
        if a >= va + sz: break
        lines.append("  +0x%03X  0x%08X  %-20s %-8s %s" % (a-va, a, bh, mn, op))
    path = OUT + "\\disasm_" + e + ".txt"
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("wrote", path, len(lines), "lines")
