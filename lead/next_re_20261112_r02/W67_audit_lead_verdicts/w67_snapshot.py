# -*- coding: utf-8 -*-
"""W67 audit: independent input snapshot (READ-ONLY on inputs).
Writes nothing outside stdout; caller redirects into W67 dir.
"""
import os, hashlib, datetime, sys

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02"
REVIEW = os.path.join(BASE, "REVIEW")

TARGETS = [
    "LEAD_VERIFY_W55B.md",
    "LEAD_VERIFY_W57.md",
    "LEAD_VERIFY_W58.md",
    "LEAD_VERIFY_W59.md",
    "LEAD_VERIFY_W63.md",
    "LEAD_VERIFY_W64B.md",
    "LEAD_VERIFY_W65.md",
    "LEAD_CHECK_menu_3slot.md",
    "LEAD_CHECK_gate_byte.md",
    "LEAD_TRIAGE_W52.md",
    "LEAD_RULING_D5_2_INPLACE_UNFREEZE.md",
    "LEAD_RULING_C_line_route_a_first.md",
]

def snap(path):
    st = os.stat(path)
    with open(path, "rb") as f:
        b = f.read()
    tz = datetime.datetime.now().astimezone().tzinfo
    mt = datetime.datetime.fromtimestamp(st.st_mtime, tz).isoformat(timespec="microseconds")
    nl = b.count(b"\n")
    # splitlines lines (counts a trailing non-newline line too)
    sl = len(b.splitlines())
    return {
        "size": st.st_size,
        "sha": hashlib.sha256(b).hexdigest(),
        "mtime": mt,
        "nl": nl,
        "sl": sl,
    }

print("=== W67 INPUT SNAPSHOT (independent recompute by ZCode) ===")
print("ts_now =", datetime.datetime.now().astimezone().isoformat(timespec="seconds"))
print()
print("--- 12 REVIEW signoffs ---")
for t in TARGETS:
    p = os.path.join(REVIEW, t)
    if not os.path.isfile(p):
        print(f"{t} | ABSENT")
        continue
    s = snap(p)
    print(f"{t} | bytes={s['size']} | sha256={s['sha']} | sha12={s['sha'][:12]} | mtime={s['mtime']} | lines_splitlines={s['sl']} | nl_count={s['nl']}")

print()
print("--- RUNLOG.md / HANDOFF.md (whole-file snapshot ONLY; full text NOT read) ---")
for t in ["RUNLOG.md", "HANDOFF.md"]:
    p = os.path.join(BASE, t)
    if not os.path.isfile(p):
        print(f"{t} | ABSENT")
        continue
    s = snap(p)
    print(f"{t} | bytes={s['size']} | sha256={s['sha']} | sha12={s['sha'][:12]} | mtime={s['mtime']} | lines_splitlines={s['sl']} | nl_count={s['nl']}")

print()
print("--- .game_instance.lock existence check (READ-ONLY, no touch) ---")
hits = []
for root in [BASE, r"D:\Project\ra2-campaign-forge"]:
    p = os.path.join(root, ".game_instance.lock")
    if os.path.exists(p):
        hits.append(p)
if hits:
    for h in hits:
        print("LOCK_PRESENT:", h)
else:
    print("LOCK_ABSENT at BASE and repo root")

print()
print("=== END SNAPSHOT ===")
