# -*- coding: utf-8 -*-
"""R218-C verification: parser correctness, segment-prefix leakage, disp extremes, objdump cross-check prep."""
import sys, re
from collections import Counter
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

SEC = P.B['.text']
LO, RAWOFF, RAWSZ = SEC['lo'], SEC['rawptr'], SEC['rawsize']

# ---- 1) detail=True spot checks on the known forwarding stub and a few hits ----
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True
for va in (0x410210, 0x41021a, 0x401422, 0x4055e4, 0x403cac):
    off = P.r2o(va)
    buf = P.RAW[off:off + 24]
    print('DETAIL %#x raw=%s' % (va, buf[:12].hex()))
    for i in md.disasm(buf, va):
        print('   %#x %s %s' % (i.address, i.mnemonic, i.op_str))
        if i.address > va:
            break
    print()

# ---- 2) full lite re-scan: classify ALL call/jmp mem operands by syntactic shape ----
md2 = Cs(CS_ARCH_X86, CS_MODE_32)
md2.detail = False
md2.skipdata = True
segpref = []
shape = Counter()
disp_all = Counter()
cur_va, cur_off, rem = LO, RAWOFF, RAWSZ
while rem > 0:
    n = min(0x10000, rem)
    buf = P.RAW[cur_off:cur_off + n]
    last = None
    for addr, size, mnem, opstr in md2.disasm_lite(buf, cur_va):
        last = (addr, size)
        if mnem.lower() not in ('call', 'jmp'):
            continue
        if '[' not in opstr:
            continue
        if re.search(r'\bptr\s+\w+:', opstr):
            segpref.append((addr, opstr))
        # normalize inner text
        inner = re.search(r'\[([^\]]*)\]', opstr).group(1)
        shape[re.sub(r'0x[0-9a-fA-F]+', 'N', inner)] += 1
        m = re.search(r'([+-])\s*(0x[0-9a-fA-F]+|\d+)', inner)
        if m:
            v = int(m.group(2), 0)
            disp_all[(-v if m.group(1) == '-' else v)] += 1
        elif not re.search(r'[+-]', inner):
            disp_all[0] += 1
    if last is None:
        break
    adv = (last[0] + last[1]) - cur_va
    if adv <= 0:
        adv = n
    cur_va += adv; cur_off += adv; rem -= adv
    del buf

print('VERIFY segment-prefixed call/jmp mem count = %d' % len(segpref))
for a, o in segpref[:30]:
    print('   SEG %#x %s' % (a, o))
print('VERIFY disp==0 (all call/jmp mem incl esp/abs-free) = %d' % disp_all[0])
print('VERIFY disp==0x2c (all call/jmp mem) = %d' % disp_all[0x2c])
print('VERIFY disp min=%d max=%d negative_count=%d' %
      (min(disp_all), max(disp_all), sum(c for d, c in disp_all.items() if d < 0)))
print('VERIFY operand shapes TOP15:')
for k, c in sorted(shape.items(), key=lambda kv: -kv[1])[:15]:
    print('   %-40s %d' % (k, c))
