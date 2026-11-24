# -*- coding: utf-8 -*-
"""Parse the surveyor's 01_exit_census.md section-2 table and compare each row to independently read disk data."""
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

D = Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
DOC = Path("D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261105/EXIT_CENSUS_77a0d667/01_exit_census.md")
lines = DOC.read_bytes().decode("utf-8-sig").splitlines()

# section 2 table: rows between the header line starting '| 目录 | final_exit' and the '### 2.1' heading
start = next(i for i, ln in enumerate(lines) if ln.startswith("| 目录 | final_exit"))
end = next(i for i, ln in enumerate(lines) if ln.startswith("### 2.1"))
table = []
for ln in lines[start + 2:end]:
    if ln.startswith("| `archive_"):
        cells = [c.strip() for c in ln.split("|")[1:-1]]
        table.append(cells)
print("PARSED TABLE ROWS =", len(table))
print("HEADER CELLS:", [c.strip() for c in lines[start].split("|")[1:-1]])

# independent disk truth
dirs = sorted([p for p in D.iterdir() if p.is_dir() and p.name.startswith("archive_T")], key=lambda p: p.name)
truth = {}
for p in dirs:
    rl = p / "qc151_run_log.json"
    if rl.exists():
        o = json.loads(rl.read_bytes().decode("utf-8-sig"))
        fe = str(o["final_exit"])
    else:
        fe = "缺"
    et = p / "error.txt"
    et_type = None
    et_where = None
    et_repr = None
    if et.exists() and et.stat().st_size > 0:
        for ln in et.read_bytes().decode("utf-8", errors="replace").splitlines():
            s = ln.strip()
            if s.lower().startswith("type"):
                et_type = s.split("=", 1)[1].strip()
            elif s.lower().startswith("where"):
                et_where = s.split("=", 1)[1].strip()
            elif s.lower().startswith("repr"):
                et_repr = s.split("=", 1)[1].strip()
    eps = sorted(q for q in p.rglob("except_post_*.txt") if q.is_file())
    hashes = set(hashlib.sha256(q.read_bytes()).hexdigest() for q in eps)
    truth[p.name] = dict(fe=fe, et_type=et_type, et_where=et_where, et_repr=et_repr,
                         ep_n=len(eps), ep_hashes=hashes)

print("\n" + "=" * 90)
print("ROW-BY-ROW COMPARISON (report cell vs independent disk)")
mismatch = []
seen = []
for cells in table:
    name = cells[0].strip("`")
    seen.append(name)
    fe_rep = cells[1]
    err_cell = cells[3]
    repr_cell = cells[4]
    exc_cell = cells[6]
    if name not in truth:
        mismatch.append("%s : NOT A REAL DIRECTORY" % name)
        continue
    t = truth[name]
    # final_exit
    if fe_rep != t["fe"]:
        mismatch.append("%s final_exit: report=%r disk=%r" % (name, fe_rep, t["fe"]))
    # errorType
    if t["et_type"]:
        if t["et_type"] not in err_cell:
            mismatch.append("%s errorType: report=%r disk type=%r" % (name, err_cell, t["et_type"]))
    else:
        if err_cell != "无 @ —":
            mismatch.append("%s errorType: report=%r but disk has NO error.txt" % (name, err_cell))
    # repr
    if t["et_repr"]:
        if t["et_repr"] not in repr_cell:
            mismatch.append("%s repr: report=%r disk repr=%r" % (name, repr_cell, t["et_repr"]))
    elif repr_cell != "无":
        mismatch.append("%s repr: report=%r but disk has NO repr" % (name, repr_cell))
    # except count + hash
    m = re.search(r"(\d+)\s*[×份]", exc_cell)
    n_rep = int(m.group(1)) if m else None
    if n_rep != t["ep_n"]:
        mismatch.append("%s except count: report=%r disk=%r (cell=%r)" % (name, n_rep, t["ep_n"], exc_cell))
    if t["ep_hashes"] and "6694b75e46a6e773" not in exc_cell and t["ep_n"] > 0:
        mismatch.append("%s except hash prefix missing from report cell %r" % (name, exc_cell))
    print("  %-22s fe=%-3r errtype=%-14r repr=%-60r except_n=%-2s OK" % (name, fe_rep,
          t["et_type"], t["et_repr"], n_rep))

print("\n" + "=" * 90)
print("ROW SET: report has", len(seen), "dirs; disk has", len(truth), "dirs")
print("  missing from report:", sorted(set(truth) - set(seen)))
print("  extra in report   :", sorted(set(seen) - set(truth)))
print("  duplicate rows    :", [k for k, v in Counter(seen).items() if v > 1])
print("\nMISMATCH COUNT =", len(mismatch))
for m in mismatch:
    print("  !!", m)

print("\n" + "=" * 90)
print("REPORT PROSE NUMBERS ABOUT except_post COVERAGE")
for i, ln in enumerate(lines, 1):
    if re.search(r"(13|21|18|19) 个 (archive|目录)|13 个 archive|21 个目录|3 趟成功趟", ln):
        print("  L%-4d %s" % (i, ln.strip()[:300]))
print("\nACTUAL: dirs with >=1 except_post =", sum(1 for v in truth.values() if v["ep_n"] > 0),
      "; dirs with 0 =", sum(1 for v in truth.values() if v["ep_n"] == 0),
      "; total files =", sum(v["ep_n"] for v in truth.values()))
print("ACTUAL: final_exit=0 dirs WITH >=1 except_post =",
      [k for k, v in truth.items() if v["fe"] == "0" and v["ep_n"] > 0])
print("         count =", sum(1 for v in truth.values() if v["fe"] == "0" and v["ep_n"] > 0))
print("ACTUAL: final_exit=0 dirs with 0 except_post =",
      [k for k, v in truth.items() if v["fe"] == "0" and v["ep_n"] == 0])
print("DONE")
