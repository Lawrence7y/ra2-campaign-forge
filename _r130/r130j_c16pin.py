#!/usr/bin/env python3
# R130 r130j: pin section 2.134 into C16_FLOORS (a new section must be pinned
# deliberately, otherwise it acquires a permanent no-check ticket -- the exact shape of
# the claims-none hole this repo keeps getting bitten by).
# Rule used by this repo: floor = measured body bytes // 2. Measured, not guessed.
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
GATE = os.path.join(R14, 'check_disc.py')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
COMMON = os.path.join(R14, 'R14_COMMON.md')
TS = time.strftime('%Y%m%d_%H%M%S')
NEW_ID = 134


def measure():
    rc = io.open(COMMON, encoding='utf-8', newline='').read()
    cur, buf = None, []
    out = {}
    for l in rc.split('\n'):
        m = re.match(r'^##\s+2\.(\d+)\b', l)
        if m:
            if cur is not None:
                out[cur] = len('\n'.join(buf).encode('utf-8'))
            cur, buf = int(m.group(1)), [l]
        elif cur is not None:
            buf.append(l)
    if cur is not None:
        out[cur] = len('\n'.join(buf).encode('utf-8'))
    return out


def main():
    sizes = measure()
    if NEW_ID not in sizes:
        print('ABORT: section 2.%d not found' % NEW_ID)
        return 1
    body = sizes[NEW_ID]
    floor = body // 2
    print('measured 2.%d body = %d bytes -> floor %d (half)' % (NEW_ID, body, floor))

    src = io.open(GATE, encoding='utf-8', newline='').read()
    if re.search(r'^\s+%d:\s*\d+,' % NEW_ID, src, re.M):
        print('ABORT: id %d already pinned (idempotency guard)' % NEW_ID)
        return 1

    # verify the OLD sha constant matches the OLD table before touching anything
    m = re.search(r'C16_FLOORS = \{(.*?)\n\}', src, re.S)
    table_txt = m.group(1)
    pairs = [(int(a), int(b)) for a, b in
             re.findall(r'(\d+):\s*(\d+)', table_txt)]
    norm = '\n'.join('%d:%d' % (k, v) for k, v in sorted(pairs))
    old_sha = hashlib.sha256(norm.encode('utf-8')).hexdigest()
    reg = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", src).group(1)
    assert old_sha == reg, 'old table sha mismatch; refusing to edit'

    # backup (wx exclusive)
    dst = os.path.join(BASE, 'SUPERSEDED.before_r130_c16pin_check_disc.py_%s.bak' % TS)
    with io.open(dst, 'xb') as f:
        f.write(io.open(GATE, 'rb').read())

    new_pairs = sorted(pairs + [(NEW_ID, floor)])
    new_norm = '\n'.join('%d:%d' % (k, v) for k, v in new_pairs)
    new_sha = hashlib.sha256(new_norm.encode('utf-8')).hexdigest()

    # rewrite the table: append 134 into the last row line
    def repl(mm):
        body_ = mm.group(1).rstrip()
        body_ = body_ + ', %d: %d' % (NEW_ID, floor)
        return 'C16_FLOORS = {' + body_ + '\n}'

    new_src = re.sub(r'C16_FLOORS = \{(.*?)\n\}', repl, src, count=1, flags=re.S)
    new_src = new_src.replace(reg, new_sha, 1)
    assert new_src != src
    with io.open(GATE, 'w', encoding='utf-8', newline='') as f:
        f.write(new_src)

    # read-back: recompute from the file we just wrote
    chk = io.open(GATE, encoding='utf-8', newline='').read()
    m2 = re.search(r'C16_FLOORS = \{(.*?)\n\}', chk, re.S)
    pairs2 = sorted((int(a), int(b)) for a, b in
                    re.findall(r'(\d+):\s*(\d+)', m2.group(1)))
    norm2 = '\n'.join('%d:%d' % (k, v) for k, v in pairs2)
    sha2 = hashlib.sha256(norm2.encode('utf-8')).hexdigest()
    reg2 = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", chk).group(1)
    print('entries %d -> %d' % (len(pairs), len(pairs2)))
    print('sha %s -> %s' % (reg[:16], reg2[:16]))
    assert sha2 == reg2, 'read-back sha mismatch'
    assert (NEW_ID, floor) in pairs2, 'new pin missing after write'
    print('read-back OK; 134 pinned at', floor)
    return 0


if __name__ == '__main__':
    sys.exit(main())
