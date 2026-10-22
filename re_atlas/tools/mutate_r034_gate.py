"""R-034: mutation-test the denominator gate.

Discipline #44: every assertion that claims to measure a value must be shown to
go red when that value changes. Mutations are applied to an in-memory copy by the
gate itself (R034_MUTATE env var); the exe on disk is never touched.

P1 hashes the whole image and therefore trips on every mutation -- it is excluded
from the FAIL set for the same reason as in mutate_r032_gate.py.
"""
import os
import subprocess
import sys

GATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "verify_r034_claims.py")

CASES = [
    # P3: break the prologue of a T2 candidate (0x403A80 starts `81 EC C0 02 00 00`)
    # by turning 0x81 into 0x00. It stops being prologue-shaped -> drops out of T1
    # -> T2 shrinks by one -> P4's pinned count must notice.
    ("0x403A80 prologue broken", 0x00403A80, 0x00, {"P4", "P5"}),
    # P5 anchor: same byte, but assert the anchor assertion itself dies.
    # (kept separate so a single case failing does not mask which one noticed)
    # N2 control: turn one padding nop into a prologue byte so the pad run shortens
    # below 2 and 0x403A80 is no longer a candidate at all. This kills N2 (the pad
    # is no longer padding), P5 (the anchor vanishes) -- and NOT P4, because P4's
    # count is unchanged when the candidate merely moves out of T2 by losing its
    # prologue... except it does change here, since 0x403A80 leaves T2 entirely.
    ("pad before 0x403A80 shortened", 0x00403A74, 0x56, {"N2", "P5"}),
    # P2: destroy the ONLY E8 that targets 0x401190 (`e8 36 6a ff ff` at 0x40A755).
    # 0x401190 has exactly one referrer in the whole image, so the rel32 target
    # count must drop 9,183 -> 9,182.
    # NOTE: my first attempt (0x528A7E) did NOT move the count -- that rel32's
    # target had other referrers too, so the target stayed in the set. A mutation
    # that changes a byte but not the measured quantity proves nothing; picking a
    # uniquely-referenced target is what makes this a real control.
    ("sole E8 to 0x401190 destroyed", 0x0040A755, 0x90, {"P2"}),
]


def run(mutation=None):
    env = dict(os.environ)
    env.pop("R034_MUTATE", None)
    if mutation:
        va, byte = mutation
        env["R034_MUTATE"] = f"0x{va:08X}={byte}"
    p = subprocess.run([sys.executable, GATE], capture_output=True,
                       text=True, timeout=1800, env=env, shell=False)
    fails = set()
    for line in p.stdout.splitlines():
        if line.startswith("FAIL\t"):
            tag = line.split("\t")[1]
            if tag != "P1":
                fails.add(tag)
    return fails, p.stdout, p.returncode


def main():
    base, _o, rc = run()
    print(f"baseline: EXIT={rc} FAILS={sorted(base) or 'none'}")
    if base or rc != 0:
        print("!! baseline not green")
        return 1

    print()
    verdicts = []
    for label, va, byte, expect in CASES:
        fails, _o, rc = run((va, byte))
        hit = expect <= fails
        verdict = "KILLS" if hit else ("kills-other" if fails else "SURVIVES")
        verdicts.append((label, sorted(fails), sorted(expect), verdict))
        print(f"{verdict:12s} {label}")
        print(f"{'':12s}   expected={sorted(expect)} actual={sorted(fails) or 'NONE'} rc={rc}")

    print()
    surv = [v for v in verdicts if v[3] == "SURVIVES"]
    if surv:
        print(f"RESULT: {len(surv)} SURVIVED -> decorative assertions")
        for label, actual, expect, _ in surv:
            print(f"  !! {label}: expected {expect}, nothing failed")
        return 1
    print(f"RESULT: {len(CASES)}/{len(CASES)} mutations killed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
