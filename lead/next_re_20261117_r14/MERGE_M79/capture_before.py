# -*- coding: utf-8 -*-
"""Capture BEFORE state (mtime float+ISO, bytes, sha256) for coverage.tsv and PANEL.md."""
import os, sys, json, hashlib, datetime
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
MERGE = os.path.join(ROOT, "MERGE_M79")
FILES = {
    "coverage.tsv": os.path.join(ROOT, "COVERAGE", "coverage.tsv"),
    "PANEL.md": os.path.join(ROOT, "COVERAGE", "PANEL.md"),
}

state = {}
for name, path in FILES.items():
    st = os.stat(path)
    raw = open(path, "rb").read()
    iso = datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    state[name] = {
        "path": os.path.relpath(path, PROJ),
        "mtime_float": st.st_mtime,
        "mtime_iso": iso,
        "bytes": st.st_size,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    print(f"{name}: mtime={st.st_mtime!r} ({iso}) bytes={st.st_size} sha256={state[name]['sha256']}")

with open(os.path.join(MERGE, "_before_state.json"), "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
print("saved _before_state.json")
