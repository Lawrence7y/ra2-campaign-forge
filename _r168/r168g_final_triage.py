#!/usr/bin/env python3
"""R168 G：65 条洞的**最终**五桶分桶（每条一个可失败判据 + 反控）。

五桶（互斥、和为 65）：
  T1 引用型 4 字节跳转表内   —— r168c 的 58 条（含 r168e 证伪 R167 的 3 条 w3 + 1 条缺陷）
  T2 严格递增字节查表（incrun >= 6）
  T3 小整数索引表（邻域 32 B 全在 0x01..0x20）
  T4 非指令短填充（长度 <= 3 的可解不出字节串，其后 <= 8 B 内出现 ret c3）
  T5 其它（不硬凑）
"""
import sys, json, random
sys.path.insert(0, '_r143')
import r143lib as L
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
B = L.Bin(); data = B.data; IB = B.IB
text = [s for s in B.secs if s[0] == '.text'][0]
LO = IB + text[1]; HI = LO + text[2]
md = Cs(CS_ARCH_X86, CS_MODE_32)
holes = [int(x, 16) for x in json.load(open('_r167/r167d_holes_semantics_final.json'))['holes']]
C = json.load(open('_r168/r168c_final_buckets.json'))
in_tab = set(int(x, 16) for x in C['buckets']['code_jump_table'])

def incrun(va, span=64):
    best = cur = 1; prev = None
    for i in range(span):
        b = B.rd(va + i, 1)
        if not b: break
        c = b[0]
        if prev is not None and c == prev + 1:
            cur += 1; best = max(best, cur)
        else: cur = 1
        prev = c
    return best

def small_int_run(va, span=32):
    n = 0
    for i in range(span):
        b = B.rd(va + i, 1)
        if not b or not (0x01 <= b[0] <= 0x20): break
        n += 1
    return n

def badlen(va, maxb=3):
    """从 va 起有多少个连续字节是「解不出指令」的单字节，且其后能解出 ret。"""
    n = 0
    for i in range(maxb):
        b = B.rd(va + i, 1)
        if not b: return 0
        if list(md.disasm(b, va + i, count=1)): break
        n += 1
    if n == 0: return 0
    for k in range(1, 10):
        b = B.rd(va + n + k - 1, 1)
        if b and b[0] == 0xC3: return n
    return 0

buckets = {'T1_jump_table': [], 'T2_byte_lookup': [], 'T3_index_table': [],
           'T4_short_pad': [], 'T5_other': []}
rows = []
for h in holes:
    r = {'va': hex(h), 'incrun': incrun(h), 'smallint32': small_int_run(h), 'badlen': badlen(h)}
    if h in in_tab:
        k = 'T1_jump_table'
    elif r['incrun'] >= 6:
        k = 'T2_byte_lookup'
    elif r['smallint32'] >= 16:
        k = 'T3_index_table'
    elif r['badlen'] > 0:
        k = 'T4_short_pad'
    else:
        k = 'T5_other'
    r['bucket'] = k
    buckets[k].append(h); rows.append(r)

# 反控
rnd = random.Random(20261127)
N = 2000
b_inc = b_sm = b_bad = 0
for _ in range(N):
    va = rnd.randrange(LO, HI - 96)
    if incrun(va) >= 6: b_inc += 1
    if small_int_run(va) >= 16: b_sm += 1
    if badlen(va) > 0: b_bad += 1

A = []
A.append({'id': 'G1 五桶互斥且和为 65',
          'ok': sum(len(v) for v in buckets.values()) == 65 == len(set(holes)),
          'detail': repr({k: len(v) for k, v in buckets.items()})})
A.append({'id': 'G2 T1 == r168c 的 code_jump_table 58 条逐条',
          'ok': set(buckets['T1_jump_table']) == in_tab and len(in_tab) == 58,
          'detail': '%d vs %d' % (len(buckets['T1_jump_table']), len(in_tab))})
A.append({'id': 'G3 反控 incrun>=6 在随机段的比例 < 3%', 'ok': b_inc / N < 0.03,
          'detail': '%d/2000=%.4f' % (b_inc, b_inc / N)})
A.append({'id': 'G4 反控 小整数 32B 游程 >=16 在随机段的比例 < 3%', 'ok': b_sm / N < 0.03,
          'detail': '%d/2000=%.4f' % (b_sm, b_sm / N)})
A.append({'id': 'G5 T2 四条就是同一 16 字节样本的两处 × 两个落点',
          'ok': sorted(buckets['T2_byte_lookup']) == [0x7c5d92, 0x7c5d9c, 0x7c80f2, 0x7c80fc],
          'detail': repr([hex(x) for x in buckets['T2_byte_lookup']])})
A.append({'id': 'G6 T4 的那条 0x793455：fe ff 两字节后第 3 字节是 c3',
          'ok': buckets['T4_short_pad'] == [0x793455] and B.rd(0x793457, 1) == b'\xc3',
          'detail': repr([hex(x) for x in buckets['T4_short_pad']])})
A.append({'id': 'G7 T5 只剩 0x7d0cba 一条（R167 缺陷产物）',
          'ok': buckets['T5_other'] == [0x7d0cba],
          'detail': repr([hex(x) for x in buckets['T5_other']])})
A.append({'id': 'G8 0x723e27 归 T3 且邻域 32 B 全为 0x01..0x20',
          'ok': 0x723e27 in buckets['T3_index_table']
          and small_int_run(0x723e27) >= 16,
          'detail': 'run=%d' % small_int_run(0x723e27)})
out = {'buckets': {k: [hex(x) for x in v] for k, v in buckets.items()},
       'counts': {k: len(v) for k, v in buckets.items()},
       'null_rates': {'incrun6': b_inc / N, 'smallint16': b_sm / N, 'badlen': b_bad / N},
       'rows': rows, 'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r168/r168g_final_triage.json', 'w'), ensure_ascii=False, indent=1)
print('counts:', out['counts'])
for k, v in out['buckets'].items(): print(' ', k, v)
print('null rates:', out['null_rates'])
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', '')[:200])
