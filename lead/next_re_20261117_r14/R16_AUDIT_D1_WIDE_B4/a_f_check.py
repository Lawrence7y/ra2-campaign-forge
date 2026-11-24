# -*- coding: utf-8 -*-
"""AUDIT B4 — 项 A（原文保全）与项 F（清单一致性）独立复核。
只读：coverage 基线(pin)、delta.tsv、fields.tsv、sieve_all.tsv、B1/B2/B3 fields.tsv。
"""
import io, json, os, sys, hashlib

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUT = os.path.join(R14, "R16_AUDIT_D1_WIDE_B4")
B4 = os.path.join(R14, "R16_D1_WIDE_B4")

def read_lines(p):
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        return f.read().split("\n")

def read_bytes(p):
    with open(p, "rb") as f:
        return f.read()

def load_tsv(p):
    raw = read_bytes(p).decode("utf-8")
    # keep exact cells; strip trailing newline
    lines = raw.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    hdr = lines[0].split("\t")
    rows = []
    for ln in lines[1:]:
        rows.append(ln.split("\t"))
    return hdr, rows, raw

rep = {}

# ---------- 基线候选 ----------
cov = os.path.join(R14, "COVERAGE", "coverage.tsv")
pin_b1 = os.path.join(R14, "R16_MERGE_D1_WIDE_B1", "_pin_coverage.tsv")
pin_b2 = os.path.join(R14, "R16_MERGE_D1_WIDE_B2", "_pin_coverage.tsv")
pin_b3 = os.path.join(R14, "R16_MERGE_D1_WIDE_B3", "_pin_coverage.tsv")

def sha(p):
    return hashlib.sha256(read_bytes(p)).hexdigest().upper()

rep["cov_state"] = {
    "current": {"path": cov, "bytes": os.path.getsize(cov), "sha": sha(cov)},
    "pin_b1": {"bytes": os.path.getsize(pin_b1), "sha": sha(pin_b1)},
    "pin_b2": {"bytes": os.path.getsize(pin_b2), "sha": sha(pin_b2)},
    "pin_b3": {"bytes": os.path.getsize(pin_b3), "sha": sha(pin_b3)},
    "executor_claimed": {"bytes": 4097787,
                          "sha": "412ED7E36BC1AD4907763FEBB3A68D5FDABB3F0D2C999800444B57098B1AB2E1"},
}
# 执行器所读状态 == pin_b1 ?
rep["executor_baseline_is_pin_b1"] = (
    os.path.getsize(pin_b1) == 4097787 and sha(pin_b1) == rep["cov_state"]["executor_claimed"]["sha"])

# ---------- delta / fields ----------
dh, drows, draw = load_tsv(os.path.join(B4, "delta.tsv"))
fh, frows, fraw = load_tsv(os.path.join(B4, "fields.tsv"))
rep["delta"] = {"header": dh, "n_rows": len(drows), "cols": sorted({len(r) for r in drows})}
rep["fields"] = {"header": fh, "n_rows": len(frows), "cols": sorted({len(r) for r in frows})}
delta_entries = [r[0] for r in drows]
fields_entries = [r[0] for r in frows]
rep["entries"] = {"delta": delta_entries, "fields": fields_entries,
                   "same_order": delta_entries == fields_entries,
                   "delta_unique": len(set(delta_entries)) == len(delta_entries),
                   "fields_unique": len(set(fields_entries)) == len(fields_entries)}

# ---------- A: 原文保全 ----------
base_map = {}
for p in (pin_b1, cov):
    h, rows, _ = load_tsv(p)
    base_map[p] = {r[0]: r for r in rows}

def a_check(baseline_path):
    base = base_map[baseline_path]
    out = {}
    for r in drows:
        e = r[0]
        b = base.get(e)
        if b is None:
            out[e] = {"error": "baseline_missing"}
            continue
        c4b, c4d = b[3], r[3]
        rec = {
            "n_cols_base": len(b), "n_cols_delta": len(r),
            "col4_strict_prefix": c4d.startswith(c4b),
            "col4_added_len": len(c4d) - len(c4b),
            "col4_base_has_ring4": ("④" in c4b),
            "grade_base": b[4], "grade_delta": r[4], "grade_same": b[4] == r[4],
            "other_cols_identical": all(b[i] == r[i] for i in (0, 1, 2, 5, 6, 7)),
            "which_cols_differ": [i for i in range(8) if b[i] != r[i]],
        }
        out[e] = rec
    return out

rep["A_vs_pin_b1"] = a_check(pin_b1)
rep["A_vs_current"] = a_check(cov)

# 追加：现行 coverage 的其余列/前 4 列与 pin 基线一致（说明 B4 未动过该文件的行）
cur = base_map[cov]; base = base_map[pin_b1]
rep["cov_untouched_for_B4_rows"] = {
    e: (cur[e] == base[e]) for e in delta_entries if e in cur and e in base}

# ---------- F: 清单一致性 ----------
sh, srows, _ = load_tsv(os.path.join(R14, "R16_SIEVE_D1_WIDE", "sieve_all.tsv"))
sieve_entries = [r[0] for r in srows]
has4 = {r[0]: r[6] for r in srows}
pending = [e for e in sieve_entries if has4[e] == "否"]
done = [e for e in sieve_entries if has4[e] != "否"]

def batch_entries(name):
    h, rows, _ = load_tsv(os.path.join(R14, name, "fields.tsv"))
    return [r[0] for r in rows]

b1 = batch_entries("R16_D1_WIDE_B1")
b2 = batch_entries("R16_D1_WIDE_B2")
b3 = batch_entries("R16_D1_WIDE_B3")
residual = [e for e in pending if e not in set(b1) | set(b2) | set(b3)]
rep["F"] = {
    "sieve_rows": len(srows), "sieve_unique": len(set(sieve_entries)),
    "has_ring4_yes": len(done), "has_ring4_no": len(pending),
    "b1_n": len(b1), "b2_n": len(b2), "b3_n": len(b3),
    "b1_b2_b3_overlap": sorted(set(b1) & set(b2)) + sorted(set(b1) & set(b3)) + sorted(set(b2) & set(b3)),
    "b1_in_pending": all(e in pending for e in b1),
    "b2_in_pending": all(e in pending for e in b2),
    "b3_in_pending": all(e in pending for e in b3),
    "residual_after_sub": residual,
    "residual_n": len(residual),
    "delta_equals_residual_set": set(residual) == set(delta_entries),
    "delta_minus_residual": sorted(set(delta_entries) - set(residual)),
    "residual_minus_delta": sorted(set(residual) - set(delta_entries)),
    "delta_has_005F4B10": "005F4B10" in delta_entries,
    "005F4B10_in_sieve": "005F4B10" in sieve_entries,
    "005F4B10_in_b3": "005F4B10" in b3,
    "005F4B10_has4": has4.get("005F4B10"),
}
# 若把 005F4B10 也剔掉：residual 是否就空？
rep["F"]["residual_without_005F4B10"] = [e for e in residual if e != "005F4B10"]

with io.open(os.path.join(OUT, "a_f_result.json"), "w", encoding="utf-8") as f:
    json.dump(rep, f, ensure_ascii=False, indent=1)

# 摘要
print("== cov state ==")
for k, v in rep["cov_state"].items():
    print(" ", k, v)
print("executor baseline == pin_b1:", rep["executor_baseline_is_pin_b1"])
print("\n== delta/fields ==", rep["delta"], rep["fields"], rep["entries"]["same_order"])
print("\n== A (vs pin_b1) ==")
bad = 0
for e, r in rep["A_vs_pin_b1"].items():
    ok = r.get("col4_strict_prefix") and r.get("grade_same") and r.get("other_cols_identical")
    if not ok:
        bad += 1
        print("  FAIL", e, r)
print("  A fail rows:", bad, "/", len(rep["A_vs_pin_b1"]))
print("  col4 added len:", {e: r["col4_added_len"] for e, r in rep["A_vs_pin_b1"].items()})
print("\n== A (vs current) ==")
bad2 = [e for e, r in rep["A_vs_current"].items()
        if not (r.get("col4_strict_prefix") and r.get("grade_same") and r.get("other_cols_identical"))]
print("  A fail rows vs current:", bad2)
print("  cov_untouched_for_B4_rows all True:", all(rep["cov_untouched_for_B4_rows"].values()))
print("\n== F ==")
for k, v in rep["F"].items():
    print(" ", k, "=", v)
