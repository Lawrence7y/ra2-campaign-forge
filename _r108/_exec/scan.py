#!/usr/bin/env python3
"""R108-EXEC scan: build A (call targets) and C (jmp/jcc targets) sets from .text.

Streaming: disasm_lite only, bounded by instruction count per batch.
No detail=True over the whole segment (card hard constraint).
Linear sweep with explicit resync on invalid bytes; resync count is reported
so the reader can judge sweep quality.
"""
import json, sys, hashlib, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = 'ra2bench/gamemd.exe'
OUT = '_r108/_exec/'

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
sec = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
TEXT_VA = sec.VirtualAddress + IB
TEXT_SIZE = sec.Misc_VirtualSize
TEXT_END = TEXT_VA + TEXT_SIZE
with open(EXE, 'rb') as f:
    f.seek(sec.PointerToRawData)
    text_bytes = f.read(TEXT_SIZE)

JCC = {'jo','jno','jb','jae','je','jne','jbe','ja','js','jns','jp','jnp',
       'jl','jge','jle','jg','jcxz','jecxz'}
LOOPX = {'loop','loope','loopne','loopz','loopnz'}

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

calls = {}
jumps = {}
n_calls = n_calls_ext = 0
n_jumps = n_jumps_ext = 0
n_loopx = 0
resyncs = []
insn_starts = set()

mv = memoryview(text_bytes)
off = 0
BATCH = 8192
while off < len(mv):
    consumed = 0
    for (addr, size, mn, ops) in md.disasm_lite(mv[off:], TEXT_VA + off, BATCH):
        consumed += size
        insn_starts.add(addr)
        if mn == 'call':
            if ops.startswith('0x'):
                t = int(ops, 16)
                if TEXT_VA <= t < TEXT_END:
                    n_calls += 1
                    calls.setdefault(t, []).append(addr)
                else:
                    n_calls_ext += 1
        elif mn == 'jmp' or mn in JCC:
            if ops.startswith('0x'):
                t = int(ops, 16)
                if TEXT_VA <= t < TEXT_END:
                    n_jumps += 1
                    jumps.setdefault(t, []).append([addr, mn])
                else:
                    n_jumps_ext += 1
        elif mn in LOOPX:
            n_loopx += 1
    if consumed == 0:
        resyncs.append(TEXT_VA + off)
        off += 1
    else:
        off += consumed

sha = hashlib.sha256(text_bytes).hexdigest()
print('text', hex(TEXT_VA), hex(TEXT_END), 'size', TEXT_SIZE)
print('text_sha256', sha)
print('direct_calls_in_text', n_calls, '-> distinct A', len(calls), '| out-of-text call targets', n_calls_ext)
print('direct_jmp_jcc_in_text', n_jumps, '-> distinct C', len(jumps), '| out-of-text jump targets', n_jumps_ext)
print('loopx excluded', n_loopx, '| resync bytes', len(resyncs))

# cross-check: raw E8 rel32 byte anchor
e8 = []
i = text_bytes.find(b'\xe8')
while i != -1:
    if i + 5 <= len(text_bytes):
        rel = struct.unpack('<i', text_bytes[i+1:i+5])[0]
        t = TEXT_VA + i + 5 + rel
        if TEXT_VA <= t < TEXT_END:
            e8.append((TEXT_VA + i, t))
    i = text_bytes.find(b'\xe8', i + 1)
e8_targets = {t for _, t in e8}
e8_at_insn_start = [a for a, _ in e8 if a in insn_starts]
print('raw E8 bytes', len(e8), 'distinct targets', len(e8_targets),
      '| E8 at confirmed insn start', len(e8_at_insn_start))
print('A vs e8_targets: only_in_A', len(set(calls) - e8_targets),
      'only_in_e8', len(e8_targets - set(calls)))

json.dump({
    'image_base': IB, 'text_va': TEXT_VA, 'text_end': TEXT_END, 'text_size': TEXT_SIZE,
    'text_sha256': sha,
    'A': {hex(k): sorted(v) for k, v in sorted(calls.items())},
    'C': {hex(k): sorted(v) for k, v in sorted(jumps.items())},
    'counts': {
        'direct_calls_in_text': n_calls, 'A_size': len(calls),
        'call_targets_out_of_text': n_calls_ext,
        'direct_jmp_jcc_in_text': n_jumps, 'C_size': len(jumps),
        'jump_targets_out_of_text': n_jumps_ext,
        'loopx_excluded': n_loopx, 'resync_bytes': len(resyncs),
        'raw_e8_bytes': len(e8), 'raw_e8_distinct_targets': len(e8_targets),
        'e8_at_confirmed_insn_start': len(e8_at_insn_start),
        'A_minus_e8': len(set(calls) - e8_targets),
        'e8_minus_A': len(e8_targets - set(calls)),
    },
}, open(OUT + 'ac_sets.json', 'w'), indent=0)
