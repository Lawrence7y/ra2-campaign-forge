"""W161 Q1: static cost model of BulletClass::AI closure, depth 1-4.

Two channels:
  A) Ghidra call edges (calledges.raw.log) - caller->callee.
  B) Byte channel: full .text linear sweep with skipdata=True, call sites -> targets;
     sites grouped into callers by nearest preceding function entry (uses entry, not size).
     Callee targets are taken from raw bytes => robust to callees outside atlas.

For each layer report: function count, cumulative instruction count (capstone disasm),
memory-reference instruction count. Then a time upper bound at 1/2/3 GHz with IPC bounds.
"""
import sys, os, json, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w161_lib as w

ROOT = r"D:\Project\ra2-campaign-forge"
OUT = os.path.join(ROOT, r"lead\next_re_20261116_r12\W161_bulletcost\EVIDENCE")
ROOT_ENTRY = 0x4666E0

def main():
    b = w.Bin()
    rows, hdr = w.load_atlas()
    atlas = {va: rec for va, rec in rows}
    entries = [va for va, _ in rows]
    by_caller, edges = w.load_calledges()

    # ---- full-section byte sweep (independent channel) ----
    calls, jmps, sweep_stats = w.sweep_full_text(b)
    print("SWEEP_STATS", json.dumps(sweep_stats))
    def caller_of(site):
        i = bisect.bisect_right(entries, site) - 1
        return entries[i] if i >= 0 else None
    byte_by_caller = {}
    for tgt, sites in calls.items():
        for s in sites:
            c = caller_of(s)
            if c is not None:
                byte_by_caller.setdefault(c, set()).add(tgt)

    # ---- per-function insn/mem stats cache ----
    def fn_stats(va):
        rec = atlas.get(va)
        if rec is None:
            return (0, 0, "NOT_IN_ATLAS")
        size = int(rec["size"], 10)  # DECIMAL per §863
        if size <= 0 or size > 0x20000:
            return (0, 0, "BAD_SIZE")
        ni, nm, nc, nbe, origins, insns, nsk = w.insn_stats(b, va, size)
        return (ni, nm, "ok")

    cache = {}
    def get_stats(va):
        if va not in cache:
            cache[va] = fn_stats(va)
        return cache[va]

    # ---- BFS by layer, channel A and B ----
    results = {}
    for chname, graph in (("A_ghidra", by_caller), ("B_byte", byte_by_caller)):
        frontier = {ROOT_ENTRY}
        visited = {ROOT_ENTRY}
        layers = []
        for depth in range(1, 5):
            nxt = set()
            for f in frontier:
                for c in graph.get(f, ()):
                    if c not in visited:
                        nxt.add(c)
            nxt.discard(ROOT_ENTRY)
            for v in nxt:
                visited.add(v)
            frontier = nxt
            total_insn = 0; total_mem = 0; in_atlas = 0; not_atlas = 0
            detail = []
            for v in sorted(nxt):
                ni, nm, st = get_stats(v)
                total_insn += ni; total_mem += nm
                if st == "ok": in_atlas += 1
                else: not_atlas += 1
                detail.append((v, ni, nm, st))
            layers.append(dict(depth=depth, n_funcs=len(nxt), n_insn=total_insn,
                               n_mem=total_mem, in_atlas=in_atlas, not_atlas=not_atlas,
                               detail=detail))
        rni, rnm, rst = get_stats(ROOT_ENTRY)
        results[chname] = dict(root=dict(va=ROOT_ENTRY, n_insn=rni, n_mem=rnm, status=rst),
                               layers=layers, visited_total=len(visited))

    report = dict(sweep_stats=sweep_stats, channels=results,
                  root_direct_callees_A=sorted(by_caller.get(ROOT_ENTRY, ())),
                  root_direct_callees_B=sorted(byte_by_caller.get(ROOT_ENTRY, ())))
    with open(os.path.join(OUT, "Q1_closure.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)

    print("ROOT", results["A_ghidra"]["root"])
    for ch in ("A_ghidra", "B_byte"):
        print("==", ch, "visited_total", results[ch]["visited_total"])
        for L in results[ch]["layers"]:
            print("  depth=%d funcs=%d insn=%d mem=%d in_atlas=%d not_atlas=%d" %
                  (L["depth"], L["n_funcs"], L["n_insn"], L["n_mem"], L["in_atlas"], L["not_atlas"]))
    print("root callees A count", len(report["root_direct_callees_A"]),
          "B count", len(report["root_direct_callees_B"]))
    print("root callees A:", [hex(x) for x in report["root_direct_callees_A"]])
    print("root callees B-only:", [hex(x) for x in set(report["root_direct_callees_B"]) - set(report["root_direct_callees_A"])])
    print("root callees A-only:", [hex(x) for x in set(report["root_direct_callees_A"]) - set(report["root_direct_callees_B"])])

if __name__ == "__main__":
    main()
