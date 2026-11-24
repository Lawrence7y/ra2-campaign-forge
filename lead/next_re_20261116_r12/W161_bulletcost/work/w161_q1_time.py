"""W161 Q1: translate instruction/memory counts to a per-bullet execution time upper bound.
Reads Q1_closure.json. Uses explicit IPC assumptions (cycles per instruction, CPI).
Reports at 1.0 / 2.0 / 3.0 GHz. No p-values; a plain interval of assumptions.
"""
import json, os
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W161_bulletcost\EVIDENCE"
d = json.load(open(os.path.join(OUT, "Q1_closure.json"), encoding="utf-8"))
root_i = d["channels"]["A_ghidra"]["root"]["n_insn"]
root_m = d["channels"]["A_ghidra"]["root"]["n_mem"]

scenarios = []
scenarios.append(("AI only (root)", root_i, root_m))
for ch in ("A_ghidra", "B_byte"):
    L = d["channels"][ch]["layers"]
    cum_i = root_i + sum(x["n_insn"] for x in L)
    cum_m = root_m + sum(x["n_mem"] for x in L)
    scenarios.append(("AI + full closure d1-4 (%s)" % ch, cum_i, cum_m))
    d1_i = root_i + L[0]["n_insn"]
    d1_m = root_m + L[0]["n_mem"]
    scenarios.append(("AI + depth1 only (%s)" % ch, d1_i, d1_m))

FREQS = [1.0e9, 2.0e9, 3.0e9]
CPIS = [1.0, 2.0, 4.0]  # 4.0 deliberately pessimistic upper bound
print("=== per-bullet pure-execution time upper bound (microseconds) ===")
print("assumptions: time = instructions * CPI / freq ; CPI 1/2/4 ; freq 1/2/3 GHz")
for name, ni, nm in scenarios:
    print("\n%s : instructions=%d mem-ref-insns=%d" % (name, ni, nm))
    for f in FREQS:
        row = []
        for cpi in CPIS:
            us = ni * cpi / f * 1e6
            row.append("CPI%.0f=%.2fus" % (cpi, us))
        print("  %.1f GHz  %s" % (f/1e9, "  ".join(row)))

print("\n=== memory-access-only upper bound (all mem-ref insns * cycles each) ===")
for name, ni, nm in scenarios:
    for cpi_mem in (5, 30, 100):
        us = nm * cpi_mem / 1e9 * 1e6
        print("  %s mem=%d * %dcyc @1GHz = %.2fus" % (name, nm, cpi_mem, us))

print("\n=== ratio: 650us / time (how many times smaller than the observed 0.65ms) ===")
for name, ni, nm in scenarios:
    us = ni * 4.0 / 1e9 * 1e6  # most generous upper bound: CPI=4 @1GHz
    print("  %s : 650/%.2f = %.1fx" % (name, us, 650.0/us))
