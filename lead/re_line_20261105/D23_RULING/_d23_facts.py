# -*- coding: utf-8 -*-
"""D-23 offline facts; writes only the explicitly assigned output file."""
import sys
import hashlib
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104')
from ra2tool import Engine

OUT = Path(r'D:\Project\ra2-campaign-forge\lead\re_line_20261105\D23_RULING\_d23_facts_out.txt')
if '--summarize' in sys.argv:
    # Count the already generated Engine records; never build a second stream.
    import re
    records = []
    text = OUT.read_bytes().decode('utf-8')
    for line in text.splitlines():
        m = re.fullmatch(r'([0-9A-F]{8}) ([0-9a-f]+) size=(\d+) (\S+).*', line)
        if m:
            va, raw, size, mnemonic = m.groups()
            assert len(bytes.fromhex(raw)) == int(size)
            records.append((int(va, 16), int(size), mnemonic))
    with OUT.open('a', encoding='utf-8', newline='\n') as out:
        for lo, hi in [(0x429830, 0x429A8F), (0x42A460, 0x42A5A7)]:
            body = [(a, n, m) for a, n, m in records if lo <= a < hi]
            assert body[0][0] == lo
            assert body[-1][0] + body[-1][1] == hi
            assert body[-1][2].startswith('ret')
            assert sum(n for a, n, m in body) == hi-lo
            line = 'F3 BODY [%s,%s) count=%d bytes=%d last_ret=%s padding_excluded=True' % (hex(lo),hex(hi),len(body),sum(n for a,n,m in body),hex(body[-1][0]))
            print(line, file=out, flush=True)
            print(line, flush=True)
    sys.exit(0)

with OUT.open('w', encoding='utf-8', newline='\n') as out:
    def p(*args):
        print(*args, file=out, flush=True)
        print(*args, flush=True)
    e = Engine()
    p('IMAGE sha256=' + hashlib.sha256(e.raw).hexdigest(), 'size=' + str(len(e.raw)), 'ImageBase=' + hex(e.IB))
    stream = e.stream  # exactly one complete decode, reused below
    by = e.by()
    decoded = sum(i.size for i in stream)
    p('COVERAGE decoded_bytes=%d text_bytes=%d insns=%d resync=%d percent=%.9f' % (decoded, e.TSZ, len(stream), e._resync, 100*decoded/e.TSZ))
    def seq(lo, hi):
        return [i for i in stream if lo <= i.address < hi]
    def ins(i):
        return '%08X %s size=%d %s %s' % (i.address, e.rd(i.address, i.size).hex(), i.size, i.mnemonic, i.op_str)
    loop = seq(0x429D6D, 0x42A3DE)
    p('F1 range=[0x429D6D,0x42A3DE) count=%d bytes=%d span=%d contiguous=%s' % (len(loop), sum(i.size for i in loop), 0x42A3DE-0x429D6D, all(a.address+a.size == b.address for a,b in zip(loop,loop[1:]))))
    p('F1 first', ins(loop[0])); p('F1 last', ins(loop[-1]))
    for lo, hi in [(0x429830, 0x429A90), (0x42A460, 0x42A5C0)]:
        body = seq(lo, hi)
        p('F3 WINDOW [%s,%s) count=%d bytes=%d' % (hex(lo), hex(hi), len(body), sum(i.size for i in body)))
        for i in body:
            p(ins(i))
    for lo, hi in [(0x6F9390, 0x6F9405), (0x6F9AE2, 0x6F9B49), (0x6F9440, 0x6F94B0), (0x6F9100, 0x6F9148)]:
        p('F4 WINDOW', hex(lo), hex(hi))
        for i in seq(lo, hi): p(ins(i))
    for R in [9,11,17,29]:
        old=(2*R+1)**2; corrected=1+sum(8*r for r in range(1,R))
        p('F4 GEOMETRY R=%d rings=0..%d W3=%d corrected=%d excess=%d relative_excess=%.9f%%' % (R,R-1,old,corrected,old-corrected,100*(old/corrected-1)))
