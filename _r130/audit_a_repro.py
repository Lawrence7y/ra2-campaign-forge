#!/usr/bin/env python3
"""R130 audit A: independent reproduction of the "one class-factory table" result.

T1  every call in .text whose target is exactly 0x6bedb0 (count + addresses)
T2  is each of those inside the loop 0x6bc34d .. back-edge
T3  census of mov-imm / add-step / cmp-bound / backwards-cond-jmp loops
T4  .rdata-head tables with stride >= 8 other than 0x7f3710

Method / constraints
--------------------
* capstone disasm_lite only; md.detail is never set.
* ONE aligned forward pass over the whole .text section, from .text start.
  The pass uses skipdata=True because .text contains embedded data (32-bit jump
  tables). Without skipdata the generator stops silently at the first
  undecodable byte (0x46f0e0) after 155215 insns and everything past it is
  invisible -- that is the failure mode this script originally had.
* Bounded instruction history: ~0x1000 bytes of preceding instructions, stored
  as a deque, never the full instruction list.
* Every reported loop is re-verified by an independent byte-level decode that
  starts AT the loop head (a branch target, hence a legitimate boundary) and
  walks forward to the back-edge. Unverified loops are dropped and counted.
"""
import collections
import hashlib
import json
import os

import capstone
import pefile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audit_a_repro.json')

TARGET_FN = 0x6bedb0
LOOP_HEAD_EXPECT = 0x6bc34d
HEAD_EXPECT = 0x7f3710
BOUND_EXPECT = 0x7f3718
STEP_EXPECT = 8

WINDOW_BYTES = int(os.environ.get('R130_WINDOW_BYTES', '0x1000'), 0)
GPR32 = frozenset(('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp'))

COND_JUMPS = frozenset((
    'je', 'jne', 'jz', 'jnz', 'jl', 'jle', 'jg', 'jge', 'jb', 'jbe', 'ja', 'jae',
    'js', 'jns', 'jo', 'jno', 'jp', 'jnp', 'jpe', 'jpo', 'jcxz', 'jecxz',
))
DEST_WRITERS = frozenset((
    'mov', 'add', 'lea', 'sub', 'inc', 'dec', 'and', 'or', 'xor', 'movzx',
    'movsx', 'shl', 'shr', 'sar', 'imul', 'neg', 'not', 'adc', 'sbb', 'pop',
    'xchg', 'rol', 'ror', 'movsxd',
))


def parse_imm(tok):
    """Capstone prints small immediates in decimal (add esi, 8) and large ones
    in hex (cmp esi, 0x7f3718). Accept both, plus negatives."""
    t = tok.strip()
    neg = t.startswith('-')
    if neg:
        t = t[1:]
    v = int(t, 16) if t.lower().startswith('0x') else int(t, 10)
    return -v if neg else v


def split_ops(s):
    """Split capstone operand text on top-level commas, bracket-aware."""
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur.strip())
            cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def dest_reg(mn, parts):
    if not parts or mn not in DEST_WRITERS:
        return None
    first = parts[0]
    if '[' in first or ']' in first:
        return None
    low = first.lower()
    return low if low in GPR32 else None


def lea_step(creg, mem):
    """Constant added by lea reg, [reg + N]; None if not that exact shape."""
    if '[' not in mem or ']' not in mem:
        return None
    inner = mem[mem.index('[') + 1:mem.rindex(']')].strip()
    if not inner.startswith(creg):
        return None
    rest = inner[len(creg):].strip()
    if not rest:
        return 0
    if rest[0] in '+-':
        try:
            return (-1 if rest[0] == '-' else 1) * parse_imm(rest[1:])
        except ValueError:
            return None
    return None


def main():
    pe = pefile.PE(EXE, fast_load=True)
    ib = pe.OPTIONAL_HEADER.ImageBase
    img = pe.get_memory_mapped_image()

    secs = {}
    for s in pe.sections:
        name = s.Name.rstrip(b'\x00').decode('ascii', 'replace')
        va = ib + s.VirtualAddress
        secs[name] = {'va': va, 'vsize': s.Misc_VirtualSize,
                      'raw_size': s.SizeOfRawData, 'va_end': va + s.Misc_VirtualSize}

    tsec = secs['.text']
    text_lo = tsec['va']
    code = img[text_lo - ib: text_lo - ib + tsec['raw_size']]
    text_hi = text_lo + len(code)

    def section_of(va):
        for name, s in secs.items():
            if s['va'] <= va < s['va_end']:
                return name
        return None

    def in_tables(va):
        return section_of(va) in ('.rdata', '.data')

    # ---------------- pass 1: aligned forward sweep ----------------
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.skipdata = True

    hist = collections.deque()
    hist_bytes = 0
    prev = None
    calls = []
    raw_loops = []
    insn_count = 0
    skip_count = 0
    reasons = collections.Counter()
    text_cov = text_lo

    for addr, size, mn, ops in md.disasm_lite(code, text_lo):
        insn_count += 1
        if mn == '.byte':
            skip_count += 1
            hist.clear()
            hist_bytes = 0
            prev = None
            text_cov = addr + size
            continue

        if mn == 'call' and ops and ops[0] not in '[' and not ops.startswith(
                ('dword', 'qword', 'byte', 'word')):
            if ops.startswith('0x') and int(ops, 16) == TARGET_FN:
                calls.append((addr, size))

        if (mn in COND_JUMPS and prev is not None and prev[2] == 'cmp'
                and ops.startswith('0x')):
            tgt = int(ops, 16)
            if tgt < addr:
                cmp_addr, _, _, cmp_ops = prev
                cparts = split_ops(cmp_ops)
                if len(cparts) == 2 and '[' not in cparts[0]:
                    creg = cparts[0].lower()
                    if creg in GPR32:
                        try:
                            bound = parse_imm(cparts[1])
                        except ValueError:
                            bound = None
                        if bound is not None:
                            rec = backscan(hist, creg, cmp_addr, bound, in_tables,
                                           reasons)
                            if rec is not None:
                                rec.update({'loop_head': tgt, 'cmp_addr': cmp_addr,
                                            'cmp_reg': creg,
                                            'jump_addr': addr, 'jump_size': size,
                                            'jump': mn,
                                            'loop_end_exclusive': addr + size})
                                raw_loops.append(rec)

        hist.append((addr, size, mn, ops))
        hist_bytes += size
        while hist and (addr - hist[0][0]) > WINDOW_BYTES:
            hist_bytes -= hist[0][1]
            hist.popleft()
        prev = (addr, size, mn, ops)
        text_cov = addr + size

    # ---------------- pass 2: independent byte-level T1 ----------------
    byte_calls = []
    for i in range(len(code) - 5):
        if code[i] == 0xE8:
            rel = int.from_bytes(code[i + 1:i + 5], 'little', signed=True)
            if text_lo + i + 5 + rel == TARGET_FN:
                byte_calls.append(text_lo + i)

    # ---------------- verification of each raw loop ----------------
    mv = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    mv.skipdata = False

    def verify(rec):
        """Independent confirmation, not reusing the history logic:
        decode from the mov-imm address forward to the back-edge in one go and
        require mov reg,imm ; ... ; add/lea reg,step ; ... ; cmp reg,bound ;
        backwards cond jmp to head. Also requires the mov to be at or before the
        loop head (hoisting is allowed, spanning it is not)."""
        lo = rec['loop_head']
        if rec['mov_addr'] > lo:
            return False
        seg = code[rec['mov_addr'] - text_lo: rec['jump_addr'] - text_lo + 16]
        reg = rec['cmp_reg']
        saw_mov = saw_add = saw_cmp = False
        for a, sz, mn, ops in mv.disasm_lite(seg, rec['mov_addr']):
            parts = split_ops(ops) if ops else []
            if a == rec['mov_addr']:
                if mn != 'mov' or len(parts) != 2 or parts[0].lower() != reg:
                    return False
                try:
                    if parse_imm(parts[1]) != rec['table_head']:
                        return False
                except ValueError:
                    return False
                saw_mov = True
            elif a == rec['add_addr']:
                if mn == 'add' and len(parts) == 2 and parts[0].lower() == reg:
                    try:
                        if parse_imm(parts[1]) != rec['step']:
                            return False
                    except ValueError:
                        return False
                elif mn == 'lea' and len(parts) == 2 and parts[0].lower() == reg:
                    if lea_step(reg, parts[1]) != rec['step']:
                        return False
                else:
                    return False
                saw_add = True
            elif a == rec['cmp_addr']:
                if mn != 'cmp' or len(parts) != 2 or parts[0].lower() != reg:
                    return False
                try:
                    if parse_imm(parts[1]) != rec['bound']:
                        return False
                except ValueError:
                    return False
                saw_cmp = True
            elif a == rec['jump_addr']:
                if mn != rec['jump'] or mn not in COND_JUMPS:
                    return False
                if not ops.startswith('0x') or int(ops, 16) != lo:
                    return False
                return saw_mov and saw_add and saw_cmp
            elif a > rec['jump_addr']:
                return False
        return False

    loops = []
    rejected = []
    for rec in raw_loops:
        if verify(rec):
            rec['head_section'] = section_of(rec['table_head'])
            loops.append(rec)
        else:
            rejected.append({'loop_head': hex(rec['loop_head']),
                             'table_head': hex(rec['table_head'])})

    # ---------------- report ----------------
    rep = {
        'binary': EXE,
        'image_base': hex(ib),
        'text_sha256': hashlib.sha256(code).hexdigest(),
        'text_range': [hex(text_lo), hex(text_hi)],
        'pass': {'insns_disassembled': insn_count,
                 'skipdata_bytes_consumed': skip_count,
                 'history_window_bytes': WINDOW_BYTES,
                 'text_fully_covered': text_cov == text_hi,
                 'text_coverage_end': hex(text_cov)},
        'T1': {
            'target': hex(TARGET_FN),
            'count': len(calls),
            'call_sites': [hex(a) for a, _ in calls],
            'call_sites_with_size': ['%s (len %d)' % (hex(a), s) for a, s in calls],
            'byte_scan_e8_rel32_count': len(byte_calls),
            'byte_scan_e8_rel32_sites': [hex(a) for a in byte_calls],
            'linear_pass_equals_byte_scan':
                sorted(a for a, _ in calls) == sorted(byte_calls),
            'byte_hits_rejected_as_unaligned':
                [hex(a) for a in byte_calls if a not in set(x for x, _ in calls)],
        },
    }

    pos = [l for l in loops if l['loop_head'] == LOOP_HEAD_EXPECT]
    if pos:
        h = pos[0]
        rep['T3_positive_control'] = {
            'found': True,
            'loop_head': hex(h['loop_head']),
            'table_head': hex(h['table_head']),
            'bound': hex(h['bound']),
            'step': h['step'],
            'count': h['count'],
            'mov_imm_at': hex(h['mov_addr']),
            'add_at': hex(h['add_addr']),
            'cmp_at': hex(h['cmp_addr']),
            'jump_at': hex(h['jump_addr']),
            'matches_card_hypothesis': (h['table_head'] == HEAD_EXPECT
                                        and h['bound'] == BOUND_EXPECT
                                        and h['step'] == STEP_EXPECT
                                        and h['count'] == 1),
        }
    else:
        rep['T3_positive_control'] = {'found': False}

    rep['T3'] = {
        'total_loops': len(loops),
        'rdata_head_loops': sum(1 for l in loops if l['head_section'] == '.rdata'),
        'data_head_loops': sum(1 for l in loops if l['head_section'] == '.data'),
        'other_head_loops': sum(1 for l in loops if l['head_section'] not in ('.rdata', '.data')),
        'raw_candidates': len(raw_loops),
        'rejected_by_reverify': rejected,
        'rejection_reasons': dict(reasons),
        'loops': [{'loop_head': hex(l['loop_head']),
                   'table_head': hex(l['table_head']),
                   'head_section': l['head_section'],
                   'step': l['step'], 'bound': hex(l['bound']),
                   'count': l['count'], 'jump': l['jump']}
                  for l in sorted(loops, key=lambda x: x['loop_head'])],
    }

    if pos:
        h = pos[0]
        lo_, hi_ = h['loop_head'], h['loop_end_exclusive']
        inside = [a for a, _ in calls if lo_ <= a < hi_]
        outside = [a for a, _ in calls if not (lo_ <= a < hi_)]
        rep['T2'] = {
            'loop_head': hex(lo_),
            'backedge': '%s at %s' % (h['jump'], hex(h['jump_addr'])),
            'loop_extent': [hex(lo_), hex(hi_)],
            'loop_body_bytes': hi_ - lo_,
            'call_sites_total': len(calls),
            'call_sites_inside': [hex(a) for a in inside],
            'call_sites_outside': [hex(a) for a in outside],
            'all_calls_inside': (not outside) if calls else None,
        }
    else:
        rep['T2'] = {'loop_head': hex(LOOP_HEAD_EXPECT), 'backedge_found': False,
                     'call_sites_total': len(calls)}

    rtab = [l for l in loops if l['head_section'] == '.rdata']
    t4 = [l for l in rtab if l['step'] >= 8 and l['table_head'] != HEAD_EXPECT]
    rep['T4'] = {
        'rdata_head_table_count': len(rtab),
        'stride_ge_8_excluding_0x7f3710_count': len(t4),
        'stride_ge_8_excluding_0x7f3710': [{'loop_head': hex(l['loop_head']),
                                            'table_head': hex(l['table_head']),
                                            'step': l['step'], 'count': l['count'],
                                            'bound': hex(l['bound']),
                                            'jump': l['jump']} for l in t4],
        'all_rdata_head_tables': [{'loop_head': hex(l['loop_head']),
                                   'table_head': hex(l['table_head']),
                                   'step': l['step'], 'count': l['count']}
                                  for l in sorted(rtab, key=lambda x: x['table_head'])],
    }

    # ---------------- re-derive the four hypotheses ----------------
    ent = img[HEAD_EXPECT - ib: HEAD_EXPECT - ib + 8]
    rep['table_at_0x7f3710'] = {
        'slot0_bytes': ent.hex(' '),
        'slot0_field0': hex(int.from_bytes(ent[0:4], 'little')),
        'slot0_field1': hex(int.from_bytes(ent[4:8], 'little')),
        'slot1_bytes_just_past_bound': img[HEAD_EXPECT - ib + 8:HEAD_EXPECT - ib + 16].hex(' '),
    }
    clsid_va = int.from_bytes(ent[0:4], 'little')
    rep['clsid_bytes'] = img[clsid_va - ib: clsid_va - ib + 16].hex(' ')
    dll_va = int.from_bytes(ent[4:8], 'little')
    rep['dll_string'] = img[dll_va - ib: dll_va - ib + 32].split(b'\x00')[0].decode('latin-1')

    mdx = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    rep['fn_0x6bedb0_head'] = ['%x  %s %s' % (a, mn, ops) for a, sz, mn, ops
                               in mdx.disasm_lite(img[TARGET_FN - ib:TARGET_FN - ib + 0x60],
                                                  TARGET_FN)][:22]

    with open(OUT, 'w') as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep, indent=1)[:14000])
    print('WROTE', OUT)


def backscan(hist, creg, cmp_addr, bound, in_tables, reasons=None):
    """Walk history backwards from the cmp: most recent writer of creg must be
    add/lea (the stride), the next older writer must be mov reg, imm32.

    reasons: optional Counter, incremented with the rejection cause, so the
    report can show what the filter excluded rather than only what it kept."""
    def rej(why):
        if reasons is not None:
            reasons[why] += 1
        return None

    writers = []
    for (a, sz, mn, ops) in reversed(hist):
        if a >= cmp_addr:
            continue
        parts = split_ops(ops) if ops else []
        if not parts:
            continue
        if dest_reg(mn, parts) != creg:
            continue
        writers.append((a, mn, parts))
        if len(writers) == 2:
            break
    if len(writers) < 2:
        return rej('fewer than 2 writers of the cmp register in the window')
    add_addr, add_mn, add_parts = writers[0]
    mov_addr, mov_mn, mov_parts = writers[1]

    step = None
    if add_mn == 'add' and len(add_parts) == 2:
        try:
            step = parse_imm(add_parts[1])
        except ValueError:
            step = None
    elif add_mn == 'lea' and len(add_parts) == 2:
        step = lea_step(creg, add_parts[1])
    if step is None or step == 0:
        return rej('nearest writer is not add/lea with a constant stride')
    if mov_mn != 'mov' or len(mov_parts) != 2:
        return rej('second writer is not mov reg, imm')
    try:
        mov_val = parse_imm(mov_parts[1])
    except ValueError:
        return rej('mov source is not an immediate')
    if not in_tables(mov_val):
        return rej('mov immediate does not land in .rdata/.data')
    delta = bound - mov_val
    if delta <= 0:
        return rej('bound is not above the head')
    if delta % step != 0:
        return rej('(bound - head) not divisible by stride')
    count = delta // step
    if not (1 <= count <= 4096):
        return rej('element count outside 1..4096')
    return {'table_head': mov_val, 'mov_addr': mov_addr, 'add_addr': add_addr,
            'step': step, 'bound': bound, 'count': count}


if __name__ == '__main__':
    main()
