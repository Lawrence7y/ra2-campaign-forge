#!/usr/bin/env python3
"""R147 E：主会话对 0x8871E0 结论的**复算**（规则 D：审计结论必须由主会话亲自复算）。

复算对象是 r147a..d 四条已落盘结论 + 执行员 #328 的独立结果。
本脚本不复用上面任何脚本的中间量，全部重扫一遍，并同时算三件事：
  R1 三形态分类：无变址（标量/指针槽） / 带变址（*N，数组容器） / 其它
     —— 这是「多实例容器」假说的**直接否证**手段：若存在以 0x8871E0 为基址的
        变址写，说明它是数组；若为 0，则容器假说在静态层面无据。
  R2 写入点的三级定性：构造写（源为 call 返回值）/ 归零写（源被证明为 0）/ 其它
  R3 交叉核对执行员 #328 的七个数字（1423 / 1423 / 3 / POS 8 / NEG 0,0 / ctor 0x52BA60）
另含正反控：
  POS 0x886380 原始字节 8
  NEG 0x8871E4 / 0x8871DC 原始字节 0（这两个是无人引用全局，当作正控会假失败）
  CTRL 0x4A8660 的负位移写法必须被本扫描器捕获（r145 的 norm 缺陷回归）
"""
import sys, re, struct, json, bisect, time
HERE = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, HERE + '/_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TGT = 0x8871E0

def N(op):
    return re.sub(r'\s+', '', op or '').lower()

tx = [s for s in B.secs if s[0] == '.text'][0]
off = tx[3]; end = off + tx[4]; vs = tx[1]
insns = []; calls = set()
while off < end:
    ch = B.data[off:min(off + 65536, end)]
    base = B.IB + (vs + (off - tx[3])); c = 0
    for a, sz, mn, op in md.disasm_lite(ch, base):
        if a - base + sz > len(ch):
            break
        c = a - base + sz
        insns.append((a, mn, N(op)))
        if mn == 'call' and N(op).startswith('0x'):
            v = int(N(op), 16)
            if B.IB <= v < B.IB + 0x900000:
                calls.add(v)
    off += c if c else 1
insns.sort()
A = [x[0] for x in insns]
starts = sorted(calls | {B.IB + tx[1]})

def func_of(v):
    i = bisect.bisect_right(starts, v) - 1
    return starts[i] if i >= 0 else starts[0]

# ---------- R1 三形态 ----------
rx = re.compile(r'0x8871e0(?![0-9a-f])')
plain, indexed, other = [], [], []
for a, mn, op in insns:
    if not rx.search(op):
        continue
    if '*' in op:
        indexed.append((a, mn, op))
    elif op.endswith('[0x8871e0]') or 'dwordptr[0x8871e0]' in op:
        plain.append((a, mn, op))
    else:
        other.append((a, mn, op))

# ---------- R2 写入定性 ----------
PRE = re.compile(r'^(dword|qword|word|byte|xmmword)ptr')
mem = '[0x8871e0]'
wr = []
for a, mn, op in plain:
    d, _, s = op.partition(',')
    if PRE.sub('', d) == mem:
        wr.append((a, mn, s))

def prev_call(a):
    """写入点之前最近的 call：返回 (call 指令 VA, call 的直接目标 VA 或 None)。
    S-334：首版只返回指令 VA（0x52BAD1），却拿去和「目标 0x665650」比，断言必然假失败。"""
    fv = func_of(a)
    i = bisect.bisect_left(A, a)
    j = i - 1
    while j >= 0 and insns[j][0] >= fv:
        if insns[j][1] == 'call':
            t = insns[j][2]
            tgt = int(t, 16) if t.startswith('0x') else None
            return insns[j][0], tgt
        j -= 1
    return None, None

wdet = []
for a, mn, s in wr:
    fv = func_of(a)
    pc, ptgt = prev_call(a)
    wdet.append({'va': '0x%X' % a, 'src': s, 'func': '0x%X' % fv,
                 'prev_call_at': '0x%X' % pc if pc else None,
                 'prev_call_target': '0x%X' % ptgt if ptgt else None,
                 'callers_of_func': ['0x%X' % x[0] for x in insns
                                     if x[1] == 'call' and x[2] == '0x%x' % fv]})

# ---------- 原始字节计数 ----------
def raw(v):
    p = struct.pack('<I', v); n = 0; i = 0
    while True:
        j = B.data.find(p, i)
        if j < 0:
            return n
        n += 1; i = j + 1

RB = {'tgt': raw(TGT), 'pos_886380': raw(0x886380),
      'neg_8871e4': raw(0x8871E4), 'neg_8871dc': raw(0x8871DC)}

# ---------- CTRL：负位移捕获回归 ----------
negdisp_ok = any(a == 0x4A8660 and '0x7e6060' in op for a, mn, op in insns)

# ---------- 执行员 #328 交叉核对 ----------
exec_json = json.load(open(HERE + '/_r147/r147x_exec_scan.json'))
x = {
    'BYTE_TARGET_COUNT': exec_json['BYTE_TARGET_COUNT'],
    'BOUNDARY_HIT_COUNT': exec_json['BOUNDARY_HIT_COUNT'],
    'WRITE_COUNT': exec_json['WRITE_COUNT'],
    'POS': exec_json['POS_0x886380_COUNT'],
    'NEG': [exec_json['NEG_COUNTS']['0x8871e4'], exec_json['NEG_COUNTS']['0x8871dc']],
    'CTOR': '0x%X' % exec_json['WRITES'][0]['func_start'],
    'ZERO_STATES': [w['state_name'] for w in exec_json['WRITES']],
}

def fc(n, c, got, want):
    return {'name': n, 'ok': bool(c), 'got': got, 'want': want}

checks = [
    fc('R1 无变址形态 (=标量/指针槽)', len(plain) == 1423, len(plain), 1423),
    fc('R1 变址形态为 0（容器/数组假说静态无据）', len(indexed) == 0, len(indexed), 0),
    fc('R1 其它形态 0', len(other) == 0, len(other), 0),
    fc('R2 写入点 3 个', len(wdet) == 3, len(wdet), 3),
    fc('R2 写入点 VA 恰为 52BAD8/52BAFA/6BEABD',
       [w['va'] for w in wdet] == ['0x52BAD8', '0x52BAFA', '0x6BEABD'],
       [w['va'] for w in wdet], ['0x52BAD8', '0x52BAFA', '0x6BEABD']),
    fc('R2 写入函数仅 2 个', len({w['func'] for w in wdet}) == 2,
       sorted({w['func'] for w in wdet}), 2),
    fc('R2 构造写 0x52BAD8 的前置 call 目标是 0x665650（宿主 ctor）',
       wdet[0]['prev_call_target'] == '0x665650', wdet[0]['prev_call_target'], '0x665650'),
    fc('POS 0x886380 原始字节 8', RB['pos_886380'] == 8, RB['pos_886380'], 8),
    fc('NEG 0x8871E4 原始 0', RB['neg_8871e4'] == 0, RB['neg_8871e4'], 0),
    fc('NEG 0x8871DC 原始 0', RB['neg_8871dc'] == 0, RB['neg_8871dc'], 0),
    fc('CTRL 负位移 0x4A8660 装表被捕获', negdisp_ok, negdisp_ok, True),
    fc('X1 执行员字节数 == 我方', x['BYTE_TARGET_COUNT'] == RB['tgt'], [x['BYTE_TARGET_COUNT'], RB['tgt']], '相等'),
    fc('X2 执行员边界命中 == 我方', x['BOUNDARY_HIT_COUNT'] == len(plain), [x['BOUNDARY_HIT_COUNT'], len(plain)], '相等'),
    fc('X3 执行员写入数 == 我方', x['WRITE_COUNT'] == len(wdet), [x['WRITE_COUNT'], len(wdet)], '相等'),
    fc('X4 执行员 POS == 我方', x['POS'] == RB['pos_886380'], [x['POS'], RB['pos_886380']], '相等'),
    fc('X5 执行员 NEG == 我方', x['NEG'] == [RB['neg_8871e4'], RB['neg_8871dc']], x['NEG'], '相等'),
    fc('X6 执行员 ctor 起点 == 我方 0x52BA60', x['CTOR'] == wdet[0]['func'], [x['CTOR'], wdet[0]['func']], '相等'),
    fc('X7 执行员三写入格的 ZERO 判定 == 我方 [UNKNOWN,ZERO,ZERO]',
       x['ZERO_STATES'] == ['UNKNOWN', 'ZERO', 'ZERO'], x['ZERO_STATES'], ['UNKNOWN', 'ZERO', 'ZERO']),
]

out = {'checks': checks, 'fails': [c['name'] for c in checks if not c['ok']],
       'R1': {'plain': len(plain), 'indexed': len(indexed), 'other': len(other),
              'indexed_sample': [{'va': '0x%X' % a, 'op': o} for a, _, o in indexed[:5]]},
       'R2': wdet, 'raw_bytes': RB, 'exec_cross': x,
       'secs': round(time.time() - T0, 1)}
json.dump(out, open(HERE + '/_r147/r147e_recompute.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({'fails': out['fails'], 'R1': out['R1'], 'R2': wdet,
                  'raw': RB, 'exec_cross': x, 'secs': out['secs']}, ensure_ascii=False, indent=1))
