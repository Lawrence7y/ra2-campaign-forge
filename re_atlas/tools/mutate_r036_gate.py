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

    # P3 + P3b + P7: the `push imm32` opcode of a __FILE__ site stops being
    # 0x68, so that site leaves the path class.  Path count drops in BOTH the
    # byte-scan count (P3) and the aligned count (P3b: its path conjunct), and
    # because the same site is also a debug site the debug total drops too.
    ("__FILE__ push 0x410994 no longer 0x68", "0x410994=0x90",
     {"P1", "P3", "P3b", "P7"}),

    # P3 + P3b: an ident-class push site.  ident is NOT part of the debug sum,
    # so P7 must stay green -- that separation is what this case checks.
    ("ident push 0x410A98 no longer 0x68", "0x410A98=0x90", {"P1", "P3", "P3b"}),

    # P4: blank one ':' in a pure name literal so it stops matching PURE and
    # PREFIX -- literal count, method set and site count all shrink.
    ("pure name literal 0x81C6D8 '::' destroyed", "0x81C6DD=0x5F", {"P1", "P4"}),

    # P4 + P5: a name-push opcode becomes a nop, so the site leaves the prefix
    # push set AND stops attributing to a function.
    ("name-push 0x652CF3 no longer 0x68", "0x652CF3=0x90", {"P1", "P4", "P5"}),

    # P6: `ToolTip.cpp` has exactly ONE push site (0x724AFA).  Removing it
    # takes the file from "attributed" to "unattributed", so 69 -> 68 while the
    # raw basename census stays at 74.  This is the case that actually kills P6.
    # It also drops the path count (both byte-scan and aligned), so P3 and P3b
    # and the debug total P7 must go red too -- the red set is P3,P3b,P6,P7.
    ("single-site file ToolTip.cpp loses its only push",
     "0x724AFA=0x90", {"P1", "P3", "P3b", "P6", "P7"}),

    # P3b (R-039): the byte-scan text class carries exactly ONE phantom site,
    # 0x5BA0CE (the imm8 byte of `cmp eax,0x68` at 0x5BA0CC; the four bytes
    # after it spell the pointer 0x0084840F -> "@E@WorldDominationTour@@@@").
    # Making that string non-printable removes the phantom from the byte scan:
    # P3 drops (6,277 -> 6,276), P7 drops (debug 2,589 -> 2,588) and P3b must
    # go red because its conjunct `nonaligned_sites == [phantom]` no longer
    # holds (the aligned counts themselves are unchanged -- the phantom was
    # never aligned).  This proves P3b actually enumerates the phantom rather
    # than being a restatement of P3.
    ("phantom string 0x84840F made non-printable",
     "0x84840F=0x01", {"P1", "P3", "P3b", "P7"}),
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
