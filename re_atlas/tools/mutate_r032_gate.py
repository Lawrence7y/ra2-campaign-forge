"""R-033: mutation-test the R-032 gate.

GOAL-3T S388: "N/N PASS 这个数字本身没有意义。必须问:这 N 条里,有多少条的断言
真的把被测物放进了等式?" This drives the answer for verify_r032_claims.py.

For each single-byte mutation below, the gate is re-run in a child process with
the mutation passed through the environment (R032_MUTATE), and the resulting
FAIL set is recorded. A mutation that is supposed to kill assertion X but does
NOT is a decorative assertion.

Read-only on the exe: mutations are applied to an in-memory copy by the gate.
"""
import os
import subprocess
import sys

GATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "verify_r032_claims.py")

# (label, VA, new_byte, assertions expected to FAIL)
CASES = [
    # P2: 0x528A10's `ret 0x14` (C2 14 00) -> `ret 0x10`, i.e. arity 5 -> 4.
    ("ReadString ret 0x14 -> 0x10", 0x00528BC7, 0x10, {"P2"}),
    # P4/P6: turn Read_VehicleTypes' `call 0x526960` (GetKeyCount, E8 at 0x672372)
    # into a NOP so the call disappears outright. The loader still calls GetKeyName,
    # so it stays in ENUM (P4 still holds); but it is no longer "GetKeyCount ->
    # GetKeyName shaped", so P6's A/B split must notice the change.
    # NOTE: merely RETARGETING this call does NOT kill either assertion -- retargeting
    # to GetSection keeps it in the enum set, and my first two attempts assumed
    # otherwise. That was a wrong expectation, not a weak assertion.
    ("VehicleTypes GetKeyCount call -> NOP", 0x00672372, 0x90, {"P4", "P6", "P3"}),
    # P7: the `je` after ReadString at 0x6723AA (74 09) -> EB (jmp).
    ("VehicleTypes je -> jmp (drop gate)", 0x006723AA, 0xEB, {"P7"}),
    # P8: "<none>" literal at 0x817474 -> NUL, breaking the compare string.
    ("<none> literal mutated", 0x00817474, 0x00, {"P8"}),
    # P5/P10: a key literal in Read_General -> first byte NUL. Must move BOTH the
    # site count (P5) and the 651 reconciliation (P10).
    ("[General] key literal mutated", 0x0083CF2C, 0x00, {"P5", "P10"}),
]


def run(mutation=None):
    env = dict(os.environ)
    env.pop("R032_MUTATE", None)
    if mutation:
        va, byte = mutation
        env["R032_MUTATE"] = f"0x{va:08X}={byte}"
    p = subprocess.run([sys.executable, GATE], capture_output=True,
                       text=True, timeout=900, env=env, shell=False)
    fails = set()
    for line in p.stdout.splitlines():
        if line.startswith("FAIL\t"):
            tag = line.split("\t")[1]
            # P1 hashes the WHOLE image, so every mutation trips it by design.
            # Excluding it is not leniency: keeping it would make every case look
            # "killed" and hide assertions that never read their own quantity.
            if tag != "P1":
                fails.add(tag)
    return fails, p.stdout, p.returncode


def main():
    base_fails, _out, base_rc = run()
    print(f"baseline: EXIT={base_rc} FAILS={sorted(base_fails) or 'none'}")
    if base_fails or base_rc != 0:
        print("!! baseline is not green; mutation testing is meaningless")
        return 1

    print()
    verdicts = []
    for label, va, byte, expect in CASES:
        fails, _out, rc = run((va, byte))
        killed = bool(fails)
        hit_expected = expect <= fails
        verdict = "KILLS" if hit_expected else ("kills-other" if killed else "SURVIVES")
        verdicts.append((label, sorted(fails), sorted(expect), verdict))
        print(f"{verdict:12s} {label}")
        print(f"{'':12s}   expected={sorted(expect)}  actual={sorted(fails) or 'NONE'}  rc={rc}")

    print()
    survivors = [v for v in verdicts if v[3] == "SURVIVES"]
    if survivors:
        print(f"RESULT: {len(survivors)} mutation(s) SURVIVED -> those assertions are decorative")
        for label, actual, expect, _ in survivors:
            print(f"  !! {label}: expected {expect} to fail, nothing did")
        return 1
    print(f"RESULT: {len(CASES)}/{len(CASES)} mutations killed by their expected assertion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
