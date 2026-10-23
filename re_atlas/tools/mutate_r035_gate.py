"""R-035: mutation-test the denominator gate.

Discipline #44: every assertion claiming to measure a value must be shown to go
red when that value changes. Mutations are applied to an in-memory copy by the
gate itself (R035_MUTATE env var); the exe on disk is never touched.

P1 hashes the whole image and trips on every mutation -- excluded from the FAIL
set for the same reason as in mutate_r032_gate.py / mutate_r034_gate.py.

Design rule (G-55): pick a mutation that changes the QUANTITY the assertion
counts, not merely a byte. Where two candidate targets existed, the one whose
change actually moves the count was chosen and the discarded one is noted.
"""
import os
import subprocess
import sys

GATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "verify_r035_claims.py")

CASES = [
    # P2: destroy one E8 whose rel32 target is uniquely referenced, so the E8
    # target set shrinks by exactly one. 0x401190 has a single referrer.
    ("sole E8 to 0x401190 destroyed", (0x0040A755, 0x90), {"P2"}),

    # P5: break the anchor's prologue (`81 EC C0 02 00 00` -> `00 EC ...`), so
    # 0x403A80 stops being prologue-shaped and leaves the UPPER set.
    # P7 is expected to stay green: no corpus name sits at 0x403A80, so the
    # named-count intersection is unaffected. P5 measures the set, P7 measures
    # the intersection -- keeping them separate is the point.
    ("anchor 0x403A80 prologue broken", (0x00403A80, 0x00), {"P5"}),

    # P6: 0x404555 is an E9 target inside 0x4041D0, referenced by TWO jmps
    # (0x404457 and 0x40446F). Corrupting only one leaves the target covered,
    # so both must go. This pair is what makes the count move.
    ("both E9 referrers of 0x404555 corrupted",
     (0x00404457, 0x90, 0x0040446F, 0x90), {"P6"}),

    # P8: blank one ':' in a pure function-name literal
    # (`CDControlClass::Lock_CD_Drive_95` at 0x81C6D8). It stops matching the
    # Class::Method regex, so the pure count and the prefix set both shrink.
    ("pure name literal 0x81C6D8 '::' destroyed", (0x0081C6DD, 0x5F), {"P8"}),

    # P9: the `push imm32` opcode at a name-push site is no longer 0x68.
    ("name-push opcode 0x652CF3 no longer 0x68", (0x00652CF3, 0x90), {"P9"}),

    # P10: the call opcode after a __FILE__ push becomes a nop, so that site no
    # longer has a call in the window and the 0x734E60 tally drops.
    ("__FILE__ callee call destroyed at 0x41099B", (0x0041099B, 0x90), {"P10"}),

    # P11: an INI-reader call becomes a nop, so that ident site stops being
    # classified as a reader argument.
    # NOTE: the first attempt used 0x672372 and only P4 went red -- that address
    # is not the call following any ident site, so it changed a byte without
    # changing the quantity P11 counts (G-55 again). 0x410AA0 IS the single
    # reader call following the `push 'Name'` at 0x410A98, verified by scanning
    # all 2,376 single-call ident sites.
    ("INI reader call after push 'Name' destroyed", (0x00410AA0, 0x90), {"P11"}),

    # ---- controls, now rewritten to be killable (v5 §7) -------------------
    # N1 asserts INTERIOR IS covered. Its host function 0x4039C0 has exactly two
    # E8 referrers (0x403ACD, 0x403AFF); destroying both orphans it, the body
    # stops being covered, and N1 goes red.
    ("N1 host function 0x4039C0 orphaned",
     (0x00403ACD, 0x90, 0x00403AFF, 0x90), {"N1"}),

    # N2 asserts E9_INTRA_SAMPLE is an E9 target AND covered. Destroying both
    # `jmp` referrers (0x404457, 0x40446F) breaks both conjuncts.
    ("N2 both E9 referrers of 0x404555 corrupted",
     (0x00404457, 0x90, 0x0040446F, 0x90), {"N2"}),

    # N3 asserts four zero referrers. Planting a dword pointer to 0x403A80 in a
    # zero-filled .data run (0x81B21A) makes the 4th conjunct nonzero.
    ("N3 dword pointer to 0x403A80 planted",
     (0x0081B21A, 0x80, 0x0081B21B, 0x3A, 0x0081B21C, 0x40, 0x0081B21D, 0x00),
     {"N3"}),

    # N4 asserts the E9-only set size AND that none of them are roots. Turning
    # one E9 referrer into an E8 (`E9` -> `E8` keeps the 5-byte shape) promotes
    # its target from E9-only to an E8 root, so e9_only shrinks by one.
    ("N4 one E9 promoted to E8 at 0x404457", (0x00404457, 0xE8), {"N4"}),

    # ---- R-038 (V-001 §七.5): a mutation that DISTINGUISHES the byte-scan E8
    # count from the aligned E8 count.
    #
    # Every earlier case moved both counts together, because both were computed
    # from the same byte scan -- a gate built on one reading cannot reject a
    # defect in that reading (V-001 §四: "门禁抓不到与自己同构的错误").
    #
    # 0x004011DB is one of the 563 phantom sites: its 0xE8 is an operand byte of
    # another instruction, and it is the ONLY source that reaches 0x405B99.
    # Rewriting its rel32 to 0x7FFFFFFF pushes that target out of .text for the
    # BYTE SCAN, while the ALIGNED decode never counted this site at all.
    # Expected: P2 and P3 red (byte-scan quantities), P2c GREEN (aligned-only).
    ("phantom E8 at 0x4011DB displaced out of .text",
     (0x004011DC, 0xFF, 0x004011DD, 0xFF, 0x004011DE, 0xFF, 0x004011DF, 0x7F),
     {"P2", "P3"}),
]


def run(mutations=None):
    env = dict(os.environ)
    env.pop("R035_MUTATE", None)
    if mutations:
        # mutations is a flat tuple (va, byte, va, byte, ...)
        parts = []
        for k in range(0, len(mutations), 2):
            parts.append(f"0x{mutations[k]:08X}={mutations[k+1]}")
        env["R035_MUTATE"] = ",".join(parts)
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
    for label, muts, expect in CASES:
        fails, _o, rc = run(muts)
        hit = expect <= fails
        verdict = "KILLS" if hit else ("kills-other" if fails else "SURVIVES")
        verdicts.append((label, sorted(fails), sorted(expect), verdict))
        print(f"{verdict:12s} {label}")
        print(f"{'':12s}   expected={sorted(expect)} "
              f"actual={sorted(fails) or 'NONE'} rc={rc}")

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
