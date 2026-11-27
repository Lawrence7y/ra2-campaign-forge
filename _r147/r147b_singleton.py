#!/usr/bin/env python3
"""R147 B：0x8871E0 单例判定的交叉复算 + 正反控 + 调用者闭环。

r147a 已得：3 写入（1 非空 + 2 归零）、1420 读。本脚本做**独立**复算，不引用 r147a 的中间量：
  V1 原始字节串计数：绝对地址在编址里的 4 字节小端形态出现次数 == 指令边界命中数
     （若不等，说明有站点落在指令中间而被 capstone 跳过，属漏检）
  V2 写入点的三类定性：非空写入 / 归零写入，并核实归零处的寄存器确为 0
     （向后扫该函数内对同一寄存器的 xor/sub 自减，或 cmp 该寄存器与自身——保守只认 xor r,r）
  V3 每个写入点所在函数（用 call 直接目标定义函数起点）的**入边数**；0 入边 => 死代码/导出
  V4 正反控：
     POS 0x886380 原始字节命中 8（r147a 用相邻全局当正控是错的，S-329）
     NEG 0x8871E4 / 0x8871DC 命中 0（确为无引用全局，不能当正控）
     CTRL 1,423 个读点里至少 1 个后面紧跟 dword ptr [reg + disp] 成员访问（证明是指针非标量）

纪律：全部流式 disasm_lite；每条断言都给 got/want；任一失败写入 fails。
"""
import sys, re, json, struct, collections, hashlib, time, bisect
HERE = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, HERE + '/_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TGT = 0x8871E0

# ---------- V1：原始字节串计数 ----------
rawpat = struct.pack('<I', TGT)
raw_hits = []
start = 0
while True:
    i = B.data.find(rawpat, start)
    if i < 0:
        break
    raw_hits.append(i)
    start = i + 1
raw_n = len(raw_hits)
# 这些偏移是否都落在 .text 的可执行区间（能换算回 VA 且节名 .text）
raw_in_text = sum(1 for o in raw_hits if B.sec_of(B.IB + [s for s in B.secs if s[0] == '.text'][0][1] + 0) is not None
                  and any(s[0] == '.text' and s[3] <= o < s[3] + s[4] for s in B.secs))

# ---------- 流式扫描 ----------
insns = []
calltgt = set()
tx = [s for s in B.secs if s[0] == '.text'][0]
off = tx[3]; end = off + tx[4]; vs = tx[1]
while off < end:
    chunk = B.data[off:min(off + 65536, end)]
    base = B.IB + (vs + (off - tx[3]))
    consumed = 0
    for a, sz, mn, op in md.disasm_lite(chunk, base):
        if a - base + sz > len(chunk):
            break
        consumed = a - base + sz
        insns.append((a, mn, re.sub(r'\s+', '', op or '').lower()))
        if mn == 'call':
            t = re.sub(r'\s+', '', op or '').lower()
            if t.startswith('0x'):
                try:
                    v = int(t, 16)
                    if B.IB <= v < B.IB + 0x900000:
                        calltgt.add(v)
                except ValueError:
                    pass
    off += consumed if consumed else 1
insns.sort()
starts = sorted(calltgt | {B.IB + tx[1]})   # 仅 call 目标：jmp 目标常是函数内失败分支
ADDRS = [a for a, _, _ in insns]
IDX = {a: i for i, a in enumerate(ADDRS)}

def func_of(va):
    i = bisect.bisect_right(starts, va) - 1
    return starts[i] if i >= 0 else starts[0]

def body(fv):
    return [x for x in insns if func_of(x[0]) == fv]

# ---------- V1b：指令边界命中数 ----------
rx = re.compile(r'0x%x(?![0-9a-f])' % TGT)
hits = [x for x in insns if rx.search(x[2])]

# ---------- V2：写入点分类 ----------
mem = '[0x%x]' % TGT
PREFIX = re.compile(r'^(dword|qword|word|byte|xmmword)ptr')
writes = []
for a, mn, op in hits:
    dest, _, src = op.partition(',')
    if PREFIX.sub('', dest) == mem:
        writes.append((a, mn, op, src))

def reg_is_zero(fv, va, reg):
    """在写入点之前、同一函数体内，是否有 xor reg,reg 或 sub reg,reg（中间未被覆盖性赋值打断的保守判法）。"""
    b = [x for x in body(fv) if x[0] < va]
    for a, mn, op in reversed(b):
        p = op.split(',')
        if mn in ('xor', 'sub') and len(p) == 2 and p[0] == reg and p[1] == reg:
            # 其后是否被 mov reg,... / pop reg 覆盖
            after = [x for x in b if a < x[0] < va and (x[2].startswith('mov' + reg + ',')
                                                        or x[2].startswith('pop' + reg)
                                                        or x[2].startswith('lea' + reg + ','))]
            return (True, '0x%X' % a) if not after else (False, 'clobbered@0x%X' % after[0][0])
        if p[0] == reg and mn in ('mov', 'movzx', 'lea', 'pop', 'xchg'):
            return False, 'assigned@0x%X' % a
    return False, 'no-zero-found'

wdet = []
for a, mn, op, src in writes:
    fv = func_of(a)
    if src in L.GEN:
        z, how = reg_is_zero(fv, a, src)
    else:
        z, how = False, 'nonreg:' + src
    wdet.append({'va': '0x%X' % a, 'mn': mn, 'op': op, 'src': src,
                 'func': '0x%X' % fv, 'src_is_zero': z, 'zero_evidence': how})

# ---------- V3：写入函数的入边 ----------
inbound = {}
for f in sorted({w['func'] for w in wdet}):
    fv = int(f, 16)
    src = [x for x, mn, op in insns if mn in ('call', 'jmp') and op == '0x%x' % fv]
    inbound[f] = {'n': len(src), 'from': ['0x%X' % s for s in src],
                  'from_funcs': ['0x%X' % func_of(s) for s in src],
                  'body_len': len(body(fv))}

# ---------- V4：控制 ----------
def raw_count(v):
    p = struct.pack('<I', v)
    n = 0; s = 0
    while True:
        i = B.data.find(p, s)
        if i < 0:
            break
        n += 1; s = i + 1
    return n

ctrl = {}
for tag, v in (('pos_886380', 0x886380), ('pos_8871e0', TGT),
               ('neg_8871e4', 0x8871E4), ('neg_8871dc', 0x8871DC)):
    ctrl[tag] = {'addr': '0x%X' % v, 'raw_count': raw_count(v)}

# 成员访问跟随：读点之后 0..3 条指令内出现 dwordptr[同寄存器+disp]
MEMP = re.compile(r'^dwordptr\[([a-z0-9]+)([+-])')
follow = 0
follow_sample = []
LOADP = re.compile(r'^([a-z0-9]+),dwordptr\[0x8871e0\]$')
for a, mn, op in hits:
    dest, _, src = op.partition(',')
    if PREFIX.sub('', dest) == mem:
        continue                     # 写入点不计
    m0 = LOADP.match(op)
    if mn != 'mov' or not m0:
        continue
    reg = m0.group(1)
    i = IDX.get(a)
    if i is None:
        continue
    for j in range(1, 4):
        if i + j >= len(insns):
            break
        na, nmn, nop = insns[i + j]
        m = re.match(r'^(dword|byte)ptr\[([a-z0-9]+)\+', nop)
        if m and m.group(2) == reg:
            follow += 1
            if len(follow_sample) < 5:
                follow_sample.append({'load_at': '0x%X' % a, 'access_at': '0x%X' % na, 'access': nop})
            break

# ---------- 断言 ----------
checks = []
def ck(n, c, got, want):
    checks.append({'name': n, 'ok': bool(c), 'got': got, 'want': want})

ck('V1 原始字节命中数 == 指令边界命中数（无漏检）', raw_n == len(hits), [raw_n, len(hits)], '相等')
ck('V1b 原始命中全部落在 .text 原始区间', raw_in_text == raw_n, [raw_in_text, raw_n], '相等')
ck('V2 写入点恰 3 个', len(writes) == 3, len(writes), 3)
ck('V2 写非空值恰 1 个', sum(1 for w in wdet if not w['src_is_zero']) == 1,
   sum(1 for w in wdet if not w['src_is_zero']), 1)
ck('V2 写零恰 2 个', sum(1 for w in wdet if w['src_is_zero']) == 2,
   sum(1 for w in wdet if w['src_is_zero']), 2)
ck('V3 构造点所在函数 0x52BA60 入边 >= 1', inbound.get('0x52BA60', {}).get('n', 0) >= 1,
   inbound.get('0x52BA60', {}).get('n'), '>=1')
ck('V3 析构函数 0x6BE1C0 入边 >= 1', inbound['0x6BE1C0']['n'] >= 1, inbound['0x6BE1C0']['n'], '>=1')
ck('V3 三个写入点收敛到 2 个函数（同一 ctor 的失败分支 + teardown）', len(inbound) == 2, sorted(inbound), 2)
ck('V4 POS 0x886380 原始命中 > 0', ctrl['pos_886380']['raw_count'] > 0, ctrl['pos_886380']['raw_count'], '>0')
ck('V4 NEG 0x8871E4 原始命中 == 0', ctrl['neg_8871e4']['raw_count'] == 0, ctrl['neg_8871e4']['raw_count'], 0)
ck('V4 NEG 0x8871DC 原始命中 == 0', ctrl['neg_8871dc']['raw_count'] == 0, ctrl['neg_8871dc']['raw_count'], 0)
ck('V4 读点后有成员访问跟随（指针语义）', follow >= 1, follow, '>=1')
ck('V4 读点数 1420 与 r147a 一致（独立复算）', len(hits) - len(writes) == 1420,
   len(hits) - len(writes), 1420)

out = {'checks': checks, 'fails': [c['name'] for c in checks if not c['ok']],
       'raw_n': raw_n, 'raw_in_text': raw_in_text, 'insn_hits': len(hits),
       'writes': wdet, 'inbound': inbound, 'ctrl': ctrl,
       'follow_n': follow, 'follow_sample': follow_sample,
       'n_insns': len(insns), 'secs': time.time() - T0}
json.dump(out, open(HERE + '/_r147/r147b_singleton.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({'fails': out['fails'],
                  'raw_n': raw_n, 'insn_hits': len(hits), 'writes': len(writes),
                  'writes_detail': wdet, 'inbound': inbound,
                  'follow_n': follow, 'ctrl': ctrl, 'secs': round(time.time() - T0, 1)},
                 ensure_ascii=False, indent=1))
