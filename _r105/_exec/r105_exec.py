#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R105 EXEC 独立复算：19 张 switch 分派表的 292 个项值定性（正反控自测）。

口径（全部从 exe 字节开始，不读主会话脚本/JSON）：
  * PE 手工解析；.text 的 VirtualSize 作为解码/读取长度，VA = ImageBase + VirtualAddress。
  * 表持有指令：iced 线性扫得到 JMP + op0 MEMORY + index scale==4 + index != NONE
    + disp 落在 .text 内；is_invalid 的单元跳过；按 disp 分组。
  * 表项：从 disp 起每 4 字节读一个 DWORD（小端），只要 DWORD 值落在 .text 内就继续，
    到第一个越界值或满 512 项；只保留 n>=2 的表。
  * B1：_r101/_exec/r101_bc.json detail 中 class=="B1" 行的 host 字符串（十六进制）；
    归属表只要求 base <= host < base+4n（不做 4 字节对齐过滤，见.md 的解释）。
  * "合法单元起点"：iced 线性扫描产出的 ip 且有 is_invalid == False；
    "在 ip 集合里"与"合法"不是同一件事，必须另查 is_invalid。
  * CALL 目标集合：CALL + op0 NEAR_BRANCH32 的 near_branch_target。
"""
import hashlib
import json
import os
import random
import statistics
import struct
import sys

VENDOR = '/home/t628/projects/ra2-campaign-forge/_r104/vendor'
sys.path.insert(0, VENDOR)
import iced_x86  # noqa: E402

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(ROOT, 'ra2bench/gamemd.exe')
BC = os.path.join(ROOT, '_r101/_exec/r101_bc.json')
OUT = os.path.join(ROOT, '_r105/_exec/r105_exec.json')
SHA256_EXPECT = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
N_SAMPLE = 292
N_TRIALS = 200
MAX_ITEMS = 512
SEED = 10517

raw = open(EXE, 'rb').read()
sha = hashlib.sha256(raw).hexdigest()
if sha != SHA256_EXPECT:
    print('WARNING: sha256 mismatch: %s' % sha, file=sys.stderr)

# ---- PE 手工解析（不用 pefile；只依赖 struct） ----
pe_off = struct.unpack_from('<I', raw, 0x3c)[0]
assert raw[pe_off:pe_off + 4] == b'PE\0\0'
coff = pe_off + 4
machine, nsec = struct.unpack_from('<HH', raw, coff)[:2]
opt_size = struct.unpack_from('<H', raw, coff + 16)[0]
opt = coff + 20
magic = struct.unpack_from('<H', raw, opt)[0]
assert magic == 0x10b, 'expect PE32'
IB = struct.unpack_from('<I', raw, opt + 28)[0]
secs = {}
for k in range(nsec):
    o = opt + opt_size + 40 * k
    name = raw[o:o + 8].rstrip(b'\0').decode('ascii', 'replace')
    vsize, va, rsize, roff = struct.unpack_from('<IIII', raw, o + 8)
    secs[name] = {'vsize': vsize, 'rva': va, 'rsize': rsize, 'roff': roff}
txt = secs['.text']
B = IB + txt['rva']
END = B + txt['vsize']
TROFF = txt['roff']
TVB = raw[TROFF:TROFF + txt['vsize']]
assert len(TVB) == txt['vsize']
assert txt['rsize'] >= txt['vsize']


def dw(va):
    """从 .text 原始文件字节读小端 DWORD；确保 4 字节全在 VirtualSize 范围内。"""
    off = va - B
    if off < 0 or off + 4 > len(TVB):
        return None
    return struct.unpack_from('<I', TVB, off)[0]


def in_text(v):
    return B <= v < END


# ---- 一次线性扫描：单元起点 / call 目标 / 持有指令 ----
d = iced_x86.Decoder(32, TVB, ip=B)
unit_ip = set()
valid_starts = set()
invalid_starts = set()
holders = {}
call_targets = set()
sweep = {'units': 0, 'invalid': 0, 'bytes': 0}
while d.can_decode:
    ins = d.decode()
    sweep['units'] += 1
    sweep['bytes'] += ins.len
    uip = ins.ip & 0xffffffff
    unit_ip.add(uip)
    if ins.is_invalid:
        invalid_starts.add(uip)
        sweep['invalid'] += 1
    else:
        valid_starts.add(uip)
        if (ins.mnemonic == iced_x86.Mnemonic.JMP
                and ins.op_count == 1
                and ins.op0_kind == iced_x86.OpKind.MEMORY
                and ins.memory_index_scale == 4
                and ins.memory_index != iced_x86.Register.NONE
                and in_text(ins.memory_displacement & 0xffffffff)):
            holders.setdefault(ins.memory_displacement & 0xffffffff, []).append(uip)
        if (ins.mnemonic == iced_x86.Mnemonic.CALL
                and ins.op_count == 1
                and ins.op0_kind == iced_x86.OpKind.NEAR_BRANCH32):
            call_targets.add(ins.near_branch_target & 0xffffffff)

# ---- Q1: 枚举表 ----
tables = {}
for base, hs in holders.items():
    vals = []
    p = base
    for _ in range(MAX_ITEMS):
        v = dw(p)
        if v is None or not in_text(v):
            break
        vals.append(v)
        p += 4
    if len(vals) >= 2:
        tables[base] = {'holders': hs, 'vals': vals}

q1 = {
    'table_count': len(tables),
    'holder_instruction_count': sum(len(t['holders']) for t in tables.values()),
    'entry_count': sum(len(t['vals']) for t in tables.values()),
    'holder_group_count_all': len(holders),
    'holder_instruction_count_all': sum(len(v) for v in holders.values()),
}

# ---- Q2: B1 定位 ----
bc = json.load(open(BC))
b1_rows = [x for x in bc['detail'] if x.get('class') == 'B1']
b1_hosts = sorted({int(x['host'], 16) for x in b1_rows})


def table_of(a):
    for base, t in tables.items():
        if base <= a < base + 4 * len(t['vals']):
            return base
    return None


b1_host_in_table = {h: table_of(h) for h in b1_hosts}
used = sorted({b for b in b1_host_in_table.values() if b is not None})
q2 = {
    'b1_rows': len(b1_rows),
    'b1_unique_hosts': len(b1_hosts),
    'hosts_in_table': sum(1 for b in b1_host_in_table.values() if b is not None),
    'used_table_count': len(used),
    'used_table_bases': [hex(b) for b in used],
    'used_table_entries_total': sum(len(tables[b]['vals']) for b in used),
    'host_to_table': {hex(h): (hex(b) if b is not None else None)
                      for h, b in b1_host_in_table.items()},
}

# ---- 292 个项值（去重按 (base, index) 计，逐项保留） ----
entries = []
for base in used:
    for idx, v in enumerate(tables[base]['vals']):
        entries.append({'table': base, 'idx': idx, 'val': v,
                        'holder': tables[base]['holders'][0]})
assert len(entries) == q2['used_table_entries_total']

# ---- Q3: 合法单元起点（ip 在集合里 AND is_invalid==False） ----
q3_rows = []
for e in entries:
    v = e['val']
    q3_rows.append({
        'table': hex(e['table']), 'idx': e['idx'], 'val': hex(v),
        'in_unit_ip_set': v in unit_ip,
        'is_invalid': v in invalid_starts,
        'is_valid_start': v in valid_starts,
    })
q3 = {
    'entry_count': len(entries),
    'valid_start_count': sum(1 for r in q3_rows if r['is_valid_start']),
    'in_ip_set_count': sum(1 for r in q3_rows if r['in_unit_ip_set']),
    'invalid_count': sum(1 for r in q3_rows if r['is_invalid']),
    'not_in_ip_set_count': sum(1 for r in q3_rows if not r['in_unit_ip_set']),
    'rows': q3_rows,
}

# ---- Q4: 三项判据 ----
q4_rows = []
for e in entries:
    v = e['val']
    q4_rows.append({
        'table': hex(e['table']), 'idx': e['idx'], 'val': hex(v),
        'forward_of_holder': v > e['holder'],
        'is_call_target': v in call_targets,
    })
spans = []
for base in used:
    hs = tables[base]['holders']
    vs = tables[base]['vals']
    spans.append({'table': hex(base), 'holder': hex(hs[0]),
                  'max_val': hex(max(vs)), 'span': max(vs) - hs[0]})
q4 = {
    'forward_count': sum(1 for r in q4_rows if r['forward_of_holder']),
    'call_target_count': sum(1 for r in q4_rows if r['is_call_target']),
    'span_min': min(x['span'] for x in spans),
    'span_max': max(x['span'] for x in spans),
    'span_median': statistics.median(x['span'] for x in spans),
    'span_rows': spans,
    'rows': q4_rows,
}

# ---- Q5: 两组反控 ----
rng = random.Random(SEED)
nc = len(entries)
fracs = []
for _ in range(N_TRIALS):
    picks = [rng.randrange(B, END) for _ in range(nc)]
    nvalid = sum(1 for a in picks if a in valid_starts)
    fracs.append(nvalid / nc)
call_pool = sorted(call_targets)
call_sample = [rng.choice(call_pool) for _ in range(nc)]
ncall = sum(1 for a in call_sample if a in call_targets)
q5 = {
    'random_text_sample_size': nc,
    'random_trials': N_TRIALS,
    'random_valid_frac_median': statistics.median(fracs),
    'random_valid_frac_min': min(fracs),
    'random_valid_frac_max': max(fracs),
    'random_valid_frac_mean': statistics.fmean(fracs),
    'random_valid_frac_p05': sorted(fracs)[int(0.05 * N_TRIALS)],
    'random_valid_frac_p95': sorted(fracs)[int(0.95 * N_TRIALS)],
    'call_pool_size': len(call_pool),
    'call_sample_size': nc,
    'call_sample_in_call_targets': ncall,
    'discriminant_a3b': (q4['call_target_count'] == 0 and ncall == nc),
}

verdict = {
    'A1_all_entries_valid_start': q3['valid_start_count'] == nc,
    'A3a_all_forward_of_holder': q4['forward_count'] == nc,
    'A3b_no_entry_is_call_target': q4['call_target_count'] == 0,
    'A3e_call_target_control_positive': ncall == nc,
    'N2_random_vs_entries_gap': q5['random_valid_frac_median'] < 0.5,
}

out = {
    'meta': {
        'sha256': sha,
        'image_base': hex(IB),
        'text_va': hex(B), 'text_end': hex(END),
        'text_vsize': txt['vsize'],
        'machine': hex(machine), 'sections': nsec,
        'vendor': 'iced-x86 vendored in _r104/vendor',
        'seed': SEED,
        'sweep': sweep,
        'definition': {
            'table': 'JMP MEM[index*4+disp] (disp in .text), disp groups, DWORD read from disp until value out of .text or 512, n>=2',
            'host_belongs_to_table': 'base <= host < base+4*n (no 4-byte alignment requirement on host)',
            'valid_start': 'ip emitted by iced linear sweep AND is_invalid == False',
            'call_target': 'CALL with op0 NEAR_BRANCH32, near_branch_target',
        },
    },
    'Q1': q1, 'Q2': q2, 'Q3': q3, 'Q4': q4, 'Q5': q5,
    'verdict': verdict,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w') as f:
    json.dump(out, f, indent=2)

print('sha256 %s' % sha)
print('Q1 tables=%d holder_ins=%d entries=%d' %
      (q1['table_count'], q1['holder_instruction_count'], q1['entry_count']))
print('Q2 b1_rows=%d hosts=%d tables=%d used_entries=%d' %
      (q2['b1_rows'], q2['b1_unique_hosts'], q2['used_table_count'],
       q2['used_table_entries_total']))
print('Q3 valid_starts=%d/%d (in_ip_set=%d)' %
      (q3['valid_start_count'], nc, q3['in_ip_set_count']))
print('Q4 forward=%d/%d call_target=%d span=%d..%d' %
      (q4['forward_count'], nc, q4['call_target_count'],
       q4['span_min'], q4['span_max']))
print('Q5 random_frac_median=%.4f call_sample=%d/%d discriminant=%s' %
      (q5['random_valid_frac_median'], ncall, nc, q5['discriminant_a3b']))
print('verdict %s' % verdict)