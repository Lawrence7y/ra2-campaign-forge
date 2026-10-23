"""R-040: mutation-test the shared-contract gate.

Discipline #44: every byte-pinnable assertion must go red under a targeted
mutation.  Mutations apply to an in-memory copy via R040_MUTATE; the exe on
disk is never touched.

C1 (whole-image sha256) trips on EVERY mutation -- excluded from the red sets
and expected sets, same convention as P1 in the other mutate_*_gate.py files.

C2 and C6 are labelled STRUCTURAL in the gate itself (they derive from
symbols.json and a partition identity, not from exe bytes), so they are
expected to stay green under every mutation; a mutation that DID move them
would mean the labels are wrong -- the exact-set scoring would catch that.

IMPORTANT: the expected red sets below are MEASURED, not predicted.  Drafting
them from memory produced two wrong guesses in this very session (a HouseClass
callee address and a fifth case on 0x473AE0 that survived, G-55's pattern), so
the run order was: gate first, per-mutation red sets second, expectations last.
This file documents the measured values.

Run: python re_atlas/tools/mutate_r040_gate.py
"""

import os
import subprocess
import sys

GATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "r040_shared_contract.py")

CASES = [
    # Stub content: 0x4C9150 `33 c0 c3` -> first byte 0x90.  The 9 bases still
    # POINT at the stub (pointer identity holds, stub_hits stays 9), so only the
    # content conjunct of C5 can fail.  Measured red = {C5}.
    ("abstract stub 0x4C9150 first byte corrupted", "0x4C9150=0x90",
     {"C5"}),

    # TEventClass WhatAmI callee 0x71FA60 (`B8 30 .. C3`) first byte -> 0x90:
    # TEventClass leaves the conforming set (C3 69->68) and its control fails
    # (C7).  Measured red = {C3, C7}.
    ("TEventClass WhatAmI callee destroyed", "0x71FA60=0x90",
     {"C3", "C7"}),

    # HouseClass GetSize callee 0x504730 (`B8 B86001 00 C3`) first byte -> 0x90:
    # same cascade via the size slot.  Measured red = {C3, C7}.
    ("HouseClass GetSize callee destroyed", "0x504730=0x90",
     {"C3", "C7"}),

    # Name-table entry 69 stores value 0x46 (Temporal) at 0x81710C; rewriting it
    # to 0x45 duplicates RadSite: value set loses 0x46 (C4) and TemporalClass's
    # id no longer maps into the table, so conf 69->68 (C3).  Measured red =
    # {C4, C3}.
    ("name-table value 0x46 duplicated to 0x45", "0x81710C=0x45",
     {"C4", "C3"}),
]

FAILS = []


def run(env_extra=None):
    env = dict(os.environ)
    env.pop("R040_MUTATE", None)
    if env_extra:
        env.update(env_extra)
    p = subprocess.run([sys.executable, GATE], capture_output=True, text=True,
                       env=env, encoding="utf-8", errors="replace")
    red = set()
    for line in (p.stderr or "").splitlines():
        if line.startswith("FAIL\t"):
            tag = line.split("\t")[1]
            if tag != "C1":           # whole-image hash, excluded by convention
                red.add(tag)
    return p.returncode, red


base_rc, base_red = run()
print(f"baseline: rc={base_rc} red={sorted(base_red) or '-'}")
if base_rc != 0:
    print("baseline is not green -- mutation results would be meaningless")
    raise SystemExit(2)

killed = 0
for label, mut, expect in CASES:
    rc, red = run({"R040_MUTATE": mut})
    if red == expect:
        verdict = "KILLED"
        killed += 1
    elif expect & red:
        verdict = "OVERKILL"
        FAILS.append(label)
    else:
        verdict = "SURVIVED"
        FAILS.append(label)
    print(f"{verdict}\t{label}\texpect={sorted(expect)} red={sorted(red) or '-'}")

print(f"\n{killed}/{len(CASES)} killed (exact-set scoring)")
raise SystemExit(0 if not FAILS else 1)
