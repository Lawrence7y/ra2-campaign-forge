#!/usr/bin/env python3
"""R133 deepseek audit: C8 (direct callers) + C9 (arg3 at each site) + C11c.

ENVIRONMENT HAZARD (measured, reproducible):
  capstone 5.0.7  disasm_lite(buffer, addr)  with skipdata=True  SIGSEGVs when the
  supplied buffer's tail truncates an instruction (i.e. the last insn would run past
  buf_end). Reusing one Cs object across calls with skipdata also crashes.
  Mitigations used here: (1) fresh Cs per window, (2) every window is over-extended by
  16 bytes so no instruction is truncated, (3) we stop consuming at the intended end.

Sweep: continuous blocked linear sweep, block N+1 begins at last_insn_end of block N,
so the global stream is a genuine non-overlapping linear sweep with instruction
boundaries respected. Stores compact arrays (addr, size, kind) + a call/jmp target map.
"""
import json, struct, sys
from array import array
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

BIN = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
A_VA, B_VA = 0x6bedb0, 0x41c250
BLOCK = 0x8000
PAD = 16

pe = pefile.PE(BIN, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
text = next(s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text')
TEXT_VA = IB + text.VirtualAddress
TEXT_SZ = text.SizeOfRawData
with open(BIN, 'rb') as f:
    f.seek(text.PointerToRawData)
    blob = f.read(TEXT_SZ)
TEXT_END = TEXT_VA + TEXT_SZ

K_OTHER, K_CALLIMM, K_CTRL, K_DB = 0, 1, 2, 3
CTRLJMP = {'call', 'jmp', 'ret', 'retn', 'iretd', 'ljmp', 'lcall'}


def fresh():
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    md.skipdata_setup = ('db', 1, 16)
    return md


addrs, sizes, kinds = array('I'), array('H'), array('B')
ops = {}
pos = TEXT_VA
n_block = 0
while pos < TEXT_END:
    end = min(pos + BLOCK, TEXT_END)
    buf = blob[pos - TEXT_VA: min(end - TEXT_VA + PAD, TEXT_SZ)]
    md = fresh()
    last = pos
    for a, s, m, o in md.disasm_lite(buf, pos):
        if a >= end:                 # beyond intended window
            break
        if m == 'db':
            k = K_DB
        elif m in ('call', 'jmp') and o.startswith('0x'):
            k = K_CALLIMM
            ops[a] = int(o, 16)
        elif m in CTRLJMP or m.startswith('j') or m.startswith('loop'):
            k = K_CTRL
        else:
            k = K_OTHER
        addrs.append(a); sizes.append(s); kinds.append(k)
        last = a + s
    if last <= pos:                  # defensive: force progress
        addrs.append(pos); sizes.append(1); kinds.append(K_DB); last = pos + 1
    pos = last
    n_block += 1
    del md

gaps = [i for i in range(1, len(addrs)) if addrs[i - 1] + sizes[i - 1] != addrs[i]]
sweep = {'insns': len(addrs), 'blocks': n_block,
         'first': hex(addrs[0]), 'last_end': hex(addrs[-1] + sizes[-1]),
         'text_end': hex(TEXT_END), 'gap_count': len(gaps), 'contiguous': not gaps,
         'skipped_db': sum(1 for k in kinds if k == K_DB),
         'fully_covered': addrs[-1] + sizes[-1] == TEXT_END}
print(json.dumps(sweep, indent=2), flush=True)

# ---------------- C8 ----------------
hits = {A_VA: [], B_VA: []}
for a, k in zip(addrs, kinds):
    if k == K_CALLIMM and ops.get(a) in hits:
        hits[ops[a]].append(a)

def verify(va, entry):
    o = va - TEXT_VA
    op = blob[o]; rel = struct.unpack_from('<i', blob, o + 1)[0]
    return {'va': hex(va), 'opcode': hex(op), 'is_e8_e9': op in (0xE8, 0xE9),
            'lands': ((va + 5 + rel) & 0xFFFFFFFF) == entry}

C8 = {'A_count': len(hits[A_VA]), 'A_sites': [hex(x) for x in hits[A_VA]],
      'B_count': len(hits[B_VA]), 'B_sites': [hex(x) for x in hits[B_VA]],
      'total': len(hits[A_VA]) + len(hits[B_VA]),
      'verify': {'A': [verify(v, A_VA) for v in hits[A_VA]],
                 'B': [verify(v, B_VA) for v in hits[B_VA]]}}

# raw-byte cross check
raw = {A_VA: [], B_VA: []}
for i in range(len(blob) - 4):
    if blob[i] in (0xE8, 0xE9):
        va = TEXT_VA + i
        t = (va + 5 + struct.unpack_from('<i', blob, i + 1)[0]) & 0xFFFFFFFF
        if t in raw:
            raw[t].append(va)
C8['raw_scan'] = {hex(k): [hex(x) for x in v] for k, v in raw.items()}
C8['raw_agrees'] = {hex(k): sorted(raw[k]) == sorted(hits[k]) for k in raw}

# ---------------- C9: arg3 at each site ----------------
idx = {a: i for i, a in enumerate(addrs)}
sites = sorted(hits[A_VA] + hits[B_VA])

# we need op_str only near call sites: re-decode a 0xc0-byte window ending at the call
def window_before_call(call_va):
    start = call_va - 0xC0
    buf = blob[start - TEXT_VA: call_va - TEXT_VA + PAD]
    md = fresh()
    return [(a, s, m, o) for a, s, m, o in md.disasm_lite(buf, start) if a < call_va]

C9 = []
for site in sites:
    # --- primary: backward walk on the global sweep index, enforcing contiguity ---
    i = idx[site]
    walk = []
    j = i - 1
    stop = 'start-of-text'
    while j >= 0:
        if addrs[j] + sizes[j] != addrs[j + 1]:
            stop = 'gap'
            break
        walk.append(j)
        if kinds[j] in (K_CTRL, K_CALLIMM):   # control transfer ends the tail
            stop = 'control-transfer'
            break
        j -= 1
    tail = walk                              # NEAREST-FIRST order (j descending)
    if tail:
        lo = addrs[tail[-1]]                 # furthest insn of the tail = a real boundary
        buf = blob[lo - TEXT_VA: site - TEXT_VA + PAD]
        md = fresh()
        dec = {a: (s, m, o) for a, s, m, o in md.disasm_lite(buf, lo) if a < site}
    else:
        dec = {}
    pushlist = []
    for j in tail:                            # already nearest-first
        a = addrs[j]
        if a in dec and dec[a][1] == 'push':
            pushlist.append({'va': hex(a), 'off_from_site': a - site, 'op': dec[a][2]})
    nearest3 = pushlist[:3]
    arg3 = nearest3[2] if len(nearest3) >= 3 else None

    # --- control: local window decode, verifying it agrees ---
    loc = window_before_call(site)
    locpush = [{'va': hex(a), 'op': o} for a, s, m, o in reversed(loc) if m == 'push'][:3]

    C9.append({'site': hex(site), 'target': hex(A_VA if site in hits[A_VA] else B_VA),
               'walk_stop_reason': stop, 'tail_len': len(tail),
               'tail_insns': len(tail),
               'pushes_in_tail_nearest_first': pushlist,
               'nearest_three': nearest3,
               'arg3': arg3['op'] if arg3 else None,
               'arg3_offset_from_site': arg3['off_from_site'] if arg3 else None,
               'arg2': nearest3[1]['op'] if len(nearest3) > 1 else None,
               'arg1': nearest3[0]['op'] if len(nearest3) > 0 else None,
               'local_window_nearest_three': locpush,
               'local_agrees': ([x['op'] for x in locpush] == [x['op'] for x in nearest3]),
               })

res = {'sweep': sweep, 'C8': C8, 'C9': C9}

whole = bytes(pe.get_memory_mapped_image())
def imm32s(val, hay, base):
    pat = struct.pack('<I', val); out = []; i = hay.find(pat)
    while i >= 0:
        out.append(hex(base + i)); i = hay.find(pat, i + 1)
    return out
res['C11c'] = {'A_imm32_in_text': imm32s(A_VA, blob, TEXT_VA),
               'B_imm32_in_text': imm32s(B_VA, blob, TEXT_VA),
               'A_imm32_in_image': imm32s(A_VA, whole, IB),
               'B_imm32_in_image': imm32s(B_VA, whole, IB)}

print(json.dumps({'C8': res['C8'], 'C9': res['C9'], 'C11c': res['C11c']}, indent=2))
json.dump(res, open('/home/t628/projects/ra2-campaign-forge/_r133/sub_deepseek/r133ds2_callers_arg3.json', 'w'), indent=2)
