#!/usr/bin/env python3
"""R147-EXEC-1: 0x8871E0 写入点普查（独立执行，只用 disasm_lite）。

一条命令完成：字节命中 / 指令边界命中 / 写入点识别 / 函数内前向数据流
（三值格 ZERO/NONZERO/UNKNOWN，分支汇合取交）/ 正反 CTRL 全输出。
"""
import sys, struct, re, json, bisect, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r143')
from r143lib import Bin
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

TARGET = 0x8871E0
POSADDR = 0x886380
NEGADDRS = [0x8871E4, 0x8871DC]
CTRL_WRITE = 0x52BAD8

b = Bin('/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe')
data = b.data


def byte_hits(val):
    pat = struct.pack('<I', val)
    out, i = [], 0
    while True:
        j = data.find(pat, i)
        if j < 0:
            break
        out.append(j)
        i = j + 1
    return out


# ---- 一次性流式反汇编 .text（disasm_lite，绝不 detail=True）----
md = Cs(CS_ARCH_X86, CS_MODE_32)
off, end, bv, chunk = b.T[3], b.T[3] + b.T[4], b.T[1], 65536
insns = []
while off < end:
    cb = data[off:min(off + chunk, end)]
    base = b.IB + (bv + (off - b.T[3]))
    cons = 0
    for a, sz, mn, op in md.disasm_lite(cb, base):
        if a - base + sz > len(cb):
            break
        cons = a - base + sz
        insns.append((a, sz, mn, re.sub(r'\s+', '', op).lower()))
    off += cons if cons else 1
addrs = [x[0] for x in insns]

# ---- 函数起点集合：仅用 call 直接目标 ----
calltargets = set()
for a, sz, mn, op in insns:
    if mn == 'call' and re.fullmatch(r'0x[0-9a-f]+', op):
        calltargets.add(int(op, 16))
ctsorted = sorted(calltargets)


def func_start(w):
    i = bisect.bisect_right(ctsorted, w) - 1
    return ctsorted[i] if i >= 0 else None


def strip_size(s):
    return re.sub(r'^(dword|word|byte|qword)ptr', '', s)


# ---- 识别指令边界命中 / 写入点 ----
boundary_hits = [(a, mn, op) for (a, sz, mn, op) in insns
                 if '%08x' % TARGET in op or '0x%x' % TARGET in op]
writes = []
for (a, sz, mn, op) in insns:
    parts = op.split(',')
    dst = strip_size(parts[0])
    if dst == '[0x%x]' % TARGET:
        writes.append((a, mn, op, parts[1] if len(parts) > 1 else ''))

# ============================================================
# 函数内前向数据流：三值格 ZERO(0) / NONZERO(1) / UNKNOWN(2)
# 汇合(meet)取交：相同保留，不同->UNKNOWN
# ============================================================
ZERO, NONZERO, UNK = 0, 1, 2
REGS = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')


def meet(x, y):
    """x/y 可为 None(TOP/未访问) 或 ZERO/NONZERO/UNK。"""
    if x is None:
        return y
    if y is None:
        return x
    return x if x == y else UNK


def parse_int(t):
    try:
        return int(t, 0) & 0xFFFFFFFF
    except Exception:
        return None


# 取函数 [fs, 下一个函数起点) 的指令切片（仅 call 目标切函数，避免 jmp 目标误判）
def func_slice(fs):
    nxt = ctsorted[bisect.bisect_right(ctsorted, fs)]
    lo = bisect.bisect_left(addrs, fs)
    hi = bisect.bisect_left(addrs, nxt)
    return insns[lo:hi]


def transfer(ins, state):
    """按指令语义返回 out-state（不可变新 dict）。"""
    a, sz, mn, op = ins
    st = dict(state)
    parts = op.split(',')
    # call / ret：caller-saved 全部 UNK；不影响 ebx/esi/edi/ebp（callee-saved）
    if mn == 'call':
        for r in ('eax', 'ecx', 'edx'):
            st[r] = UNK
        return st
    dst = parts[0] if parts else ''
    src = parts[1] if len(parts) > 1 else ''
    dr = dst if dst in REGS else None
    if mn == 'mov':
        if dr:
            if src in REGS:
                st[dr] = st.get(src, UNK)
            else:
                v = parse_int(src)
                st[dr] = ZERO if v == 0 else (NONZERO if v is not None else UNK)
        else:
            # mov [mem], reg —— 写入点本身不改寄存器
            pass
    elif mn == 'xor':
        if dr and src == dr:
            st[dr] = ZERO
        elif dr:
            st[dr] = UNK
    elif mn in ('pop',):
        if dr:
            st[dr] = UNK
    elif mn in ('add', 'sub', 'and', 'or', 'inc', 'dec', 'neg', 'not',
                'shl', 'shr', 'sar', 'imul'):
        if dr and dr in REGS:
            st[dr] = UNK
    elif mn == 'lea':
        if dr:
            st[dr] = NONZERO  # 地址常量恒非 0
    elif mn == 'movzx' or mn == 'movsx':
        if dr:
            st[dr] = UNK
    return st


def solve_func(fs):
    """迭代 worklist 数据流。返回每个地址入口 in-state。"""
    sl = func_slice(fs)
    if not sl:
        return {}
    entries = {a: i for i, (a, sz, mn, op) in enumerate(sl)}
    by_addr = {a: ins for ins in sl for a in [ins[0]]}
    succ = []
    for (a, sz, mn, op) in sl:
        nxt = a + sz
        # 无条件 jmp / ret 无 fall-through；条件跳转有 fall-through
        unconditional = (mn == 'jmp' or mn == 'ret')
        s = [] if unconditional else ([nxt] if nxt in entries else [])
        # 条件/无条件跳转：目标为后继（直接地址）
        if mn in ('jmp', 'jne', 'je', 'jz', 'jnz', 'jg', 'jge', 'jl', 'jle',
                  'ja', 'jae', 'jb', 'jbe', 'jc', 'jnc', 'jo', 'jno', 'js', 'jns'):
            t = parse_int(op)
            if t is not None and t in entries:
                s.append(t)
        succ.append(s)
    # 初始化：入口块全 UNK；其余为 None(TOP/未访问)，meet 时跳过
    IN = {a: None for a in entries}
    IN[fs] = {r: UNK for r in REGS}
    changed = True
    iters = 0
    while changed and iters < 200:
        changed = False
        iters += 1
        for i, (a, sz, mn, op) in enumerate(sl):
            cur = IN[a]
            if cur is None:
                continue  # 尚未从入口到达
            out = transfer((a, sz, mn, op), cur)
            for t in succ[i]:
                if t not in IN:
                    continue
                base = IN[t] if IN[t] is not None else out
                merged = {r: meet(base[r], out[r]) for r in REGS}
                if IN[t] is None or merged != IN[t]:
                    IN[t] = merged
                    changed = True
    return IN, iters


def state_at(write_addr):
    fs = func_start(write_addr)
    IN, iters = solve_func(fs)
    st = IN.get(write_addr) or {r: UNK for r in REGS}
    return fs, st, iters


# ---- 结果汇总 ----
results = []
for (a, mn, op, src) in writes:
    fs, st, iters = state_at(a)
    src = src.strip()
    verdict = st.get(src, UNK) if src in REGS else UNK
    results.append({
        'write_va': a, 'mnemonic': mn, 'operands': op, 'src': src,
        'func_start': fs, 'src_state_at_write': verdict,
        'state_name': {ZERO: 'ZERO', NONZERO: 'NONZERO', UNK: 'UNKNOWN'}[verdict],
        'dataflow_iters': iters,
        'in_state': {r: {ZERO: 'Z', NONZERO: 'N', UNK: 'U'}[st.get(r, UNK)] for r in REGS},
    })

byte_target = byte_hits(TARGET)
byte_pos = byte_hits(POSADDR)
byte_negs = {hex(x): len(byte_hits(x)) for x in NEGADDRS}
ctrl = next((r for r in results if r['write_va'] == CTRL_WRITE), None)

summary = {
    'BYTE_TARGET_COUNT': len(byte_target),
    'BYTE_TARGET_SECTIONS': dict(collections.Counter(
        next((nm for nm, ava, vs, raw, rs in b.secs if raw <= o < raw + rs), '?')
        for o in byte_target)),
    'BOUNDARY_HIT_COUNT': len(boundary_hits),
    'BYTE_EQ_BOUNDARY': len(byte_target) == len(boundary_hits),
    'WRITE_COUNT': len(writes),
    'WRITES': results,
    'POS_0x886380_COUNT': len(byte_pos),
    'NEG_COUNTS': byte_negs,
    'CTRL_0x52BAD8': {
        'src': ctrl['src'] if ctrl else None,
        'state': ctrl['state_name'] if ctrl else None,
        'is_zero': ctrl['src_state_at_write'] == ZERO if ctrl else None,
        'pass': (ctrl is not None and ctrl['src_state_at_write'] != ZERO),
    },
    'ALL_WRITES_ZERO': all(r['src_state_at_write'] == ZERO for r in results),
}
print(json.dumps(summary, indent=2))
with open('/home/t628/projects/ra2-campaign-forge/_r147/r147x_exec_scan.json', 'w') as f:
    json.dump(summary, f, indent=2)
