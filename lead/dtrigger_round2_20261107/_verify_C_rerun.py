# -*- coding: utf-8 -*-
# 独立复核 C：比对重跑产物、独立解析三张时序表、核查 §9.7 措辞支撑
import hashlib, os

ROOT = r"D:/Project/ra2-campaign-forge"
WD = os.path.join(ROOT, "lead/dtrigger_round2_20261107")
CMP = os.path.join(ROOT, "lead/dtrigger_compare_20261107")

def rd(p):
    return open(p, "r", encoding="utf-8").read()

new_stdout = rd(os.path.join(WD, "_verify_C_rerun_stdout.txt"))
landed_stdout = rd(os.path.join(WD, "_dC_stdout.txt"))
stderr = rd(os.path.join(WD, "_verify_C_rerun_stderr.txt"))
print("re-run stderr bytes =", len(stderr.encode("utf-8")))
print("re-run stdout == landed _dC_stdout.txt =", new_stdout == landed_stdout)
print("re-run stdout sha256 =", hashlib.sha256(new_stdout.encode("utf-8")).hexdigest())
print("landed stdout sha256 =", hashlib.sha256(landed_stdout.encode("utf-8")).hexdigest())

main = new_stdout.split("@@CELLS_BEGIN@@")[0]
cells_part = new_stdout.split("@@CELLS_BEGIN@@")[1].split("@@CELLS_END@@")[0].strip("\n")
landed_out = rd(os.path.join(WD, "_dC_out.txt"))
landed_cells = rd(os.path.join(WD, "_dC_cells.txt"))
print("main == _dC_out.txt =", main == landed_out, "(main chars %d / landed %d)" % (len(main), len(landed_out)))
print("cells == _dC_cells.txt =", cells_part == landed_cells, "(cells chars %d / landed %d)" % (len(cells_part), len(landed_cells)))
cell_lines = [l for l in cells_part.split("\n") if "|" in l and l.strip().startswith("C")]
print("cell data rows =", len(cell_lines))

thirteen = ["C2-N16-P95x2", "C2-P95x2", "C2-P95x3", "C2-P99x2", "C2-P99x3", "C2-abs-P95x2",
            "C3-N16-r2", "C3-r12", "C3-r2", "C3-r4", "C3-r4-clean", "C3-r8", "C3-r8-clean"]
files = {
 "metrics": os.path.join(CMP, "_dtrigger_metrics_out.txt"),
 "supp": os.path.join(CMP, "_dtrigger_supplement_out.txt"),
 "probe": os.path.join(CMP, "_dtrigger_probe_out.txt"),
}
print("--- independent table parse (13 zero-preempt criteria) ---")
for tag, p in files.items():
    lines = rd(p).split("\n")
    hits = {}
    for i, l in enumerate(lines, 1):
        if "|" not in l: continue
        f = [z.strip() for z in l.split("|")]
        if f[0] in thirteen and len(f) > 2 and f[1].isdigit():
            hits[f[0]] = (i, f)
    print("  %-8s rows for 13 criteria = %d" % (tag, len(hits)))
    for c in thirteen:
        if c in hits:
            i, f = hits[c]
            if tag == "metrics":
                print("    %-22s line %-3d within50=%s latP50=%s note=%s" % (c, i, f[9], f[6], f[11] if len(f)>11 else ""))
            elif tag == "supp":
                print("    %-22s line %-3d nTrig=%s >50=%s >=100=%s" % (c, i, f[1], f[6], f[8]))
            else:
                print("    %-22s line %-3d nTrig=%s >50=%s waitMed=%s" % (c, i, f[1], f[9], f[6]))
        else:
            print("    %-22s (absent)" % c)

print("--- §9.7 '高档 ≥100ms' support ---")
supp = rd(files["supp"]).split("\n")
all100, some100, none100 = [], [], []
for c in thirteen:
    found = False
    for l in supp:
        if "|" not in l: continue
        f = [z.strip() for z in l.split("|")]
        if f[0] == c and len(f) >= 12 and f[1].isdigit():
            found = True
            n, g100 = int(f[1]), int(f[8])
            (all100 if g100 == n else some100 if g100 > 0 else none100).append(c)
            break
    if not found:
        none100.append(c + "(no-row)")
print("  all >=100 (every trigger):", all100)
print("  only some >=100:", some100)
print("  none/no row:", none100)
named7 = ["C2-P95x3", "C2-P99x3", "C3-r4", "C3-r4-clean", "C3-r8", "C3-r8-clean", "C3-r12"]
print("  CRITERIA_COMPARE.md:338 named 7 =", named7)
print("  named7 present in all100 list =", [c for c in named7 if c in all100])
