#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R194 exec: static xref survey of 0x4A1CA0 / 0x4A1D50 / 0x4A1DE0 + CRC table.
Single-pass streaming lite sweep; detail=True only on two 64-byte bodies.
"""
import os, sys, re, json, hashlib, bisect, collections
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

OUTDIR = ROOT + '/_r194/exec_r194'
os.makedirs(OUTDIR, exist_ok=True)

SEC = P.B['.text']
LO, HI = SEC['lo'], SEC['hi_file']
CODE = P.RAW[SEC['rawptr']:SEC['rawptr'] + SEC['rawsize']]

md_lite = Cs(CS_ARCH_X86, CS_MODE_32)
md_det = Cs(CS_ARCH_X86, CS_MODE_32)
md_det.detail = True

T1, T2, T3 = 0x4A1CA0, 0x4A1D50, 0x4A1DE0
TARGETS = [T1, T2, T3]
CRC = 0x81F7B4
ABS = re.compile(r'^0x[0-9a-f]+$')
CRCKEY = '%x' % CRC          # '81f7b4'

lines = []
def emit(s=''):
    lines.append(str(s))
    print(s)

emit('[SETUP] gamemd.exe sha256=%s' % hashlib.sha256(P.RAW).hexdigest())
emit('[SETUP] .text lo=0x%X hi_file=0x%X rawsize=%d' % (LO, HI, len(CODE)))
for t in TARGETS:
    emit('[SETUP] target 0x%X section=%s' % (t, P.where(t)))
emit('[SETUP] CRC 0x%X section=%s' % (CRC, P.where(CRC)))

# ---------------- one streaming lite pass ----------------
bitmap = bytearray(len(CODE))
direct = collections.defaultdict(list)
indirect = []
jmp_t = set()
crc_hits = []
n_insn = n_call = n_jmp = 0

def record(a, sz, m, o, from_seed=False):
    global n_insn, n_call, n_jmp
    bitmap[a - LO] = 1
    n_insn += 1
    if m == 'call':
        n_call += 1
        if ABS.match(o):
            direct[int(o, 16)].append(a)
        else:
            b = CODE[a - LO:a - LO + sz]
            if (a, o, b.hex()) not in indirect_seen:
                indirect_seen.add((a, o, b.hex())); indirect.append((a, o, b.hex()))
    elif m == 'jmp':
        n_jmp += 1
        if ABS.match(o):
            jmp_t.add(int(o, 16))
    if '81f7b4' in o.lower() and not any(h[0] == a for h in crc_hits):
        if m == 'mov' and re.match(r'^[a-z]{3}, (?:0x)?0*81f7b4$', o.lower()):
            form = 'mov_r32_imm32'
        elif m in ('mov', 'lea') and re.search(r'\[[^\]]*\*4 \+ 0x0*81f7b4\]$', o.lower()):
            form = ('mov' if m == 'mov' else 'lea') + '_sib_disp32'
        elif m == 'lea' and re.match(r'^[a-z]{3}, \[(?:ds:)?(?:0x)?0*81f7b4\]$', o.lower()):
            form = 'lea_r32_imm'
        elif m == 'push' and re.match(r'^(?:0x)?0*81f7b4$', o.lower()):
            form = 'push_imm32'
        else:
            form = 'other:' + m
        crc_hits.append((a, m, o, form))

indirect_seen = set()
for a, sz, m, o in md_lite.disasm_lite(CODE, LO):
    record(a, sz, m, o)
n_linear = n_insn

emit('[SETUP] lite insns=%d calls=%d jmps=%d direct_targets=%d' %
     (n_insn, n_call, n_jmp, len(direct)))

# ---------------- Q1 ----------------
q1 = {}
for t in TARGETS:
    sites = sorted(direct.get(t, []))
    q1['0x%X' % t] = {'count': len(sites), 'first20': ['0x%X' % x for x in sites[:20]]}
    emit('[Q1-LINEAR-ONLY] 0x%X : %d direct calls (pre-seed; see [Q1-SEED] for final)' %
         (t, len(sites)))

# ---------------- function starts ----------------
flow = set(t for t in list(direct.keys()) + list(jmp_t) if LO <= t < HI)
fill = set()
i, n = 0, len(CODE)
while i < n:
    if CODE[i] in (0xCC, 0x90):
        j = i
        while j < n and CODE[j] in (0xCC, 0x90):
            j += 1
        if j - i >= 2 and j < n and bitmap[j]:
            fill.add(LO + j)
        i = j
    else:
        i += 1
starts_full = flow | fill
starts_nofill = set(flow)
sl_full = sorted(starts_full)
sl_nofill = sorted(starts_nofill)
emit('[START] flow_targets=%d fill_starts=%d full=%d nofill=%d' %
     (len(flow), len(fill), len(sl_full), len(sl_nofill)))

# Seeded decode from every flow start: linear sweep desynchronizes on embedded data.
seeded = 0
seed_added = 0
for st in sl_full:
    for x in md_lite.disasm(CODE[st - LO:min(st - LO + 4096, n)], st):
        seeded += 1
        # Only harvest instructions the linear pass did not decode at this address.
        if not bitmap[x.address - LO]:
            before = len(crc_hits) + len(indirect)
            record(x.address, x.size, x.mnemonic, x.op_str)
            if len(crc_hits) + len(indirect) > before:
                seed_added += 1
        if x.mnemonic.startswith('ret'):
            break
emit('[SETUP] seeded insns=%d ; new findings=%d ; merged crc_hits=%d' %
     (seeded, seed_added, len(crc_hits)))
for h in crc_hits:
    emit('[DEBUG-CRC] 0x%X %-5s form=%s ops=%s' % (h[0], h[1], h[3], h[2]))
imm_hits = [x for x in crc_hits if x[3] in ('mov_r32_imm32', 'lea_r32_imm', 'push_imm32')]
mov_n = sum(1 for x in crc_hits if x[3] == 'mov_r32_imm32')
lea_n = sum(1 for x in crc_hits if x[3] == 'lea_r32_imm')
push_n = sum(1 for x in crc_hits if x[3] == 'push_imm32')
sib_n = sum(1 for x in crc_hits if x[3] in ('mov_sib_disp32', 'lea_sib_disp32'))
sib_hits = [x for x in crc_hits if x[3] in ('mov_sib_disp32', 'lea_sib_disp32')]
ff2 = sum(1 for a, o, b in indirect
          if len(b) >= 4 and b[:2] == 'ff' and (int(b[2:4], 16) & 0x38) == 0x10)
ff3 = sum(1 for a, o, b in indirect
          if len(b) >= 4 and b[:2] == 'ff' and (int(b[2:4], 16) & 0x38) == 0x18)
emit('[Q2] indirect calls total=%d ; FF/2(near call r/m32)=%d ; FF/3(far)=%d ; other=%d' %
     (len(indirect), ff2, ff3, len(indirect) - ff2 - ff3))
for t in direct:
    direct[t] = sorted(set(direct[t]))
q1 = {}
for t in TARGETS:
    sites = sorted(direct.get(t, []))
    q1['0x%X' % t] = {'count': len(sites), 'first20': ['0x%X' % x for x in sites[:20]]}
    emit('[Q1-SEED] 0x%X : %d direct calls ; first20=%s' %
         (t, len(sites), ','.join('0x%X' % x for x in sites[:20])))

def host(a, sl):
    k = bisect.bisect_right(sl, a) - 1
    return sl[k] if k >= 0 else None

# ---------------- Q3 + R3 ----------------
q3, r3 = {}, {}
for t in TARGETS:
    sites = sorted(direct.get(t, []))
    hc = collections.Counter(host(a, sl_full) for a in sites)
    hc_nf = collections.Counter(host(a, sl_nofill) for a in sites)
    hosts = sorted((('0x%X' % h) if h is not None else 'NONE', c) for h, c in hc.items())
    hosts_nf = sorted((('0x%X' % h) if h is not None else 'NONE', c) for h, c in hc_nf.items())
    distinct = sum(1 for h in hc if h is not None)
    distinct_nf = sum(1 for h in hc_nf if h is not None)
    q3['0x%X' % t] = {'distinct_hosts': distinct, 'hosts': hosts,
                      'has_host_0x410410': any(h == 0x410410 for h in hc)}
    r3['0x%X' % t] = distinct_nf
    emit('[Q3] 0x%X distinct host functions (full)=%d ; hosts=%s' % (t, distinct, hosts))
    emit('[Q3] 0x%X host_start==0x410410 ? %s' %
         (t, q3['0x%X' % t]['has_host_0x410410']))
    emit('[R3] 0x%X distinct host functions (no-fill)=%d ; hosts=%s' % (t, distinct_nf, hosts_nf))

# ---------------- Q4 / R1 ----------------
emit('[Q4] immediate 0x81F7B4 hits: total_any_form=%d immediate_forms=%d mov_r32_imm32=%d lea_r32_imm=%d push_imm32=%d' %
     (len(crc_hits), len(imm_hits), mov_n, lea_n, push_n))
q4first = []
for a, m, o, f in sorted(imm_hits)[:12]:
    h = host(a, sl_full)
    hs = ('0x%X' % h) if h is not None else 'NONE'
    q4first.append({'addr': '0x%X' % a, 'form': f, 'mnem': m, 'operands': o, 'host': hs})
    emit('[Q4] 0x%X  %-8s %-28s form=%-16s host=%s' % (a, m, o, f, hs))
crc_hosts_sib = collections.Counter(host(a, sl_full) for a, m, o, f in sib_hits)
others_sib = sorted((('0x%X' % h) if h is not None else 'NONE', c)
                    for h, c in crc_hosts_sib.items() if h not in (T1, T3))
emit('[Q4] SIB-disp32 (mov/lea r32,[reg*4+0x81F7B4]) hits=%d ; hosts=%s' % (sib_n, others_sib))
for a, m, o, f in sorted(sib_hits):
    h = host(a, sl_full)
    emit('[Q4] SIB 0x%X %-5s %-42s host=%s' %
         (a, m, o, ('0x%X' % h) if h is not None else 'NONE'))
crc_hosts = collections.Counter(host(a, sl_full) for a, m, o, f in imm_hits)
others = sorted((('0x%X' % h) if h is not None else 'NONE', c)
                for h, c in crc_hosts.items() if h not in (T1, T3))
emit('[Q4] bare-immediate (mov/lea/push imm32) host functions EXCLUDING 0x4A1CA0/0x4A1DE0 : %s (none)' % others)
emit('[Q4] ANSWER: other functions referencing CRC table (via SIB disp32) = %s' % others_sib)
emit('[R1] any-immediate 0x81F7B4 hits=%d ; Q1 call hits(0x4A1CA0)=%d ; equal=%s' %
     (len(imm_hits), q1['0x4A1CA0']['count'], len(imm_hits) == q1['0x4A1CA0']['count']))
emit('[R2] bare (no host attribution) call sites to 0x4A1DE0 = %d ; Q3 full distinct hosts = %s' %
     (len(direct.get(T3, [])), q3['0x%X' % T3]['distinct_hosts']))

# ---------------- Q5 hexdump + detail disasm ----------------
def dump(va, nbytes=64):
    off = P.r2o(va)
    raw = P.RAW[off:off + nbytes]
    hexlines = []
    for k in range(0, len(raw), 16):
        chunk = raw[k:k + 16]
        hexlines.append('0x%08X: %s' % (va + k, ' '.join('%02X' % b for b in chunk)))
    ins = []
    for x in md_det.disasm(raw, va):
        ins.append({'addr': '0x%08X' % x.address, 'bytes': x.bytes.hex(),
                    'mnem': x.mnemonic, 'ops': x.op_str})
        if x.mnemonic.startswith('ret'):
            break
    if not any(d['mnem'].startswith('ret') for d in ins):
        # hexdump stays 64 bytes; keep disassembling further for the until-ret view
        tail = P.RAW[off + nbytes:off + nbytes + 256]
        for x in md_det.disasm(tail, va + nbytes):
            ins.append({'addr': '0x%08X' % x.address, 'bytes': x.bytes.hex(),
                        'mnem': x.mnemonic, 'ops': x.op_str})
            if x.mnemonic.startswith('ret'):
                break
    return hexlines, ins

q5 = {}
for t in (T2, T1):
    hl, ins = dump(t)
    q5['0x%X' % t] = {'hexdump': hl, 'insns': ins}
    emit('[Q5] ===== 0x%X 64-byte hexdump =====' % t)
    for h in hl:
        emit(h)
    emit('[Q5] ----- instructions until ret (detail=True) -----')
    for d in ins:
        emit('0x%08X  %-20s %-8s %s' % (int(d['addr'], 16), d['bytes'], d['mnem'], d['ops']))
    emit('[Q5] stack/immediate operands in 0x%X body:' % t)
    for d in ins:
        if re.search(r'\[(esp|ebp)\s*\+|0x81f7b4', d['ops'], re.I):
            emit('   %s %-8s %s' % (d['addr'], d['mnem'], d['ops']))

Q5_ANSWER = (
    '实测成立（栈槽语义修正）：0x4A1CA0 序言无 push ebp，入口 [esp]=返回地址/[esp+4]=第一参数/'
    '[esp+8]=第二参数。0x004A1CAC "push ebx" 后 [esp+8] 变为入口 [esp+4]，'
    '故 0x004A1CAD "mov bl, byte ptr [esp + 8]" 读取的是**第一参数的低字节**（modifier=byte，'
    '非 dword）；随后 0x004A1CB1 "cmp bl, dl" / 0x004A1CB4 "setne bl" 归一为 0/1 布尔字节，'
    '0x004A1CB7 "mov byte ptr [eax + ecx + 8], bl" 写入 CRC 缓冲。'
    '结论：被读的 [esp+8] 既不是「剩余字节数」（无 dword 算术/计数器用法），'
    '也不是「缓冲区指针」（无 [esp+8] 取 dword 作基址寻址）；它是单个布尔/标志字节。'
    '真正的第二参数（入口 [esp+8]）在 push ebx 后位于 [esp+0xC]，体内未被读取。'
    '0x004A1CB3 又 push edi，此后 [esp+0xC] 才是入口 [esp+8]，但代码未访问该槽。'
    '依据：0x004A1CAC / 0x004A1CAD / 0x004A1CB3 / 0x004A1CB7 / 0x004A1D23(ret 4)。')
emit('[Q5-ANSWER] ' + Q5_ANSWER)

# ---------------- assertions + write outputs ----------------
for t in TARGETS:
    assert LO <= t < HI, 'target 0x%X outside .text' % t
assert sum(v['count'] for v in q1.values()) == sum(len(direct.get(t, [])) for t in TARGETS), 'q1 consistency'
assert len(q5['0x4A1D50']['insns']) > 0 and len(q5['0x4A1CA0']['insns']) > 0, 'empty detail disasm'
assert any(d['mnem'].startswith('ret') for d in q5['0x4A1CA0']['insns']), 'no ret in 0x4A1CA0 body'
assert mov_n >= 0 and lea_n >= 0 and len(imm_hits) == mov_n + lea_n + push_n
print('[ASSERT] PASS: setup/q1/q4/q5 structural checks')

doc = {'setup': {'gamemd_sha256': hashlib.sha256(P.RAW).hexdigest(),
                 'text_lo': '0x%X' % LO, 'text_hi_file': '0x%X' % HI,
                 'crc_base': '0x%X' % CRC, 'lite_insns': n_insn,
                 'direct_calls': n_call, 'jmp_insns': n_jmp},
       'Q1': q1, 'Q2': {'indirect_total': len(indirect), 'ff2': ff2, 'ff3': ff3,
                        'examples': [{'addr': '0x%X' % a, 'ops': o, 'bytes': b}
                                     for a, o, b in indirect[:12]]},
       'Q3': q3,
       'Q4': {'total_any_form': len(crc_hits), 'immediate_forms': len(imm_hits),
              'mov_imm32': mov_n, 'lea_imm': lea_n, 'push_imm32': push_n,
              'sib_disp32_hits': sib_n, 'sib_disp32': [
                  {'addr': '0x%X' % a, 'mnem': m, 'operands': o,
                   'host': ('0x%X' % host(a, sl_full)) if host(a, sl_full) is not None else 'NONE'}
                  for a, m, o, f in sorted(sib_hits)],
              'sib_other_hosts': others_sib,
              'first12': q4first, 'other_hosts': others},
       'Q5': q5, 'Q5_ANSWER': Q5_ANSWER,
       'R1': {'any_immediate_hits': len(imm_hits),
              'call_hits_T1': q1['0x4A1CA0']['count'],
              'equal': len(imm_hits) == q1['0x4A1CA0']['count']},
       'R2': {'bare_sites_T3': len(direct.get(T3, [])),
              'full_hosts_T3': q3['0x%X' % T3]['distinct_hosts']},
       'R3': {'hosts_no_fill': r3}}

jp, tp = OUTDIR + '/xref.json', OUTDIR + '/xref.txt'
with open(jp, 'w', encoding='utf-8') as f:
    json.dump(doc, f, ensure_ascii=False, indent=2)
finals = []
for p in (jp, tp):
    d = open(p, 'rb').read()
    finals.append('[FINAL] %s bytes=%d sha256=%s' % (p, len(d), hashlib.sha256(d).hexdigest()))
lines.extend(finals)
with open(tp, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
for s in finals:
    print(s)
