#!/usr/bin/env python3
# R130 r130k: controls for this round's gate edit (C16 pin of section 2.134).
# The point of a control here is to prove the pin is LOAD-BEARING, i.e. that hollowing
# section 2.134 or editing its floor now FAILS. Without this, "pinned 128 / unpinned 0"
# is just a number in a note line.
#
# Method: edit a COPY of the gate's inputs in place with restoration guaranteed by
# try/finally plus a sha assertion, and run the real check_disc.py against it.
# (R126 S-161 was a temp-directory trap; R128 used the copy-and-restore approach.)
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
GATE = os.path.join(R14, 'check_disc.py')
COMMON = os.path.join(R14, 'R14_COMMON.md')

PASS, FAIL = [], []


def ck(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    d = '' if not detail else (' :: ' + (detail if isinstance(detail, str)
                                         else repr(detail)))
    print(('  PASS ' if cond else '  FAIL ') + name + d[:200])


def run():
    p = subprocess.run([sys.executable, GATE], capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout


def sha(p):
    return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()


def main():
    g0, c0 = sha(GATE), sha(COMMON)
    # hold the pristine bytes in memory so restoration can never depend on disk state
    orig_common = io.open(COMMON, 'rb').read()
    orig_gate = io.open(GATE, 'rb').read()
    print('baseline sha gate', g0[:16], 'common', c0[:16])
    try:
        # ---- positive control ----
        rc, out = run()
        ck('P1 unmodified gate exits 0', rc == 0, str(rc))
        ck('P2 C16 reports pinned 128 unpinned 0',
           'pinned 128' in out and 'unpinned 0' in out)
        ck('P3 134 is among the pinned (min margin now 941)',
           'min margin 941' in out, [l for l in out.splitlines()
                                     if 'min margin' in l][0][:80])

        # ---- NC1: hollow section 2.134 (delete its body) must FAIL ----
        orig = io.open(COMMON, encoding='utf-8', newline='').read()
        i = orig.find('## 2.134')
        assert i > 0, 'section 2.134 not found'
        # keep the heading, drop everything after it
        hollow = orig[:i] + '## 2.134\n'
        with io.open(COMMON, 'w', encoding='utf-8', newline='') as f:
            f.write(hollow)
        rc, out = run()
        ck('N1 hollowed 2.134 makes the gate FAIL', rc != 0, str(rc))
        ck('N1b the failure names C16 and section 134',
           'C16' in out and '134' in out,
           [l for l in out.splitlines() if 'C16' in l and '134' in l][:1])

        # ---- restore ----
        with io.open(COMMON, 'w', encoding='utf-8', newline='') as f:
            f.write(orig)
        assert sha(COMMON) == c0, 'COMMON not restored'
        rc, out = run()
        ck('R1 restored gate exits 0 again', rc == 0, str(rc))

        # ---- NC2: lower the 134 floor without touching the sha -> TAMPERED ----
        gsrc = io.open(GATE, encoding='utf-8', newline='').read()
        bad = gsrc.replace(', 134: 941', ', 134: 900', 1)
        assert bad != gsrc
        with io.open(GATE, 'w', encoding='utf-8', newline='') as f:
            f.write(bad)
        rc, out = run()
        ck('N2 editing the floor alone -> gate FAILs as TAMPERED',
           rc != 0 and 'TAMPERED' in out, str(rc))

        # ---- restore gate ----
        with io.open(GATE, 'w', encoding='utf-8', newline='') as f:
            f.write(gsrc)
        assert sha(GATE) == g0, 'GATE not restored'
        rc, out = run()
        ck('R2 restored gate exits 0 after tamper test', rc == 0, str(rc))

        # ---- NC3: drop 134 from the table entirely (still with old sha) -> FAIL ----
        drop = gsrc.replace(', 134: 941', '', 1)
        assert drop != gsrc
        with io.open(GATE, 'w', encoding='utf-8', newline='') as f:
            f.write(drop)
        rc, out = run()
        ck('N3 removing the 134 pin -> gate FAILs', rc != 0, str(rc))

    finally:
        # Unconditional restoration from the in-memory copies. Self-error S-203: the
        # first version of this block could write an EMPTY file over R14_COMMON.md when
        # its fallback path did not exist. Never let recovery depend on disk state.
        with io.open(COMMON, 'wb') as f:
            f.write(orig_common)
        with io.open(GATE, 'wb') as f:
            f.write(orig_gate)

    print()
    print('final sha gate', sha(GATE)[:16], 'common', sha(COMMON)[:16])
    ck('Z1 gate sha back to baseline', sha(GATE) == g0)
    ck('Z2 common sha back to baseline', sha(COMMON) == c0)
    print('TOTAL PASS %d FAIL %d' % (len(PASS), len(FAIL)))
    if FAIL:
        print('FAILED', FAIL)
    return 0 if not FAIL else 1


if __name__ == '__main__':
    sys.exit(main())
