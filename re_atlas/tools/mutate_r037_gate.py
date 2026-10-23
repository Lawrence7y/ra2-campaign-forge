"""R-037: mutation-test the vtable-scope gate.

Discipline #44: every assertion claiming to measure a value must be shown to go
red when that value changes.  Mutations are applied to an in-memory copy by the
gate itself (R037_MUTATE env var); the exe on disk is never touched.

P1 hashes the whole image and trips on every mutation -- excluded from the
expected-red sets for the same reason as in the other mutate_*_gate.py files.

Scoring rule: KILLED only when the red set equals the expected set EXACTLY.
A mutation that reddens extra assertions is OVERKILL and fails, so that a
mutation merely tripping P1 cannot "kill" every assertion.

Run: python re_atlas/tools/mutate_r037_gate.py
"""

import os
import subprocess
import sys

GATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "verify_r037_scope.py")

CASES = [
    # P5/P6/P8: turn the abstract stub's `xor eax,eax` into `mov eax,1`, so the
    # 9 base classes' slots 11/12 stop being the stub.  P5 must see them move
    # from "not conforming" to... still not `mov eax,imm;ret` (it becomes
    # `B8 01 00 00 00 C3` only if we rewrite all 5 bytes).  Corrupting ONE byte
    # of the stub keeps them non-conforming but breaks the stub-identity test
    # in P6, which is exactly what P6 measures.
    ("abstract stub 0x4C9150 first byte corrupted", "0x4C9150=0x90", {"P1", "P6"}),

    # P5/P6: make one of the 69 conforming classes' v[11] stop being
    # `mov eax,imm; ret`.  TEventClass v[11] = 0x71FA60 (`B8 30 00 00 00 C3`);
    # turning the 0xB8 into 0x90 drops it from the conforming set (69 -> 68)
    # and adds it to the gap set (9 -> 10).
    ("TEventClass v[11] opcode 0xB8 destroyed", "0x71FA60=0x90",
     {"P1", "P5", "P6"}),

    # P5 only: make a conforming class's v[12] stop being `mov eax,imm; ret`.
    # TEventClass v[12] = 0x71FA50 (`B8 58 00 00 00 C3`).
    ("TEventClass v[12] opcode 0xB8 destroyed", "0x71FA50=0x90",
     {"P1", "P5", "P6"}),
]

FAILS = []


def run(env_extra=None):
    env = dict(os.environ)
    env.pop("R037_MUTATE", None)
    if env_extra:
        env.update(env_extra)
    p = subprocess.run([sys.executable, GATE], capture_output=True, text=True,
                       env=env, encoding="utf-8", errors="replace")
    red = set()
    for line in (p.stderr or "").splitlines():
        if line.startswith("FAIL\t"):
            red.add(line.split("\t")[1])
    return p.returncode, red


base_rc, base_red = run()
print(f"baseline: rc={base_rc} red={sorted(base_red) or '-'}")
if base_rc != 0:
    print("baseline is not green -- mutation results would be meaningless")
    raise SystemExit(2)

killed = 0
for label, mut, expect in CASES:
    rc, red = run({"R037_MUTATE": mut})
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
