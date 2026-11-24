"""Scan YRpp for CALL(0x...)/JMP_THIS(0x...) address bindings to S17 sub_ candidates (§8.5 channel 1)."""
import os
import re

YRPP = r"D:\Project\ra2-campaign-forge\YRpp"
CANDS = ["004068E0", "0040E340", "00427940", "0042E410", "00433CF0",
         "0049F740", "0049F8B0", "00773450"]

# Build patterns: YRpp uses CALL(0x004068E0), JMP_THIS(0x...), etc.
patterns = {}
for c in CANDS:
    patterns[c] = re.compile(
        r"(CALL|JMP_THIS|JMP_STD)\s*\(\s*0x?" + c + r"\b", re.I)

hits = {c: [] for c in CANDS}
# also plain hex token presence
plain = {c: re.compile(r"\b0x?" + c + r"\b", re.I) for c in CANDS}
plainhits = {c: 0 for c in CANDS}

nfiles = 0
for root, dirs, files in os.walk(YRPP):
    for fn in files:
        if not fn.lower().endswith((".h", ".cpp", ".txt", ".html", ".source", ".inl")):
            continue
        path = os.path.join(root, fn)
        try:
            txt = open(path, "r", encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        nfiles += 1
        for c in CANDS:
            for m in patterns[c].finditer(txt):
                ln = txt.count("\n", 0, m.start()) + 1
                hits[c].append((os.path.relpath(path, YRPP), ln, m.group(0)))
            plainhits[c] += len(plain[c].findall(txt))

print(f"YRpp files scanned: {nfiles}")
print("\n=== §8.5 channel-1 bindings (CALL/JMP_THIS/JMP_STD) ===")
for c in CANDS:
    print(f"  0x{c}: {len(hits[c])} binding(s)")
    for rel, ln, g in hits[c][:10]:
        print(f"      {rel}:{ln}  {g}")
print("\n=== plain hex token counts (context only, NOT a binding) ===")
for c in CANDS:
    print(f"  0x{c}: {plainhits[c]}")
