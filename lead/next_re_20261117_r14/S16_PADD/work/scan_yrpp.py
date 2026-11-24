import os, re, sys
ROOT = r"D:\Project\ra2-campaign-forge"
YRPP = ROOT + r"\YRpp"
PLACE = "00430BA0 0053A6C0 0053D8E0 0053DDA0 0065E660 006CE240 006CE2D0 006CE320 0071AB60 0053DA40 0053DA70 0053DA90 0053DAA0 0053DAE0 0053DB90 0053DBC0 0053DC00 0053DC20 0053DCD0 0053DD00 0053DD50 006CDEB0 006CDFF0 006CE1F0 006CE7C0 006CE800 006CEA10 006CEF80 0071A650 0071A660 0071A700 0071A720 0071A760 0071B190 0071B1A0 0071B1B0".split()
pats = {hx: re.compile(re.escape(hx[2:]), re.I) for hx in PLACE}
hits = {hx: [] for hx in PLACE}
nfiles = 0
for dp, dirs, files in os.walk(YRPP):
    for fn in files:
        if not fn.lower().endswith((".h", ".cpp", ".c", ".txt")):
            continue
        fp = os.path.join(dp, fn)
        nfiles += 1
        try:
            with open(fp, encoding="utf-8", errors="replace") as f:
                for ln, line in enumerate(f, 1):
                    for hx, pat in pats.items():
                        if pat.search(line):
                            hits[hx].append((os.path.relpath(fp, ROOT), ln, line.strip()[:160]))
        except Exception:
            pass
print("YRpp files scanned:", nfiles)
print()
for hx in PLACE:
    hs = hits[hx]
    if hs:
        print("=== %s : %d hits ===" % (hx, len(hs)))
        for rel, ln, txt in hs[:12]:
            print("   %s:%d: %s" % (rel, ln, txt))
        print()
print("=== ZERO YRpp binding ===")
print(", ".join(hx for hx in PLACE if not hits[hx]))
