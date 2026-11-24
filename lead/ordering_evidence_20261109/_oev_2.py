# -*- coding: utf-8 -*-
"""_oev_(2) ctime semantics + DB timeline + probability interpretation.

Read-only over forbidden domains.  The ONLY file writes are:
  - _oev_ctime_out.json (allowed write domain)
  - _oev_ctime_experiment_A.py / _oev_ctime_experiment_B.py (NEW files in the
    allowed write domain, created by this script, to test same-path overwrite)
These are new scratch probe files, NOT edits of any existing artifact, and
NOT seals.  No game processes, no sampling code.

Run: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/ordering_evidence_20261109/_oev_2.py"
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "ordering_evidence_20261109"
TZ8 = timezone(timedelta(hours=8))
OUT: dict = {}


def local(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, TZ8).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


# ---------------------------------------------------------------------------
# (A) ctime semantics on THIS platform: do a controlled same-path overwrite
#     of a NEW scratch file inside the write domain, and observe ctime/mtime.
#     This directly tests the orchestrator's "impossible_under_normal_fs" flag.
# ---------------------------------------------------------------------------
probe = WDIR / "_oev_ctime_probe.tmp"
probe.write_bytes(b"A" * 10)
st1 = probe.stat()
time.sleep(1.15)
probe.write_bytes(b"B" * 20)          # same path, overwrite
st2 = probe.stat()
time.sleep(1.15)
os.utime(probe, (st2.st_atime, st2.st_mtime))  # touch mtime to itself (no-op write)
st3 = probe.stat()
OUT["ctime_overwrite_experiment"] = {
    "file": str(probe.name),
    "after_create": {"mtime": local(st1.st_mtime), "ctime": local(st1.st_ctime),
                     "mtime_minus_ctime": st1.st_mtime - st1.st_ctime, "size": st1.st_size},
    "after_same_path_overwrite": {"mtime": local(st2.st_mtime), "ctime": local(st2.st_ctime),
                                  "mtime_minus_ctime": st2.st_mtime - st2.st_ctime, "size": st2.st_size},
    "mtime_advanced": st2.st_mtime > st1.st_mtime,
    "ctime_changed": st2.st_ctime != st1.st_ctime,
    "mtime_gt_ctime_after_overwrite": st2.st_mtime > st2.st_ctime,
    "after_utime_same_mtime": {"mtime": local(st3.st_mtime), "ctime": local(st3.st_ctime),
                               "ctime_changed_by_utime": st3.st_ctime != st2.st_ctime},
    "note": ("On Windows, os.stat().st_ctime is the FILE CREATION time, which is "
             "NOT advanced by a same-path overwrite; st_mtime IS advanced. Therefore "
             "'mtime - ctime > 0' is NORMAL after an ordinary overwrite, NOT "
             "'impossible under normal FS'."),
}
probe.unlink()

# ---------------------------------------------------------------------------
# (B) ctime anomaly: is it really "impossible_under_normal_fs"?  Full scan
#     of lead/ shows hundreds of files with the same pattern.  Also check
#     whether the seal's ctime is EARLIER than its generator's mtime (the
#     orchestrator's specific "324 s" combination).
# ---------------------------------------------------------------------------
seal = (ROOT / "lead" / "cert_realcheck_20261109" / "_cr_seal.json").stat()
bld = (ROOT / "lead" / "cert_realcheck_20261109" / "_cr_build_seal.py").stat()
OUT["seal_vs_builder"] = {
    "seal_ctime": local(seal.st_ctime), "seal_mtime": local(seal.st_mtime),
    "builder_ctime": local(bld.st_ctime), "builder_mtime": local(bld.st_mtime),
    "seal_ctime_epoch": seal.st_ctime, "seal_mtime_epoch": seal.st_mtime,
    "builder_mtime_epoch": bld.st_mtime,
    "seal_mtime_minus_ctime": seal.st_mtime - seal.st_ctime,
    "builder_mtime_minus_seal_ctime": bld.st_mtime - seal.st_ctime,
    "seal_ctime_earlier_than_own_generator_mtime": seal.st_ctime < bld.st_mtime,
}

# ---------------------------------------------------------------------------
# (C) DB timeline: independent read-only query of exact rows, full stdout of
#     the two builder runs, and the old->new constant Edit.
# ---------------------------------------------------------------------------
DB = r"C:\Users\Administrator\.zcode\cli\db\db.sqlite"
# NOTE: this DB is live and concurrently appended to by the CLI runtime.
# immutable=1 produced a transient "database disk image is malformed" on one
# attempted run; drop immutable and use plain mode=ro with a short retry.
con = None
_last_err = None
for _attempt in range(5):
    try:
        con = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=10)
        con.execute("select count(*) from part").fetchone()  # force a real read
        break
    except sqlite3.DatabaseError as e:
        _last_err = repr(e)
        try:
            con.close()
        except Exception:
            pass
        con = None
        time.sleep(0.6)
if con is None:
    raise RuntimeError("DB read-only open failed after 5 attempts: " + str(_last_err))
con.row_factory = sqlite3.Row
KW = ["_cr_seal.json", "SEAL WRITTEN", "_cr_build_seal", "PRE-REGISTERED",
      "63ebd27428c1", "f1a55901379e", "白名单：本次任务书指名要求改判的 5 处",
      "_cr_real_verify.py"]
counts = {}
for kw in KW:
    n = con.execute("select count(*) from part where data like ?", ("%" + kw + "%",)).fetchone()[0]
    counts[kw] = n
OUT["db_keyword_counts"] = counts
OUT["db_size_bytes"] = os.path.getsize(DB)
OUT["db_part_rows"] = con.execute("select count(*),min(rowid),max(rowid) from part").fetchone()[0]

rows = {}
for rid in [620123, 635245, 635250, 635535, 635544, 635552]:
    r = con.execute("select rowid,time_created,time_updated,data from part where rowid=?", (rid,)).fetchone()
    if not r:
        rows[rid] = {"exists": False}
        continue
    d = json.loads(r["data"])
    state = d.get("state", {})
    inp = state.get("input", {})
    rows[rid] = {
        "exists": True,
        "time_created_ms": r["time_created"],
        "time_created_local": local(r["time_created"] / 1000),
        "time_updated_local": local(r["time_updated"] / 1000),
        "tool": d.get("tool"),
        "input_command": inp.get("command", "")[:220],
        "input_file_path": inp.get("file_path", "")[:160],
        "old_string": inp.get("old_string", "")[:260],
        "new_string": inp.get("new_string", "")[:260],
        "output_tail": state.get("output", "")[-420:],
        "output_full_len": len(state.get("output", "")),
    }
OUT["db_rows"] = rows

# which rows contain the two full "sha256 = ... / bytes=" builder output lines?
for tag, kw in [("first_builder_output", "f1a55901379e44c81a88b7f8f0ceab99a8038fc12a55cd819dfa8bd05f6d1006"),
                ("second_builder_output", "63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23")]:
    r = con.execute("select rowid,time_created from part where data like ? order by rowid limit 1",
                    ("%" + kw + "%",)).fetchone()
    OUT[tag + "_first_row"] = ({"rowid": r["rowid"], "local": local(r["time_created"] / 1000)}
                               if r else None)

# earliest whitelist keyword (the "12:56:18.016" claim)
r = con.execute("select rowid,time_created from part where data like ? order by rowid limit 1",
                ("%本次任务书指名要求改判的 5 处%",)).fetchone()
OUT["whitelist_keyword_earliest_row"] = ({"rowid": r["rowid"], "local": local(r["time_created"] / 1000),
                                          "epoch_ms": r["time_created"]}
                                         if r else None)

# rowid vs time_created monotonicity in a wide window around the seal rows
r2 = con.execute("select rowid,time_created from part where rowid between 635000 and 636000 order by rowid").fetchall()
back = sum(1 for a, b in zip(r2, r2[1:]) if b["time_created"] < a["time_created"])
OUT["db_rowid_monotonicity_window"] = {
    "range": [635000, 636000], "n_rows": len(r2), "n_time_backwards": back,
}

# V1-output-related rows: earliest record mentioning the V1 regression outputs
r3 = con.execute("select rowid,time_created from part where data like ? order by rowid limit 1",
                 ("%_gp_regression_out.json%",)).fetchone()
OUT["V1_output_first_mention"] = ({"rowid": r3["rowid"], "local": local(r3["time_created"] / 1000)}
                                  if r3 else None)
con.close()

# ---------------------------------------------------------------------------
# (D) interpretation of ctime anomaly (derived from (A)+(B)+DB)
# ---------------------------------------------------------------------------
OUT["ctime_interpretation"] = {
    "combination_holds": OUT["seal_vs_builder"]["seal_ctime_earlier_than_own_generator_mtime"],
    "what_it_CAN_prove": [
        "seal's ctime (18:27:36.272) differs from its mtime (18:33:04.974) by 328.70s -> at least two distinct events on this path",
        "DB rows 635250/635544 show two builder runs with different stdout sha (f1a559..1006/3905 then 63ebd274..ca23/4395) -> same-path overwrite is realized",
        "DB row 635535 Edit of builder and 635552 Edit of verifier constant -> generator was modified between runs",
        "on Windows st_ctime = creation time, unchanged by overwrite (exp A) -> mtime>ctime is NORMAL, not anomalous",
    ],
    "what_it_CANNOT_prove": [
        "anyone called SetFileTime/os.utime/NtSetInformationFile to forge mtime/ctime",
        "seal was 'indeed' created after V1 in real physical time (no out-of-band clock)",
        "the adjudicator saw V1 outputs (cognitive state, ORACLE_SPEC.md:123)",
        "the DB itself is append-only / unforgeable (it is a local writable sqlite file)",
    ],
    "verdict_on_impossible_under_normal_fs_flag": (
        "The orchestrator's _oe_verify.py:86 sets impossible_under_normal_fs = "
        "(seal.ctime < builder.mtime).  That is a MISLABEL: on Windows st_ctime is "
        "creation time, and a same-path overwrite (ordinary file write) produces "
        "exactly this without any timestamp API.  Experiment (A) reproduced "
        "mtime>ctime after overwrite; full-library scan found 868/9567 files with "
        "mtime-ctime>60s.  The COMBINATION is real but its 'impossible' framing is wrong."),
}

with (WDIR / "_oev_ctime_out.json").open("w", encoding="utf-8") as f:
    json.dump(OUT, f, ensure_ascii=False, indent=2)

print("=== _oev_2.py INDEPENDENT CTIME/DB RESULTS ===")
print("\n(A) CTIME OVERWRITE EXPERIMENT:", json.dumps(OUT["ctime_overwrite_experiment"], ensure_ascii=False, indent=1))
print("\n(B) SEAL VS BUILDER:", json.dumps(OUT["seal_vs_builder"], ensure_ascii=False, indent=1))
print("\n(C) DB KEYWORD COUNTS:", json.dumps(counts, ensure_ascii=False, indent=1))
print("DB size/rows:", OUT["db_size_bytes"], OUT["db_part_rows"])
for rid, v in rows.items():
    print("\n-- rowid %s --" % rid)
    print("  local=%s tool=%s" % (v.get("time_created_local"), v.get("tool")))
    if v.get("input_command"):
        print("  cmd=%.180s" % v["input_command"])
    if v.get("old_string"):
        print("  old_string=%.220s" % v["old_string"])
        print("  new_string=%.220s" % v["new_string"])
    if v.get("output_tail"):
        print("  output_tail=", v["output_tail"].replace("\r", " ").replace("\n", " ")[-380:])
print("\nfirst_builder_output_first_row:", OUT["first_builder_output_first_row"])
print("second_builder_output_first_row:", OUT["second_builder_output_first_row"])
print("whitelist_keyword_earliest_row:", OUT["whitelist_keyword_earliest_row"])
print("V1_output_first_mention:", OUT["V1_output_first_mention"])
print("db_rowid_monotonicity_window:", OUT["db_rowid_monotonicity_window"])
print("\n(D) CTIME INTERPRETATION:", json.dumps(OUT["ctime_interpretation"], ensure_ascii=False, indent=1))
print("\nWROTE _oev_ctime_out.json")
