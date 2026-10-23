"""R-036: mutation-test the R1-3 deliverable gate.

Discipline #44: every assertion claiming to measure a value must be shown to go
red when that value changes.  Mutations are applied to an in-memory copy by the
gate itself (R036_MUTATE env var); the exe on disk is never touched.

P1 hashes the whole image and trips on every mutation -- excluded from the
expected-red sets for the same reason as in mutate_r032/r034/r035_gate.py.

Design rule (G-55): pick a mutation that changes the QUANTITY the assertion
counts, not merely a byte.

Scoring rule (avoids the "N/N PASS with inflated counts" trap): a case counts as
KILLED only if the red set equals the expected set EXACTLY.  A case that reddens
extra assertions is reported as OVERKILL and fails -- otherwise a mutation that
merely trips P1 would "kill" every assertion.

Run: python re_atlas/tools/mutate_r036_gate.py
"""

import os
import subprocess
import sys

GATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "r036_r13_deliverable.py")

CASES = [
    # P2: break the prologue of one T2 candidate so it leaves the T2 set.
    # 0x403A80 is the R-034 anchor, `81 EC C0 02 00 00`; zeroing the opcode
    # makes it stop matching PROLOGUE.  Nothing else reads this address, so the
    # red set should be exactly {P1, P2}.
    ("T2 anchor 0x403A80 prologue broken", "0x403A80=0x00", {"P1", "P2"}),

    # P3 + P7: the `push imm32` opcode of a __FILE__ site stops being 0x68, so
    # that site leaves the path class.  Path count drops, and because the same
    # site is also a debug site the debug total drops too.
    ("__FILE__ push 0x410994 no longer 0x68", "0x410994=0x90", {"P1", "P3", "P7"}),

    # P3: an ident-class push site.  ident is NOT part of the debug sum, so P7
    # must stay green -- that separation is what this case checks.
    ("ident push 0x410A98 no longer 0x68", "0x410A98=0x90", {"P1", "P3"}),

    # P4: blank one ':' in a pure name literal so it stops matching PURE and
    # PREFIX -- literal count, method set and site count all shrink.
    ("pure name literal 0x81C6D8 '::' destroyed", "0x81C6DD=0x5F", {"P1", "P4"}),

    # P4 + P5: a name-push opcode becomes a nop, so the site leaves the prefix
    # push set AND stops attributing to a function.
    ("name-push 0x652CF3 no longer 0x68", "0x652CF3=0x90", {"P1", "P4", "P5"}),

    # P6: `ToolTip.cpp` has exactly ONE push site (0x724AFA).  Removing it
    # takes the file from "attributed" to "unattributed", so 69 -> 68 while the
    # raw basename census stays at 74.  This is the case that actually kills P6.
    ("single-site file ToolTip.cpp loses its only push",
     "0x724AFA=0x90", {"P1", "P3", "P6", "P7"}),
]

FAILS = []


def run(env_extra=None):
    env = dict(os.environ)
    env.pop("R036_MUTATE", None)
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
    rc, red = run({"R036_MUTATE": mut})
    if red == expect:
        verdict = "KILLED"
        killed += 1
    elif expect & red:
        verdict = "OVERKILL"      # extra assertions reddened: not a clean kill
        FAILS.append(label)
    else:
        verdict = "SURVIVED"
        FAILS.append(label)
    print(f"{verdict}\t{label}\texpect={sorted(expect)} red={sorted(red) or '-'}")

print(f"\n{killed}/{len(CASES)} killed (exact-set scoring)")
raise SystemExit(0 if not FAILS else 1)
