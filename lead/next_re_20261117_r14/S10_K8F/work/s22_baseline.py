"""S22 baseline recompute for K8F; writes EVIDENCE/S22_BASELINE_K8.txt."""
from pathlib import Path
import csv, hashlib, datetime, re

ROOT = Path(r"D:\Project\ra2-campaign-forge")
CARD = ROOT / "lead/next_re_20261117_r14/S10_K8F"
COV = ROOT / "lead/next_re_20261117_r14/COVERAGE/coverage.tsv"
ATL = ROOT / "lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv"
EXE = ROOT / "ra2youli/gamemd.exe"
OUT = CARD / "EVIDENCE/S22_BASELINE_K8.txt"
DELTA = CARD / "coverage_delta.tsv"

def rows(p):
    with p.open("r", encoding="utf-8", newline="") as f:
        yield from csv.DictReader(f, delimiter="\t")

def norm(x):
    return x.strip().lower()

def named(r):
    n = r.get("name", "").strip()
    return bool(n) and not n.startswith("sub_") and "::sub_" not in n and re.search(r"::(?:v?slot)\d+$", n) is None

def proved(r):
    return r.get("grade", "").strip().upper() == "[已证]"

cov_all = list(rows(COV))
cov = [r for r in cov_all if r.get("subsystem", "").strip().upper() == "S22"]
atl = {norm(r["entry"]) for r in rows(ATL)}
ci = [r for r in cov if norm(r["entry"]) in atl]
outside = [r for r in cov if norm(r["entry"]) not in atl]
base_proved = sum(map(proved, ci))
base_named = sum(named(r) for r in ci)

delta_rows = []
with DELTA.open("r", encoding="utf-8") as f:
    for line in f:
        fld = line.rstrip("\n").split("\t")
        if len(fld) == 9 and fld[1] == "S22":
            delta_rows.append({
                "entry": fld[0], "name": fld[2], "grade": fld[4],
                "semantics": fld[3]
            })
base_by = {norm(r["entry"]): r for r in cov_all}
new_proved = 0
new_named = 0
notes = []
for d in delta_rows:
    e = norm(d["entry"])
    b = base_by.get(e)
    in_at = e in atl
    delta_p = d["grade"].strip().upper() == "[已证]"
    gain_p = int(in_at and delta_p and not proved(b))
    gain_n = int(in_at and named(d) and not named(b))
    new_proved += gain_p
    new_named += gain_n
    notes.append(
        f"  {d['entry']} in_atlas={int(in_at)} base_grade={'PROVED' if proved(b) else 'NOT_PROVED'} "
        f"base_named={int(named(b))} delta_named={int(named(d))} "
        f"proved_gain={gain_p} named_gain={gain_n}"
    )

sim_proved = base_proved + new_proved
sim_named = base_named + new_named
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
stamp = lambda p: datetime.datetime.fromtimestamp(p.stat().st_mtime, datetime.timezone(datetime.timedelta(hours=8))).isoformat()
L = [
    "S22_BASELINE_K8 RECOMPUTE",
    "SAMPLE_TIME_ISO=" + now,
    "SCRIPT=work/s22_baseline.py (relative to S10_K8F)",
    "TOOLS=Python3.12.10 csv/hashlib; disassembly cross-check work/reverify_semantics_k8f.py with capstone5.0.7(skipdata=True)+pefile2024.8.26",
    "TARGET=" + str(EXE),
    "EXE_SHA256=" + hashlib.sha256(EXE.read_bytes()).hexdigest().upper(),
    "COVERAGE=" + str(COV),
    "COVERAGE_SHA256=" + hashlib.sha256(COV.read_bytes()).hexdigest().upper(),
    "COVERAGE_MTIME_ISO=" + stamp(COV),
    "ATLAS=" + str(ATL),
    "ATLAS_SHA256=" + hashlib.sha256(ATL.read_bytes()).hexdigest().upper(),
    "ATLAS_MTIME_ISO=" + stamp(ATL),
    "DELTA=" + str(DELTA),
    "S22_ROWS_TOTAL=" + str(len(cov)),
    "S22_ROWS_IN_ATLAS=" + str(len(ci)),
    "ATLAS_N=" + str(len(ci)),
    "S22_ROWS_OUTSIDE_ATLAS=" + str(len(outside)),
    "PROVED=" + str(base_proved),
    "PROVED_PCT=" + f"{100.0*base_proved/len(ci):.4f}",
    "NAMED=" + str(base_named),
    "DELTA_S22_ROWS=" + str(len(delta_rows)),
    "SIM_PROVED_GAIN=" + str(new_proved),
    "SIM_NAMED_GAIN=" + str(new_named),
    "SIM_PROVED=" + str(sim_proved),
    "SIM_PROVED_PCT=" + f"{100.0*sim_proved/len(ci):.4f}",
    "SIM_NAMED=" + str(sim_named),
    "RULE=Rows outside the atlas are excluded from the atlas denominator and from proved/named gains, the same口径 used when S10 excludes 005B3740.",
    "EXCLUDED_ROW=006B6FA0 not in atlas; it does not add to 55 or 6.",
    "DELTA_ROW_DETAIL:",
    *notes,
]
OUT.write_text("\n".join(L) + "\n", "utf-8", newline="\n")
assert (len(ci), base_proved, base_named, sim_proved, sim_named) == (4851, 54, 4, 55, 6)
print("WROTE", OUT, "lines", len(L))
