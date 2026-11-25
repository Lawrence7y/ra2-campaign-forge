#!/usr/bin/env python3
"""R133 deepseek audit: C8 + C9 recomputed from an OBJDUMP linear sweep.

Why objdump: capstone 5.0.7 disasm_lite()+skipdata SIGSEGVs nondeterministically on
this binary (see r133ds2_capstone_bug.json). objdump performs a genuine linear sweep
and never crashes. This gives a second, independent implementation of the C9 backward
walk, so agreement with the capstone path (where it survives) is real cross-checking.

Walk rule (from the card): from the call site, walk BACKWARDS requiring
addr+size == next_addr; stop at the first gap or first control transfer; collect the
pushes in the contiguous tail; nearest three; arg3 = the earliest of those three.
"""
import json, re, sys

OBJD = '/tmp/objd_full.txt'
A_VA, B_VA = 0x6bedb0, 0x41c250

ADDR = re.compile(r'^\s*([0-9a-f]+):')

rows = []            # (addr, size, mnem, op_str)
skipped = 0
merged = 0
with open(OBJD) as f:
    for ln in f:
        if '\t' not in ln:
            continue
        parts = ln.rstrip('\n').split('\t')
        if len(parts) < 2:
            continue
        head = parts[0].strip()
        m = ADDR.match(head)
        if not m:
            skipped += 1
            continue
        addr = int(m.group(1), 16)
        raw = parts[1].strip().split()
        if not raw or any(len(b) != 2 for b in raw):
            skipped += 1
            continue
        instr = parts[2].strip() if len(parts) > 2 else ''
        if not instr:
            # objdump continuation of an instruction whose bytes overflowed the
            # 7-byte display column: same instruction, extra bytes. Extend the
            # previous row instead of emitting a bogus 1-byte row.
            if rows and rows[-1][0] + rows[-1][1] == addr:
                pa, ps, pm, po = rows[-1]
                rows[-1] = (pa, ps + len(raw), pm, po)
                merged += 1
            else:
                skipped += 1
            continue
        if instr.startswith('('):
            mnem, op = '(bad)', ''
        else:
            bits = instr.split(None, 1)
            mnem = bits[0]
            op = bits[1].strip() if len(bits) > 1 else ''
        rows.append((addr, len(raw), mnem, op))

addrs = [r[0] for r in rows]
sizes = [r[1] for r in rows]
idx = {a: i for i, a in enumerate(addrs)}

gaps = [i for i in range(1, len(rows)) if rows[i - 1][0] + rows[i - 1][1] != rows[i][0]]

CTRL_MNEMS = {'ret', 'retq', 'iret', 'iretd', 'jmp', 'call', 'ljmp', 'lcall'}
def is_ctrl(mnem):
    return mnem in CTRL_MNEMS or mnem.startswith('j') or mnem.startswith('loop')

# ---- C8: all call/jmp rows whose operand is exactly the entry VA ----
sites = {A_VA: [], B_VA: []}
for a, s, mnem, op in rows:
    if mnem in ('call', 'callq', 'jmp'):
        try:
            tgt = int(op.split()[0], 16)
        except ValueError:
            continue
        if tgt in sites:
            sites[tgt].append((a, s, mnem, op))

C8 = {'A_count': len(sites[A_VA]), 'B_count': len(sites[B_VA]),
      'total': len(sites[A_VA]) + len(sites[B_VA]),
      'A_sites': [hex(a) for a, *_ in sites[A_VA]],
      'B_sites': [hex(a) for a, *_ in sites[B_VA]],
      'A_insn': [{'va': hex(a), 'size': s, 'mnem': m, 'op': op} for a, s, m, op in sites[A_VA]],
      'B_insn': [{'va': hex(a), 'size': s, 'mnem': m, 'op': op} for a, s, m, op in sites[B_VA]]}
print(json.dumps({'sweep': {'rows': len(rows), 'first': hex(rows[0][0]),
                            'last_end': hex(rows[-1][0] + rows[-1][1]),
                            'gap_count': len(gaps)},
                  'C8': C8}, indent=2))

# ---- C9 ----
all_sites = [(a, A_VA) for a, *_ in sites[A_VA]] + [(a, B_VA) for a, *_ in sites[B_VA]]
all_sites.sort()

C9 = []
for site, tpl in all_sites:
    i = idx[site]
    tail = []
    stop = 'start-of-sweep'
    j = i - 1
    while j >= 0:
        if rows[j][0] + rows[j][1] != rows[j + 1][0]:
            stop = 'gap'
            break
        tail.append(j)
        if is_ctrl(rows[j][2]):
            stop = 'control-transfer'
            break
        j -= 1
    tail.sort()                         # ascending address; last = furthest
    pushes = [(rows[k][0], rows[k][2], rows[k][3], rows[k][1])
              for k in tail if rows[k][2] == 'push']
    pushes.sort()                       # ascending address
    nearest3 = list(reversed(pushes))[:3]   # nearest-first
    C9.append({
        'site': hex(site), 'template': hex(tpl),
        'walk_stopped_by': stop, 'tail_insn_count': len(tail),
        'tail_first_va': hex(rows[tail[0]][0]) if tail else None,
        'tail_last_va': hex(rows[tail[-1]][0]) if tail else None,
        'pushes_in_tail_ascending': [{'va': hex(p[0]), 'op': p[2]} for p in pushes],
        'nearest_three': [{'va': hex(p[0]), 'op': p[2], 'off_from_site': p[0] - site}
                          for p in nearest3],
        'arg1_nearest': nearest3[0][2] if len(nearest3) > 0 else None,
        'arg2': nearest3[1][2] if len(nearest3) > 1 else None,
        'arg3': nearest3[2][2] if len(nearest3) > 2 else None,
    })

print(json.dumps({'C9': C9}, indent=2))
json.dump({'sweep': {'rows': len(rows), 'first': hex(rows[0][0]),
                     'last_end': hex(rows[-1][0] + rows[-1][1]), 'gap_count': len(gaps)},
           'C8': C8, 'C9': C9},
          open('/home/t628/projects/ra2-campaign-forge/_r133/sub_deepseek/r133ds2_objdump.json', 'w'), indent=2)
