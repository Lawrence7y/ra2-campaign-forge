# -*- coding: utf-8 -*-
"""R-041: mutation-test the L-21 gate (TEventClass +0x28/+0x30).

Same conventions as mutate_r040_gate.py:
  - mutations go through the gate's R041_MUTATE env (in-memory copy only;
    the exe on disk is never touched);
  - expected red sets are MEASURED first, written last (the G-55 discipline:
    drafting them from memory produced wrong guesses in this session's
    previous round);
  - exact-set scoring: KILLED requires red == expect; OVERKILL (superset)
    means two assertions share one byte-window -> the gate must be decoupled,
    not the expectation bent; SURVIVED means the assertion is not actually
    pinned by the bytes it names.

C1/C2/C7 test the three field-displacement bytes; C3 the resolver call rel32;
C4 the Name-displacement inside the X4 window; C5 the registry vtable
immediate; C6 the "%d,%d,%s" literal first byte; C8 the GetSize immediate;
C9 the write-site disp (shared by X9 and X10 -> expect TWO reds); C10 the
ctor zero-store disp that ONLY X10 reads.  A shared byte legitimately kills
every assertion that window covers -- the expectation must list them all
(bending the set instead would hide the coupling, same G-55 pattern as R-036).

Run: python re_atlas/tools/mutate_r041_gate.py
"""

import os
import subprocess
import sys

GATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "r041_l21_eventteam.py")

CASES = [
    # slot10 `mov eax,[ecx+0x28]` disp 0x28->0x20.  The byte 0x71F802 is inside
    # the X1 window only (X1 = 17 bytes at 0x71F800; the same disp at 0x71F80C
    # is past that window and belongs to X7).  Measured red should be {X1}.
    ("slot10 head [ecx+0x28] displaced", "0x71F802=0x20", {"X1"}),

    # Save `mov eax,[esi+0x28]` at 0x71F82E (8b 46 28): disp byte at 0x71F830
    # -> 0x20 breaks the X2 first block; X2b reads 0x71F852 (separate).
    # Measured red = {X2}.
    ("Save [esi+0x28] disp displaced", "0x71F830=0x20", {"X2"}),

    # parse fn `call 0x6F0FC0`: flip rel32 LSB -> different callee.
    # Measured red = {X3} (X4 reads the callee itself, untouched here).
    ("resolver call rel32 LSB", "0x71F596=0x00", {"X3"}),

    # resolver `add ecx,0x24` at 0x6F0FDB..0x6F0FDD (83 C1 24); the 0x24 (Name
    # slot) sits at 0x6F0FDD inside the 34-byte X4 window (0x6F0FC0..0x6F0FE1).
    # X5b reads 0x6F1976.. (separate region).  Measured red = {X4}.
    ("resolver Name-disp 0x24->0x25", "0x6F0FDD=0x25", {"X4"}),

    # registry ctor `mov [esi+8],0x7f47ac`: the imm LSB at 0x6F080D (instr
    # starts 0x6F080A: c7 46 08 AC 47 7f 00).  X6 (structural) reads
    # symbols.json, unaffected.  Measured red = {X5}.
    ("registry vtable imm corrupted", "0x6F080D=0x00", {"X5"}),

    # "%d,%d,%s" first byte '%' -> '&': X5c red.  Measured red = {X5c}.
    ("debug format string corrupted", "0x844714=0x26", {"X5c"}),

    # X7 window starts 0x71F80B; `cmp [ecx+0x30],edx` disp byte at 0x71F813
    # (past X1's 17-byte window which ends 0x71F810).  Measured red = {X7}.
    ("slot10 tail [ecx+0x30] disp (X7-only)", "0x71F813=0x2F", {"X7"}),

    # GetSize `mov eax,0x58` imm LSB -> 0x50: X8 red (its conjunct), and
    # nothing else reads 0x71FA51.  Measured red = {X8}.
    ("GetSize immediate 0x58->0x50", "0x71FA51=0x50", {"X8"}),

    # X9-only region: the `mov [esi+0x28],edx` disp byte at 0x72750D (inside
    # the 17-byte X9 window 0x7274FD..0x72750C? window ends 0x7274FD+16=0x72750D
    # -- the last byte, so the flip hits the window tail only).
    # Measured red = {X9}.
    ("write-site [esi+0x28] disp displaced", "0x72750D=0x2F", {"X9", "X10"}),

    # X10-only region: the ctor zero-store `mov [esi+0x28],ebx` disp byte at
    # 0x71E6B4 (89 5E 28; window 0x71E6B2..0x71E6B4).  No other assertion
    # reads these three bytes.  Measured red = {X10}.
    ("ctor zero-store [esi+0x28] disp displaced", "0x71E6B4=0x29", {"X10"}),
]

FAILS = []


def run(env_extra=None):
    env = dict(os.environ)
    env.pop("R041_MUTATE", None)
    if env_extra:
        env.update(env_extra)
    p = subprocess.run([sys.executable, GATE], capture_output=True, text=True,
                       env=env, encoding="utf-8", errors="replace")
    red = set()
    for line in (p.stderr or "").splitlines():
        if line.startswith("X") and " FAIL:" in line:
            red.add(line.split(" ", 1)[0])
    return p.returncode, red


base_rc, base_red = run()
print(f"baseline: rc={base_rc} red={sorted(base_red) or '-'}")
if base_rc != 0:
    print("baseline is not green -- mutation results would be meaningless")
    raise SystemExit(2)

killed = 0
for label, mut, expect in CASES:
    rc, red = run({"R041_MUTATE": mut})
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
