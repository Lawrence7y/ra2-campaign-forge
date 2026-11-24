# _efv_diff45.py — 45 行逐行 before/after 对比 + 全锚点迁移矩阵（自己的两次实跑产物）
import io, json

BASE = r"D:/Project/ra2-campaign-forge/lead/eqdecl_fix_20261110"
a = json.load(io.open(BASE + r"/_efv_full_orig.json", encoding="utf-8"))
b = json.load(io.open(BASE + r"/_efv_full_fixed.json", encoding="utf-8"))

def key(r): return (r["file"], r["line"])
amap = {key(r): r for r in a["all_records"]}
bmap = {key(r): r for r in b["all_records"]}

# ---- 45 行清单对比 ----
rows45 = []
for ra in a["listed_45"]["rows"]:
    fl = ra["file:line"]
    rb = next(x for x in b["listed_45"]["rows"] if x["file:line"] == fl)
    changed = (ra["verdict"], ra["failure_type"], ra["skip_reason"]) != \
              (rb["verdict"], rb["failure_type"], rb["skip_reason"])
    rows45.append({
        "file:line": fl,
        "before": f'{ra["verdict"]}/{ra["failure_type"] or "-"}/{ra["skip_reason"] or "-"}',
        "after": f'{rb["verdict"]}/{rb["failure_type"] or "-"}/{rb["skip_reason"] or "-"}',
        "changed": changed,
    })
changed45 = [r for r in rows45 if r["changed"]]
fail_to_fail = [r for r in rows45 if r["before"].startswith("FAIL") and r["after"].startswith("FAIL")]
new_fail_45 = [r for r in rows45 if not r["before"].startswith("FAIL") and r["after"].startswith("FAIL")]
print(json.dumps({
    "listed45": {"n": len(rows45), "changed": len(changed45),
                 "changed_rows": changed45,
                 "beforeFAIL_afterFAIL": len(fail_to_fail),
                 "new_FAIL_in_45": len(new_fail_45)},
}, ensure_ascii=False, indent=1))

# ---- 全锚点迁移矩阵 ----
trans = {}
new_fails, lost_fails = [], []
keys = sorted(set(amap) | set(bmap))
for k in keys:
    ra, rb = amap.get(k), bmap.get(k)
    va = f'{ra["verdict"]}/{ra.get("failure_type") or "-"}' if ra else "ABSENT"
    vb = f'{rb["verdict"]}/{rb.get("failure_type") or "-"}' if rb else "ABSENT"
    t = (va, vb)
    trans[t] = trans.get(t, 0) + 1
    if rb and rb["verdict"] == "FAIL" and (not ra or ra["verdict"] != "FAIL"):
        new_fails.append({"file:line": f"{k[0]}:{k[1]}", "before": va})
    if ra and ra["verdict"] == "FAIL" and (not rb or rb["verdict"] != "FAIL"):
        lost_fails.append({"file:line": f"{k[0]}:{k[1]}", "before": va, "after": vb})
print("n_anchor_keys:", len(keys))
print("transitions:")
for t, n in sorted(trans.items(), key=lambda x: -x[1]):
    print(f"  {t[0]:24s} -> {t[1]:24s} {n}")
print("new_FAIL_total:", len(new_fails), json.dumps(new_fails, ensure_ascii=False))
print("FAIL_resolved_total:", len(lost_fails))
for x in lost_fails:
    print("  resolved:", json.dumps(x, ensure_ascii=False))
