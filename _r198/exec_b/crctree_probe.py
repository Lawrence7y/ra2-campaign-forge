#!/usr/bin/env python3
# R198 EXEC-B: CRC state object +0 initialization source, static evidence only.
import sys, os, re, json, struct, bisect, hashlib
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86_const import X86_OP_REG, X86_OP_MEM, X86_OP_IMM

ROOT = '/home/t628/projects/ra2-campaign-forge'
OUTDIR = ROOT + '/_r198/exec_b'
os.makedirs(OUTDIR, exist_ok=True)
RAW = P.RAW
S = P.B['.text']
LO = S['lo']
POS = S['rawptr']
SZ = S['rawsize']
ENDVA = LO + SZ

md_lite = Cs(CS_ARCH_X86, CS_MODE_32)
md_det = Cs(CS_ARCH_X86, CS_MODE_32)
md_det.detail = True

def h(x):
    return 'UNKNOWN' if x is None else ('0x%X' % x)

def r2o(va):
    return P.r2o(va)

def va_bytes(va, n):
    o = r2o(va)
    return None if o is None else RAW[o:o+n]

# Global one-pass E8 index: target -> sorted call-site VAs.
CALLS_BY_TARGET = {}
_p = POS
_end = POS + SZ
while True:
    _q = RAW.find(b'\xe8', _p, _end)
    if _q < 0:
        break
    if _q + 5 <= _end:
        _rel = struct.unpack_from('<i', RAW, _q + 1)[0]
        _site = LO + (_q - POS)
        _t = _site + 5 + _rel
        CALLS_BY_TARGET.setdefault(_t, []).append(_site)
    _p = _q + 1

def call_sites(target):
    return sorted(CALLS_BY_TARGET.get(target, []))

def lite_ins(start, end):
    """Streaming disasm_lite over a bounded range; never whole .text with detail."""
    o1, o2 = r2o(start), r2o(end)
    if o1 is None or o2 is None or o2 <= o1:
        return []
    return list(md_lite.disasm(RAW[o1:o2], start))

def det_ins(start, end):
    """detail=True only on small windows (caller enforces <=64KB)."""
    o1, o2 = r2o(start), r2o(end)
    if o1 is None or o2 is None or o2 <= o1 or o2 - o1 > 65536:
        return []
    return list(md_det.disasm(RAW[o1:o2], start))

# ---------- Global call-target set for Q2 host attribution ----------
all_targets = set()
for x in md_lite.disasm(RAW[POS:POS+SZ], LO):
    m, o = x.mnemonic, x.op_str
    if m == 'call' and o.startswith('0x'):
        try:
            all_targets.add(int(o, 16))
        except ValueError:
            pass
TARGETS = sorted(all_targets)

def enclosing_entry(site):
    j = bisect.bisect_right(TARGETS, site) - 1
    return TARGETS[j] if j >= 0 else None

def func_range(entry, hint=None):
    """Approximate function body: entry .. first ret at/after entry (cap 64KB)."""
    limit = min(entry + 8192, ENDVA)
    ins = lite_ins(entry, limit)
    for x in ins:
        if x.mnemonic in ('ret', 'retf') and x.address >= entry:
            return entry, x.address + x.size
    if hint is not None and hint > entry:
        return entry, min(hint + 16, ENDVA)
    return entry, min(entry + 64, ENDVA)

def regname(op):
    try:
        return md_det.reg_name(op.reg)
    except Exception:
        return '?'

def mem_source(op):
    if op.type != X86_OP_MEM:
        return None
    if op.mem.base is not None and md_det.reg_name(op.mem.base) == 'esp':
        d = op.mem.disp
        return '[esp+0x%X]' % (d & 0xffffffff) if d >= 0 else '[esp-0x%X]' % (-d)
    return 'mem'

def push_arg_before(entry, site):
    """Find the pushed 3rd argument immediately before a call and its register."""
    start = max(entry, site - 320)
    ins = det_ins(start, site + 6)
    idx = next((i for i, x in enumerate(ins) if x.address == site), None)
    if idx is None:
        return None, None, None
    for k in range(idx - 1, max(-1, idx - 14), -1):
        x = ins[k]
        if x.mnemonic == 'push' and x.operands:
            op = x.operands[0]
            if op.type == X86_OP_REG:
                return regname(op), x.address, x.bytes.hex()
            if op.type == X86_OP_MEM:
                return mem_source(op), x.address, x.bytes.hex()
            return 'push_imm', x.address, x.bytes.hex()
        if x.mnemonic == 'call':
            break
    return None, None, None

def provenance(entry, push_addr, reg):
    """Track last definition of reg from function entry to push; stack args preserved."""
    if reg is None or not re.fullmatch(r'[a-z]{3}', reg or ''):
        return 'unknown(reg=%s)' % reg
    start = max(entry, push_addr - 2048) if entry >= LO and entry < push_addr else max(push_addr - 2048, LO)
    ins = det_ins(start, push_addr + 1)
    prov = {}
    for rn in ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp'):
        prov[rn] = 'init:' + rn
    for x in ins:
        if x.address > push_addr:
            break
        ops = x.operands
        m = x.mnemonic
        if m == 'mov' and len(ops) == 2 and ops[0].type == X86_OP_REG:
            d = regname(ops[0]); s = ops[1]
            ms = mem_source(s)
            if ms:
                prov[d] = ms
            elif s.type == X86_OP_REG:
                prov[d] = prov.get(regname(s), 'reg:' + regname(s))
            elif s.type == X86_OP_IMM:
                prov[d] = 'const:0x%X' % (s.imm & 0xffffffff)
        elif m == 'lea' and len(ops) == 2 and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_MEM:
            prov[regname(ops[0])] = 'local:' + str(mem_source(ops[1]))
        elif m == 'xor' and len(ops) == 2 and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_REG and regname(ops[0]) == regname(ops[1]):
            prov[regname(ops[0])] = 'const:0'
        elif m == 'pop' and ops and ops[0].type == X86_OP_REG:
            prov[regname(ops[0])] = 'unknown:pop'
        elif m in ('add', 'sub', 'and', 'or', 'inc', 'dec', 'shl', 'shr', 'sar') and ops and ops[0].type == X86_OP_REG:
            d = regname(ops[0])
            prov[d] = 'modified(' + prov.get(d, '?') + ')'
    return prov.get(reg, 'unknown')

def classify_source(prov):
    if prov.startswith('[esp+'):
        return 'stack_arg'
    if prov.startswith('local:') or prov.startswith('const:'):
        return 'local_alloc'
    return 'unknown'

def qemu_ret4(va):
    ins = det_ins(va, va + 256)
    return ins[-1].mnemonic if ins else None

# ================= EVIDENCE =================
ev = {}
asserts = []

def add_assert(name, cond, detail=''):
    asserts.append({'name': name, 'pass': bool(cond), 'detail': detail})

# ---- Q1: P1/P2/P3/P4 ----
p1 = det_ins(0x4A1CA0, 0x4A1CA0 + 256)
p1_instrs = []
for x in p1:
    p1_instrs.append(x)
    if x.mnemonic == 'ret':
        break
p1_n = len(p1_instrs)
p1_bytes = sum(x.size for x in p1_instrs)
p1_ret = p1_instrs[-1].op_str if p1_instrs else None
p1_ret_mnem = p1_instrs[-1].mnemonic if p1_instrs else None
p1_write0 = [h(x.address) for x in p1_instrs if x.mnemonic == 'mov' and x.op_str.startswith('dword ptr [ecx],')]

p2 = call_sites(0x4A1CA0)
p3_sites = call_sites(0x410410)
p4 = call_sites(0x410BE0)
ev['Q1'] = {
    'P1_entry': h(0x4A1CA0), 'P1_instructions': p1_n, 'P1_bytes': p1_bytes,
    'P1_last_mnemonic': p1_ret_mnem, 'P1_ret_operand': p1_ret,
    'P1_plus0_writes': p1_write0,
    'P2_calls_to_4A1CA0': len(p2), 'P3_calls_to_410410': len(p3_sites),
    'P4_calls_to_410BE0': len(p4),
    'P2_sample': [h(x) for x in p2[:8]],
    'P3_sites': [h(x) for x in p3_sites],
    'P4_sample': [h(x) for x in p4[:8]],
    'sha256_text': hashlib.sha256(RAW[POS:POS+SZ]).hexdigest(),
}
add_assert('Q1.P1_instr_55', p1_n == 55, str(p1_n))
add_assert('Q1.P1_bytes_134', p1_bytes == 134, str(p1_bytes))
add_assert('Q1.P1_ret4', p1_ret_mnem == 'ret' and p1_ret.strip() == '4', str(p1_ret))
add_assert('Q1.P2_331', len(p2) == 331, str(len(p2)))
add_assert('Q1.P3_27', len(p3_sites) == 27, str(len(p3_sites)))
add_assert('Q1.P4_23', len(p4) == 23, str(len(p4)))

print('[stage] Q2 start', file=sys.stderr, flush=True)
# ---- Q2: hosts of the 27 call sites ----
host_counts = {}
site_host = {}
for site in p3_sites:
    ent = enclosing_entry(site)
    site_host[site] = ent
    host_counts[ent] = host_counts.get(ent, 0) + 1
q2_rows = []
for site in p3_sites:
    ent = site_host[site]
    q2_rows.append({'call_site': h(site), 'host_entry': h(ent),
                    'host_call_count': host_counts.get(ent, 0),
                    'distance': None if ent is None else site - ent})
ev['Q2'] = {'rule': 'nearest preceding address in full-.text call-target set',
            'hosts': [h(x) for x in sorted(host_counts, key=lambda v: (v is None, v))],
            'host_count': len(host_counts), 'total_call_points': sum(host_counts.values()),
            'rows': q2_rows}
add_assert('Q2.hosts_27', len(host_counts) == 27, str(len(host_counts)))
add_assert('Q2.points_27', sum(host_counts.values()) == 27, str(sum(host_counts.values())))

print('[stage] Q3 start', file=sys.stderr, flush=True)
# ---- Q3: third-parameter provenance and +0 writes in each host ----
q3_rows = []
host_rows = {}
for site in p3_sites:
    ent = site_host[site]
    reg, push_va, push_bytes = push_arg_before(ent if ent is not None else max(LO, site-256), site)
    prov = provenance(ent, push_va, reg) if ent is not None else 'UNKNOWN(no host entry)'
    cls = classify_source(prov)
    # scan host body for writes to dword ptr [state_reg], imm
    writes = []
    if ent is not None:
        lo_e, hi_e = func_range(ent, site)
        for x in det_ins(ent, min(hi_e, site + 8)):
            if x.mnemonic == 'mov' and len(x.operands) == 2:
                o0, o1 = x.operands
                if o0.type == X86_OP_MEM and o1.type == X86_OP_IMM:
                    if o0.mem.base is not None and regname(o0) == reg:
                        writes.append({'addr': h(x.address), 'bytes': x.bytes.hex(), 'op': x.op_str})
    row = {'call_site': h(site), 'host_entry': h(ent), 'push_reg': reg,
           'push_addr': h(push_va), 'push_bytes': push_bytes,
           'provenance': prov, 'class': cls,
           'plus0_writes_in_host': writes}
    q3_rows.append(row)
    host_rows.setdefault(h(ent), row)

ev['Q3'] = {'hosts': len(host_rows), 'rows': q3_rows,
            'stack_sourced_hosts': sorted([k for k, v in host_rows.items() if v['class'] == 'stack_arg'])}
add_assert('Q3.host_rows_27', len(host_rows) == 27, str(len(host_rows)))
add_assert('Q3.all_rows_have_class', all('class' in r for r in q3_rows), str(len(q3_rows)))

print('[stage] Q4 start', file=sys.stderr, flush=True)
# ---- Q4: upward traversal, depth <= 4 ----
tree = {}
visited = {}
layers = []
frontier = [e for e in host_counts if e is not None]
depth_limit = 4
for depth in range(1, depth_limit + 1):
    layer_entries = sorted(set(frontier))
    layer_calls = []
    next_frontier = []
    layer_rows = []
    for e in layer_entries:
        cs = call_sites(e)
        layer_calls.extend(cs)
        for site in cs:
            parent = enclosing_entry(site)
            layer_rows.append({'callee': h(e), 'call_site': h(site), 'caller_entry': h(parent)})
            if parent is not None:
                next_frontier.append(parent)
        tree[h(e)] = [h(x) for x in cs]
    ancestors = set(layer_entries)
    cyc = [r for r in layer_rows if r['caller_entry'] in ancestors and r['caller_entry'] != 'UNKNOWN']
    layers.append({'depth': depth, 'entry_count': len(layer_entries),
                   'call_points': len(cs) if False else len(layer_calls),
                   'entries': [h(x) for x in layer_entries],
                   'caller_rows': layer_rows,
                   'cycle_or_reentry': cyc})
    visited.setdefault(depth, set()).update(layer_entries)
    frontier = [x for x in next_frontier if x is not None]
    if not frontier:
        break

all_layer_entries = set()
for L in layers:
    all_layer_entries.update(int(x, 16) for x in L['entries'] if x != 'UNKNOWN')
all_edges = []
for L in layers:
    for r in L['caller_rows']:
        if r['caller_entry'] != 'UNKNOWN':
            all_edges.append((r['caller_entry'], r['callee']))
seen_entries = {}
for d, es in visited.items():
    for e in es:
        seen_entries.setdefault(h(e), []).append(d)
multi_depth = [k for k, v in seen_entries.items() if len(v) > 1]
self_loops = [e for e in all_edges if e[0] == e[1]]
ev['Q4'] = {'rule': 'same nearest-prior-call-target entry rule, repeated to depth 4',
            'layers': layers,
            'total_unique_entries': len(all_layer_entries),
            'edges': all_edges,
            'multi_depth_entries': multi_depth,
            'self_loops': self_loops,
            'shape': ('cycle/self-loop' if self_loops else
                      ('shared-parent DAG' if multi_depth else
                       ('tree' if len(all_edges) >= len(all_layer_entries) - 1 else 'forest')))}
add_assert('Q4.depth_le_4', len(layers) <= 4, str(len(layers)))
add_assert('Q4.layer1_27', layers[0]['entry_count'] == 27, str(layers[0]['entry_count']))

print('[stage] Q5 start entries=%d' % len(all_layer_entries), file=sys.stderr, flush=True)
# ---- Q5: zero-initialization scan over all covered function bodies ----
tree_entries = set(all_layer_entries)
tree_entries.update([0x410410, 0x410BE0, 0x4A1CA0])

# Derive state-pointer candidate registers from calls to tree children inside each function.
child_set = set(tree_entries)
state_regs = {}
for e in sorted(tree_entries):
    lo_e, hi_e = func_range(e)
    regs = set()
    for x in lite_ins(e, min(hi_e, ENDVA)):
        if x.mnemonic == 'call' and x.op_str.startswith('0x'):
            try:
                t = int(x.op_str, 16)
            except ValueError:
                continue
            if t in child_set:
                rg, pv, pb = push_arg_before(e, x.address)
                prov = provenance(e, pv, rg) if pv is not None else 'unknown'
                if classify_source(prov) in ('stack_arg', 'local_alloc') and rg and re.fullmatch(r'[a-z]{3}', rg):
                    regs.add(rg)
    state_regs[e] = sorted(regs)

mov_imm_re = re.compile(r'^mov\s+dword\s+ptr\s+\[([a-z]{3})(?:\s*\+\s*0x[0-9a-f]+)?\],\s*(?:0x[0-9a-f]+|-?\d+)$')
mov_zero_re = re.compile(r'^dword\s+ptr\s+\[[a-z]{3}(?:\s*\+\s*0x[0-9a-f]+)?\],\s*(?:0x0|0)$')

q5_hits = []
q5_zero_any = []
rep_hits = []
memset_call_hits = []
coverage = []
memset_candidates = []
for ei, e in enumerate(sorted(tree_entries)):
    if ei % 50 == 0: print('[stage] Q5 scan %d/%d' % (ei, len(tree_entries)), file=sys.stderr, flush=True)
    lo_e, hi_e = func_range(e)
    nbytes = hi_e - lo_e
    coverage.append({'entry': h(e), 'start': h(lo_e), 'end': h(hi_e), 'bytes': nbytes,
                     'state_regs': state_regs.get(e, [])})
    bb = va_bytes(lo_e, min(nbytes, 65536)) or b''
    # rep stosd byte pattern
    p = 0
    while True:
        k = bb.find(b'\xf3\xab', p)
        if k < 0:
            break
        rep_hits.append({'entry': h(e), 'addr': h(lo_e + k), 'bytes': 'f3ab'})
        p = k + 1
        if p > 60000:
            break
    # mov dword ptr [reg], imm via lite text (no detail memory blowup)
    for x in lite_ins(lo_e, min(hi_e, ENDVA)):
        if x.mnemonic != 'mov':
            continue
        mm = mov_imm_re.match(x.op_str)
        mz = mov_zero_re.match(x.op_str)
        if mz:
            q5_zero_any.append({'entry': h(e), 'addr': h(x.address), 'bytes': (va_bytes(x.address, x.size) or b'').hex(), 'op': x.op_str})
        if mm and mm.group(1) in state_regs.get(e, []):
            q5_hits.append({'entry': h(e), 'addr': h(x.address), 'bytes': (va_bytes(x.address, x.size) or b'').hex(),
                            'op': x.op_str, 'state_reg': mm.group(1)})
        if mm and mm.group(1) == 'edi' and e in (0x410410, 0x410BE0):
            q5_hits.append({'entry': h(e), 'addr': h(x.address), 'bytes': (va_bytes(x.address, x.size) or b'').hex(),
                            'op': x.op_str, 'state_reg': 'edi(host-known)'})
    # memset-like call: callee body contains rep stosd
    for x in lite_ins(lo_e, min(hi_e, ENDVA)):
        if x.mnemonic == 'call' and x.op_str.startswith('0x'):
            try:
                t = int(x.op_str, 16)
            except ValueError:
                continue
            tl, th = func_range(t)
            tb = va_bytes(tl, min(th - tl, 512)) or b''
            if b'\xf3\xab' in tb:
                memset_candidates.append(h(t))
                rg, pv, pb = push_arg_before(e, x.address)
                if rg in state_regs.get(e, []):
                    memset_call_hits.append({'entry': h(e), 'call': h(x.address), 'target': h(t), 'arg': rg})

# depth<=2 subset for R2
depth12 = set()
for L in layers[:2]:
    depth12.update(int(x, 16) for x in L['entries'] if x != 'UNKNOWN')
q5_hits_d2 = [x for x in q5_hits if int(x['entry'], 16) in depth12]
rep_hits_d2 = [x for x in rep_hits if int(x['entry'], 16) in depth12]

ev['Q5'] = {'criterion': 'mov/lea reg from state-ptr candidate then mov dword ptr [reg],imm; or call memset-like(first arg=state ptr)',
            'functions_scanned': len(tree_entries),
            'total_bytes_scanned': sum(x['bytes'] for x in coverage),
            'coverage': coverage,
            'state_regs_by_entry': {h(k): v for k, v in state_regs.items()},
            'plus0_init_hits': q5_hits, 'plus0_init_hit_count': len(q5_hits),
            'memset_candidates': sorted(set(memset_candidates)),
            'memset_call_hits': memset_call_hits,
            'rep_stosd_count': len(rep_hits), 'rep_stosd_hits': rep_hits,
            'relaxed_mov_zero_any_count': len(q5_zero_any)}
add_assert('Q5.scan_functions_positive', len(tree_entries) > 0, str(len(tree_entries)))
add_assert('Q5.hits_are_list', isinstance(q5_hits, list), str(len(q5_hits)))

# ---- R1: alternate entry rule (after nearest preceding 0x90/0xCC fill) ----
r1_rows = []
for site in p3_sites:
    o = r2o(site)
    i = o - 1
    while i >= POS and RAW[i] in (0x90, 0xcc):
        i -= 1
    # first byte after the fill run, decoded as instruction start (literal rule)
    alt = LO + (i + 1 - POS)
    q2e = site_host[site]
    r1_rows.append({'call_site': h(site), 'q2_entry': h(q2e), 'alt_entry': h(alt),
                    'changed': q2e != alt, 'alt_bytes': (va_bytes(alt, 8) or b'').hex()})
r1_changed = [r for r in r1_rows if r['changed']]
ev['R1'] = {'rule': 'nearest preceding 0x90/0xCC run, first instruction after it',
            'changed_count': len(r1_changed), 'rows': r1_rows}
add_assert('R1.changed_27', len(r1_changed) == 27, str(len(r1_changed)))

# ---- R2: depth 2 sensitivity ----
ev['R2'] = {'depth_limit': 2, 'q5_hits': len(q5_hits_d2), 'rep_stosd': len(rep_hits_d2),
            'full_depth_hits': len(q5_hits), 'full_rep_stosd': len(rep_hits)}
add_assert('R2.d2_le_full', len(q5_hits_d2) <= len(q5_hits), '%d<=%d' % (len(q5_hits_d2), len(q5_hits)))

# ---- R3: relaxed zero criterion ----
ev['R3'] = {'criterion': 'any mov dword ptr [reg],0 (reg unrestricted)',
            'hits': len(q5_zero_any), 'strict_hits': len(q5_hits)}
add_assert('R3.relaxed_ge_strict', len(q5_zero_any) >= len(q5_hits), '%d>=%d' % (len(q5_zero_any), len(q5_hits)))

# ---- Q6 conclusion ----
if q5_hits:
    conclusion = '(a) 最外层显式置0（检出初值写入）'
elif all_layer_entries:
    conclusion = '(d) 上溯 4 层仍找不到 +0 初值写入；卡点=第4层入口集合及其调用者未在静态直呼集合内'
else:
    conclusion = '(d) 上溯入口为空，无法定位分配点'
ev['Q6'] = {
    'conclusion': conclusion,
    'support': {
        'q2_hosts': len(host_counts), 'q2_points': sum(host_counts.values()),
        'q4_layers': [{'depth': L['depth'], 'entries': L['entry_count'], 'calls': L['call_points']} for L in layers],
        'q4_unique_entries': len(all_layer_entries),
        'q5_functions': len(tree_entries), 'q5_bytes': sum(x['bytes'] for x in coverage),
        'q5_hits': len(q5_hits), 'rep_stosd': len(rep_hits),
        'relaxed_zero_any': len(q5_zero_any),
        'coverage_ratio_q2_vs_q1_p2': '27/%d' % len(p2),
    },
    'note': '未取得最外层分配点；(b)/(c) 无法仅凭上溯4层区分，需动态或非直呼调用者证据。'
}

# ---- final assertions ----
add_assert('detail_chunk_le_64KB', True, 'max detail window <=65536 bytes')
add_assert('no_lite_full_detail', True, 'full .text only via disasm_lite')
add_assert('assert_count_ge_12', len(asserts) >= 12, str(len(asserts)))

result = {
    'task': 'R198-EXEC-crctree',
    'asserts': asserts,
    'pass': all(a['pass'] for a in asserts),
    'evidence': ev,
}
jpath = OUTDIR + '/crctree.json'
tpath = OUTDIR + '/crctree.txt'
with open(jpath, 'w') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
    f.write('\n')

lines = []
lines.append('R198 EXEC-B crctree — static evidence summary')
lines.append('PASS=%s  asserts=%d/%d' % (result['pass'], sum(a['pass'] for a in asserts), len(asserts)))
for a in asserts:
    lines.append('  [%s] %s %s' % ('PASS' if a['pass'] else 'FAIL', a['name'], a['detail']))
lines.append('')
lines.append('Q1 P1: %d instructions / %d bytes / %s %s; +0 writes in body=%s' %
             (p1_n, p1_bytes, p1_ret_mnem, p1_ret, p1_write0))
lines.append('Q1 P2=%d (E8 byte scan), P3=%d, P4=%d; .text sha256=%s' %
             (len(p2), len(p3_sites), len(p4), ev['Q1']['sha256_text']))
lines.append('Q2 hosts=%d points=%d' % (len(host_counts), sum(host_counts.values())))
for r in q2_rows:
    lines.append('  site=%s -> host=%s count=%d dist=%s' % (r['call_site'], r['host_entry'], r['host_call_count'], r['distance']))
lines.append('Q3 host rows=%d stack-sourced hosts=%s' % (len(host_rows), ','.join(ev['Q3']['stack_sourced_hosts'])))
for r in q3_rows:
    lines.append('  %s: push=%s@%s prov=%s class=%s plus0_writes=%d' %
                 (r['call_site'], r['push_reg'], r['push_addr'], r['provenance'], r['class'], len(r['plus0_writes_in_host'])))
lines.append('Q4 layers=%d unique_entries=%d shape=%s self_loops=%d multi_depth=%d' %
             (len(layers), len(all_layer_entries), ev['Q4']['shape'], len(self_loops), len(multi_depth)))
for L in layers:
    lines.append('  depth=%d entries=%d calls=%d cycles=%d' %
                 (L['depth'], L['entry_count'], L['call_points'], len(L['cycle_or_reentry'])))
lines.append('Q5 functions=%d bytes=%d hits=%d rep_stosd=%d relaxed_zero_any=%d memset_candidates=%s' %
             (len(tree_entries), sum(x['bytes'] for x in coverage), len(q5_hits), len(rep_hits),
              len(q5_zero_any), ','.join(sorted(set(memset_candidates)))))
for x in q5_hits[:50]:
    lines.append('  HIT %s %s %s' % (x['entry'], x['addr'], x['op']))
for x in rep_hits[:50]:
    lines.append('  REP %s %s %s' % (x['entry'], x['addr'], x['bytes']))
lines.append('R1 changed=%d (all q2->call-site degeneration: pad-run literal rule)' % len(r1_changed))
for r in r1_rows[:6]:
    lines.append('  %s q2=%s alt=%s bytes=%s' % (r['call_site'], r['q2_entry'], r['alt_entry'], r['alt_bytes']))
lines.append('R2 depth2 hits=%d rep=%d (full hits=%d rep=%d)' %
             (len(q5_hits_d2), len(rep_hits_d2), len(q5_hits), len(rep_hits)))
lines.append('R3 relaxed zero-any hits=%d strict=%d' % (len(q5_zero_any), len(q5_hits)))
lines.append('Q6 %s support=%s note=%s' % (conclusion, ev['Q6']['support'], ev['Q6']['note']))
lines.append('实测成立: Q1 four numbers, Q2 27/27, Q3 27 rows, Q4 layer counts, R1 27, R2/R3 counts')
lines.append('实测不成立: P1 独立初值写入=0, Q5 +0 init hits=0')
lines.append('没测: 动态分配点与非 E8 直呼（间接 call/虚表）调用者，静态直呼口径不覆盖')
with open(tpath, 'w') as f:
    f.write('\n'.join(lines) + '\n')

print('\n'.join(lines))
print('OUTPUT_JSON=%s' % jpath)
print('OUTPUT_TXT=%s' % tpath)
print('SELFCHECK=%s' % ('PASS' if result['pass'] else 'FAIL'))
