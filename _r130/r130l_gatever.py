#!/usr/bin/env python3
# R130 r130l: bump GATE_VER R129 -> R130 and sync the C10 registry row (id 20),
# because this round DID change check_disc.py (C16 pin of section 2.134).
# C10 requires the registry row's grep and GATE_VER to agree; both must move together.
# Backups are wx-exclusive; every step is read-back verified; idempotency guarded.
import hashlib
import io
import os
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
GATE = os.path.join(R14, 'check_disc.py')
TSV = os.path.join(R14, 'DISC_RECHECK.tsv')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
TS = time.strftime('%Y%m%d_%H%M%S')


def sha(p):
    return hashlib.sha256(io.open(p, 'rb').read()).hexdigest()[:16]


def main():
    gb = io.open(GATE, 'rb').read()
    tb = io.open(TSV, 'rb').read()
    print('before gate', hashlib.sha256(gb).hexdigest()[:16],
          'tsv', hashlib.sha256(tb).hexdigest()[:16])

    gsrc = gb.decode('utf-8')
    tsrc = tb.decode('utf-8')

    if "GATE_VER = 'R130'" in gsrc:
        print('ABORT: already R130 (idempotency guard)')
        return 1
    assert "GATE_VER = 'R129'" in gsrc
    assert "grep=(?m)^GATE_VER = 'R129'" in tsrc

    # backups
    for p, tag in ((GATE, 'r130_gatever_gate'), (TSV, 'r130_gatever_tsv')):
        dst = os.path.join(BASE, 'SUPERSEDED.before_%s_%s_%s.bak'
                           % (tag, os.path.basename(p), TS))
        with io.open(dst, 'xb') as f:
            f.write(io.open(p, 'rb').read())
        print('backup', os.path.basename(dst))

    # edit 1: GATE_VER (exactly one occurrence)
    assert gsrc.count("GATE_VER = 'R129'") == 1
    newg = gsrc.replace("GATE_VER = 'R129'", "GATE_VER = 'R130'", 1)
    with io.open(GATE, 'w', encoding='utf-8', newline='') as f:
        f.write(newg)

    # edit 2: registry row grep (exactly one occurrence)
    assert tsrc.count("grep=(?m)^GATE_VER = 'R129'") == 1
    newt = tsrc.replace("grep=(?m)^GATE_VER = 'R129'",
                        "grep=(?m)^GATE_VER = 'R130'", 1)
    with io.open(TSV, 'w', encoding='utf-8', newline='') as f:
        f.write(newt)

    # read-back
    g2 = io.open(GATE, 'rb').read()
    t2 = io.open(TSV, 'rb').read()
    a = g2.decode('utf-8')
    b = t2.decode('utf-8')
    assert "GATE_VER = 'R130'" in a and "GATE_VER = 'R129'" not in a
    assert "grep=(?m)^GATE_VER = 'R130'" in b and "grep=(?m)^GATE_VER = 'R129'" not in b
    # CR profiles must not move
    assert g2.count(b'\r') == gb.count(b'\r'), 'gate CR moved'
    assert t2.count(b'\r') == tb.count(b'\r'), 'tsv CR moved'
    print('after  gate', hashlib.sha256(g2).hexdigest()[:16],
          'tsv', hashlib.sha256(t2).hexdigest()[:16])
    print('CR gate', g2.count(b'\r'), 'tsv', t2.count(b'\r'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
