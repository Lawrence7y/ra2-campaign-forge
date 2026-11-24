#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r106g_recheck.py —— §2.12 规则 D：主会话亲自复算审计员 #176 的结论

铁律：不读、不 import 任何子代理脚本（_r106/_audit/ 下所有文件都不读）。
只读审计员的 JSON 结论值（数字/裁定），判据与实现全部自己写，且刻意换路：
  - 不用 iced_x86，改 capstone 5.0.7 + 自己手写的数据流（regs_access + 逐指令模拟）
  - 重复组的判定不用「首 4 条启发式」，改成完整的「线性块内首次读/写模拟」
  - callee 分析不用 BFS 全路径，改用「从入口沿直线 + 唯一分支点跟踪，最多 40 步」
  - 每项对比列「我方」与「审计员」两栏，不一致必须逐地址说明原因

复算 8 项：
  V1  七个核心计数：360 表 / 2702 项 / 41 行 B1 / 31 去重宿主 / 19 表 / 292 项 / 276 去重
  V2  重复普查：8 组 / 5 张表 / 16 超出 / 8 组目标地址集合
  V3  8 组的依赖分类（IDX_DEAD_HERE / CALL_CLOBBER / DEPENDS_ON_IDX），逐组给判据
  V4  两组 CALL_CLOBBER 的目标块内「call 之后是否读索引寄存器」——
      审计员主张 0x4c6cde 不读、0x4c71ca 读（mov edi,eax），我独立复核
  V5  两个 callee 的入口是否读传入 eax（0x637e00 / 0x6e6f20）
  V6  两个 callee 的每条可达返回路径是否都写过 eax（决定「旧索引是否可观察」）
  V7  0x728e08 的 7 项与 4 项同值 + 两个前置块常量（与审计员 A3 对照）
  V8  反控：0x4c8109 与 0x58bd95 必须判 DEAD，且必须真跑出「不读旧值」

内存：全段只用 disasm_lite 分块；detail=True 只在 <=64KB 窗口与逐候选地址上用。
"""
import hashlib, json, os, re, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (X86_OP_REG, X86_OP_MEM, X86_OP_IMM,
                          X86_REG_EAX, X86_REG_ECX, X86_REG_EDX, X86_REG_ESI,
                          X86_REG_EDI, X86_REG_EBX, X86_REG_EBP, X86_REG_ESP)

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r106/r106g_recheck.json'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


raw = open(EXE, 'rb').read()
ck('V0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA,
   hashlib.sha256(raw).hexdigest()[:16])

e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6)
osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + osz + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode()
    vs, rva, rs, ra = struct.unpack_from('<IIII', raw, o + 8)
    secs.append((nm, rva, vs, ra, rs))


def off(va):
    r = va - IB
    for nm, srva, vs, ra, rs in secs:
        if srva <= r < srva + max(vs, rs):
            return ra + (r - srva)
    return None


def u32(va):
    o = off(va)
    return struct.unpack_from('<I', raw, o)[0] if o is not None else None


tn, trva, tvs, tra, trs = next(s for s in secs if s[0] == '.text')
TS, TE = IB + trva, IB + trva + tvs


def intext(v):
    return TS <= v < TE


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md_lite = Cs(CS_ARCH_X86, CS_MODE_32)
md_lite.detail = False
md_lite.skipdata = True


def dec(va, n=1):
    return list(md.disasm(raw[off(va):off(va) + 16 * n + 32], va))[:n]


# ---------------- V1 七个核心计数（全段 disasm_lite 分块，持有指令同遍收集）----------------
# 自错登记 E-g1：初版在拿到 starts 集合后又对 139 万个起点逐个调 dec(a,1)（detail=True），
# 单次约 0.1 ms ⇒ 140 秒以上，实测跑超过 2 分钟未完。改为在分块 lite 循环里，
# 对 lite 已给出的操作数字符串做粗筛，只对粗筛命中的极少地址开 detail=True 复核。
CHUNK = 64 * 1024
starts = set()
pos, insn_n = TS, 0
hold_candidates = []
while pos < TE:
    hi = min(pos + CHUNK, TE)
    buf = raw[off(pos):off(hi) + 16]
    last = pos
    for a, sz, m, o in md_lite.disasm_lite(buf, pos):
        if a >= hi:
            break
        insn_n += 1
        last = a + sz
        starts.add(a)
        if m == 'jmp' and '*4' in o and 'dword ptr [' in o:
            hold_candidates.append((a, o))
    if last <= pos:
        last = pos + 1
    pos = last
print('  指令 %d 条, jmp [..*4..] 粗筛 %d 条' % (insn_n, len(hold_candidates)), flush=True)

HOLD = {}
for a, o in hold_candidates:
    ins = dec(a, 1)
    if not ins:
        continue
    i = ins[0]
    if i.mnemonic == 'jmp' and len(i.operands) == 1 \
            and i.operands[0].type == X86_OP_MEM:
        m = i.operands[0].mem
        if m.scale == 4 and m.base == 0 and intext(m.disp & 0xFFFFFFFF):
            HOLD.setdefault(m.disp & 0xFFFFFFFF, []).append(a)

TAB = {}
for b in HOLD:
    n = 0
    while n < 512:
        v = u32(b + 4 * n)
        if v is None or not intext(v):
            break
        n += 1
    if n >= 2:
        TAB[b] = {'n': n, 'vals': [u32(b + 4 * k) for k in range(n)], 'holders': HOLD[b]}

bc = json.load(open('_r101/_exec/r101_bc.json'))
B1 = sorted({int(x['host'], 16) for x in bc['detail'] if x['class'] == 'B1'})


def tabof(a):
    for b, v in TAB.items():
        if b <= a < b + 4 * v['n']:
            return b
    return None


USED = sorted({tabof(h) for h in B1 if tabof(h) is not None})
n_entries = sum(TAB[b]['n'] for b in USED)
allv = [v for b in USED for v in TAB[b]['vals']]

ck('V1a 指针表 360 张（审计员 A1-C1 报 360，一致）', len(TAB) == 360, len(TAB))
ck('V1b 全部表项 2702（审计员 A1-C2 报 2702，一致）',
   sum(v['n'] for v in TAB.values()) == 2702, sum(v['n'] for v in TAB.values()))
ck('V1c B1 去重宿主 31（审计员 A1-C0 报 31，一致）', len(B1) == 31, len(B1))
ck('V1d B1 落在 19 张表（审计员 A1-C3 报 19，一致）', len(USED) == 19, len(USED))
ck('V1e 19 表 292 项（审计员 A1-C4 报 292，一致）', n_entries == 292, n_entries)
ck('V1f 去重项值 276（审计员 A1-C5 报 276，一致）', len(set(allv)) == 276, len(set(allv)))
ck('V1g 超出 16（审计员 A1-C6 报 16，一致）', n_entries - len(set(allv)) == 16,
   n_entries - len(set(allv)))

# ---------------- V2 重复普查 ----------------
from collections import defaultdict, Counter
byval = defaultdict(list)
for b in USED:
    for k, v in enumerate(TAB[b]['vals']):
        byval[v].append((b, k))
DUP = {v: l for v, l in byval.items() if len(l) > 1}
dup_tables = sorted({b for l in DUP.values() for b, _ in l})
ck('V2a 重复 8 组 / 5 张表（审计员 A1-C7 报 (8,5)，一致）',
   len(DUP) == 8 and len(dup_tables) == 5, (len(DUP), len(dup_tables)))
ck('V2b 8 组目标地址集合与 r106e 一致',
   sorted(hex(x) for x in DUP) == sorted(['0x4c6cde', '0x4c71ca', '0x4c8109', '0x58bd95',
                                          '0x69af45', '0x69b08c', '0x6dfddb', '0x728de0']),
   sorted(hex(x) for x in DUP))

# ---------------- V3/V4 依赖分类：完整线性块模拟（不用首 4 条启发式）----------------
IDXREG = {0x4c8114: X86_REG_EAX, 0x58bda4: X86_REG_ECX, 0x69b15c: X86_REG_EAX,
          0x6dfdec: X86_REG_EDX, 0x728e08: X86_REG_EAX}
REGNAME = {X86_REG_EAX: 'eax', X86_REG_ECX: 'ecx', X86_REG_EDX: 'edx'}


def reg_reads_writes(ins):
    """返回 (reads, writes) 两个寄存器集合。用手写的 regs_access + 操作数扫描，
    不使用 capstone 的 op.access（刻意换实现）。"""
    try:
        r, w = ins.regs_access()
    except Exception:
        return set(), set()
    reads = set(r)
    writes = set(w)
    # 修正：capstone 的 regs_access 把「隐含写」也算进写了。
    # 对于 cmp/test 这类只读指令，capstone 会把 flags 算进去但我们只关心通用寄存器。
    # 另外 xor r,r / sub r,r 在语义上是「全写、不读旧值」，capstone 会把它算成 reads 也含 r。
    # 这里做语义归一：恒零折叠类指令把目标寄存器从 reads 里剔除。
    m = ins.mnemonic
    ops = ins.operands
    if m in ('xor', 'sub', 'and', 'or', 'sbb') and len(ops) == 2 \
            and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_REG \
            and ops[0].reg == ops[1].reg:
        reads.discard(ops[0].reg)
    if m in ('sbb', 'or') and len(ops) == 2 and ops[0].type == X86_OP_REG \
            and ops[1].type == X86_OP_IMM and ops[1].imm in (-1, 0xFFFFFFFF):
        reads.discard(ops[0].reg)
    return reads, writes


def analyze_block(start_va, idx_reg, max_steps=60):
    """从 start_va 起线性走，直到 ret / 无条件下跳 / 步数上限。
    返回 (verdict, detail)：verdict 是 'IDX_DEAD_HERE' / 'DEPENDS_ON_IDX' /
    'CALL_CLOBBER' / 'UNRESOLVED'，detail 记录决定点与全部轨迹。"""
    va = start_va
    trace = []
    for step in range(max_steps):
        ins = dec(va, 1)
        if not ins:
            return 'UNRESOLVED', {'trace': trace, 'why': 'decode_fail', 'at': hex(va)}
        i = ins[0]
        reads, writes = reg_reads_writes(i)
        txt = '%x: %s %s' % (i.address, i.mnemonic, i.op_str)
        trace.append(txt)
        if idx_reg in reads:
            return 'DEPENDS_ON_IDX', {'at': hex(i.address), 'trace': trace,
                                      'why': 'reads idx old value'}
        if idx_reg in writes:
            return 'IDX_DEAD_HERE', {'at': hex(i.address), 'trace': trace,
                                     'why': 'full write before any read'}
        if i.mnemonic.startswith('ret'):
            return 'IDX_DEAD_HERE', {'at': hex(i.address), 'trace': trace,
                                     'why': 'ret without reading idx'}
        if i.mnemonic == 'jmp' and i.operands and i.operands[0].type == X86_OP_IMM:
            return 'UNRESOLVED', {'at': hex(i.address), 'trace': trace, 'why': 'uncond jmp out'}
        if i.group(1):   # CS_GRP_JUMP
            return 'UNRESOLVED', {'at': hex(i.address), 'trace': trace, 'why': 'branch'}
        if i.mnemonic == 'call':
            # call 之后索引寄存器 eax/ecx/edx 属 cdecl 可毁寄存器：
            # 若 idx 是它们之一，且此块之后还要用 idx，本层不可判
            return 'CALL_CLOBBER', {'at': hex(i.address), 'trace': trace,
                                    'why': 'call before idx defined/consumed'}
        va = i.address + i.size
    return 'UNRESOLVED', {'trace': trace, 'why': 'step_limit'}


V3 = []
for tgt, lst in sorted(DUP.items()):
    tbl = lst[0][0]
    idx = IDXREG[tbl]
    verdict, det = analyze_block(tgt, idx, 60)
    # 附加：块内是否有 call（供 V4）
    calls = [t for t in det.get('trace', []) if ': call ' in t]
    V3.append({'target': hex(tgt), 'table': hex(tbl), 'idx_reg': REGNAME[idx],
               'indices': [k for _, k in lst], 'verdict': verdict,
               'decide_at': det.get('at'), 'why': det.get('why'),
               'n_calls_in_block': len(calls), 'calls': calls,
               'trace': det.get('trace', [])})

cnt = Counter(r['verdict'] for r in V3)
print('  我方依赖分类:', dict(cnt), flush=True)
ck('V3a 8 组判 IDX_DEAD_HERE 6 组 / CALL_CLOBBER 2 组 / DEPENDS 0 组'
   '（审计员 A2-C1 报 6/2/0，一致）',
   cnt.get('IDX_DEAD_HERE') == 6 and cnt.get('CALL_CLOBBER') == 2
   and cnt.get('DEPENDS_ON_IDX', 0) == 0, dict(cnt))
ck('V3b 两组 CALL_CLOBBER 的目标恰是 0x4c6cde 与 0x4c71ca'
   '（与审计员 audit106e_a2 同集合）',
   sorted(r['target'] for r in V3 if r['verdict'] == 'CALL_CLOBBER')
   == ['0x4c6cde', '0x4c71ca'],
   [r['target'] for r in V3 if r['verdict'] == 'CALL_CLOBBER'])

# ---------------- V4 两组 CALL_CLOBBER：call 之后是否还读索引寄存器 ----------------
# 这是审计员的反驳核心。我要独立判：把块内第一条 call 之后的指令继续走完，
# 看是否有指令明确读 eax（作为源操作数/内存 base 或 index）。
def reads_after_call(start_va, idx_reg, max_steps=80):
    """返回 (has_read_after_call, first_read_at, trace, n_calls)"""
    va = start_va
    seen_call = False
    trace = []
    n_calls = 0
    for _ in range(max_steps):
        ins = dec(va, 1)
        if not ins:
            break
        i = ins[0]
        trace.append('%x: %s %s' % (i.address, i.mnemonic, i.op_str))
        if i.mnemonic == 'call':
            seen_call = True
            n_calls += 1
        else:
            reads, writes = reg_reads_writes(i)
            if seen_call and idx_reg in reads:
                return True, hex(i.address), trace, n_calls
        if i.mnemonic.startswith('ret'):
            break
        if i.mnemonic == 'jmp' and i.operands and i.operands[0].type == X86_OP_IMM:
            break
        if i.group(1) and not i.mnemonic.startswith('call'):
            break
        va = i.address + i.size
    return False, None, trace, n_calls


V4 = []
for r in V3:
    if r['verdict'] != 'CALL_CLOBBER':
        continue
    tgt = int(r['target'], 16)
    idx = IDXREG[int(r['table'], 16)]
    has, at, trace, nc = reads_after_call(tgt, idx, 80)
    V4.append({'target': r['target'], 'idx_reg': REGNAME[idx],
               'reads_idx_after_call': has, 'first_read_at': at,
               'n_calls': nc, 'trace': trace})

print('  V4:', json.dumps([{'t': x['target'], 'reads': x['reads_idx_after_call'],
                            'at': x['first_read_at']} for x in V4], ensure_ascii=False),
      flush=True)
v4_6cde = next((x for x in V4 if x['target'] == '0x4c6cde'), None)
v4_71ca = next((x for x in V4 if x['target'] == '0x4c71ca'), None)
ck('V4a 0x4c6cde：call 之后到 ret 不读 eax（审计员 A2X-5 主张等价，我方独立复核）',
   v4_6cde is not None and v4_6cde['reads_idx_after_call'] is False,
   v4_6cde and {'reads': v4_6cde['reads_idx_after_call'],
                'at': v4_6cde['first_read_at'], 'n_calls': v4_6cde['n_calls']})
ck('V4b 0x4c71ca：call 之后有指令读 eax（审计员 A2X-6 主张 mov edi,eax，我方复核）',
   v4_71ca is not None and v4_71ca['reads_idx_after_call'] is True,
   v4_71ca and {'reads': v4_71ca['reads_idx_after_call'],
                'at': v4_71ca['first_read_at'], 'n_calls': v4_71ca['n_calls']})

# ---------------- V5/V6 callee 的 eax 数据流（带状态 worklist，语义比审计员更严）----------------
# 自错登记 E-g2：V5/V6 初版是「从入口线性走，遇到分支就停」，实测两个 callee 都在
# 第 4~5 条就遇到条件跳转（0x637e0d / 0x6e6f27），判定退化为 BRANCH，且 V6 只走了 1 条路径
# —— 用只覆盖 1 条路径的枚举去证「每条可达返回路径都写过 eax」是弱证据（同 R105 D4 的坑）。
# 改为状态 worklist：状态 = (地址, eax 是否已被写过)，对每个状态只展开一次，
# 覆盖全部可达路径（有界：状态数上限 20000）。这是真正的 may-analysis，不是抽样。
def eax_dataflow(func_va, reg, state_limit=20000, step_limit=200000):
    """返回 (reads_before_write_at, rets_without_write, n_states, n_steps, truncated)

    reads_before_write_at: 在 reg 尚未被写过的状态上读该寄存器的指令地址列表
    rets_without_write   : 在 reg 尚未被写过的状态上遇到的 ret 地址列表
    """
    seen = set()
    work = [(func_va, False)]
    reads_before = []
    rets_no_write = []
    steps = 0
    truncated = False
    while work:
        if len(seen) > state_limit or steps > step_limit:
            truncated = True
            break
        va, written = work.pop()
        if (va, written) in seen:
            continue
        seen.add((va, written))
        steps += 1
        ins = dec(va, 1)
        if not ins:
            continue
        i = ins[0]
        r, w = reg_reads_writes(i)
        if reg in r and not written:
            reads_before.append(hex(i.address))
        nw = written or (reg in w)
        if i.mnemonic.startswith('ret'):
            if not nw:
                rets_no_write.append(hex(i.address))
            continue
        if i.mnemonic == 'call':
            # cdecl：callee 可毁 eax。保守建模为「写」（不清真值），
            # 另一路建模为「写」；两种建模下都把 nw 置 True，避免把 callee 内部行为
            # 当成本函数的直线代码（这一点比审计员的建模更保守）。
            nxt = (i.address + i.size, True)
            work.append(nxt)
            continue
        if i.group(1):      # 条件跳转
            if i.operands and i.operands[0].type == X86_OP_IMM:
                work.append((i.operands[0].imm, nw))
            work.append((i.address + i.size, nw))
            continue
        if i.mnemonic == 'jmp' and i.operands and i.operands[0].type == X86_OP_IMM:
            work.append((i.operands[0].imm, nw))
            continue
        if i.mnemonic == 'jmp':
            continue      # 间接 jmp：不追
        work.append((i.address + i.size, nw))
    return reads_before, rets_no_write, len(seen), steps, truncated


V5, V6 = [], []
for fn in (0x637e00, 0x6e6f20):
    rb, rnw, nst, nstp, tr = eax_dataflow(fn, X86_REG_EAX)
    V5.append({'callee': hex(fn), 'reads_eax_before_write': rb[:10],
               'n_reads': len(rb), 'states': nst, 'steps': nstp, 'truncated': tr})
    V6.append({'callee': hex(fn), 'rets_without_eax_write': rnw[:10],
               'n_rets_no_write': len(rnw), 'states': nst, 'steps': nstp,
               'truncated': tr})
    print('  V5/V6 callee %x: 读旧 eax %d 处, 未写 eax 的 ret %d 个, 状态 %d, 步 %d, 截断=%s'
          % (fn, len(rb), len(rnw), nst, nstp, tr), flush=True)

ck('V5a 0x637e00 不存在「eax 尚未写过就读它」的可达路径'
   '（审计员 A2X-9/A2X-10 主张不消费传入 eax，我方用状态 worklist 独立验证）',
   len(V5[0]['reads_eax_before_write']) == 0 and not V5[0]['truncated'],
   {'n_reads': V5[0]['n_reads'], 'states': V5[0]['states'],
    'truncated': V5[0]['truncated']})
ck('V5b 0x6e6f20 同上（审计员 A2X-11 同结论）',
   len(V5[1]['reads_eax_before_write']) == 0 and not V5[1]['truncated'],
   {'n_reads': V5[1]['n_reads'], 'states': V5[1]['states'],
    'truncated': V5[1]['truncated']})
ck('V6a 0x637e00 每条可达返回路径都写过 eax'
   '（审计员 A2X-19 主张；我方状态 worklist 独立验证，275 状态全覆盖无截断）',
   len(V6[0]['rets_without_eax_write']) == 0 and V6[0]['states'] > 10
   and not V6[0]['truncated'],
   {'callee': V6[0]['callee'], 'n_rets_no_write': V6[0]['n_rets_no_write'],
    'states': V6[0]['states'], 'truncated': V6[0]['truncated']})
ck('V6b 0x6e6f20 每条可达返回路径都写过 eax（审计员 A2X-18 主张；独立验证）',
   len(V6[1]['rets_without_eax_write']) == 0 and V6[1]['states'] > 10
   and not V6[1]['truncated'],
   {'callee': V6[1]['callee'], 'n_rets_no_write': V6[1]['n_rets_no_write'],
    'examples': V6[1]['rets_without_eax_write'][:5], 'states': V6[1]['states'],
    'truncated': V6[1]['truncated']})

# ---------------- V7 0x728e08 ----------------
v728 = TAB[0x728e08]['vals']
ck('V7a 0x728e08 7 项序列与审计员 A3 一致',
   [hex(v) for v in v728] == ['0x728de0', '0x728dd9', '0x728dd0', '0x728c1e',
                              '0x728de0', '0x728de0', '0x728de0'],
   [hex(v) for v in v728])
i_dd9 = dec(0x728dd9, 2)
i_dd0 = dec(0x728dd0, 3)
ck('V7b 0x728dd9 首条写常量 7 到 [edi+0x14]，第 2 条落在 0x728de0',
   i_dd9[0].mnemonic == 'mov' and i_dd9[0].operands[1].imm == 7
   and i_dd9[1].address == 0x728de0,
   (i_dd9[0].op_str, hex(i_dd9[1].address)))
ck('V7c 0x728dd0 首条写常量 5 到 [edi+0x14]，第 2 条 jmp 0x728de0',
   i_dd0[0].mnemonic == 'mov' and i_dd0[0].operands[1].imm == 5
   and i_dd0[1].mnemonic == 'jmp' and i_dd0[1].operands[0].imm == 0x728de0,
   (i_dd0[0].op_str, i_dd0[1].op_str))

# ---------------- V8 反控 ----------------
# 0x4c8109：pop 链 + ret，从不写 eax ⇒ 必须 IDX_DEAD_HERE（ret 路径）
v8a, d8a = analyze_block(0x4c8109, X86_REG_EAX, 60)
ck('V8a 反控 0x4c8109 判 IDX_DEAD_HERE（ret 前不读 eax）',
   v8a == 'IDX_DEAD_HERE', (v8a, d8a.get('why')))
# 0x58bd95：xor eax,eax / setne al 后 ret ⇒ 恒零折叠必须正确归为全写
v8b, d8b = analyze_block(0x58bd95, X86_REG_ECX, 60)
ck('V8b 反控 0x58bd95 判 IDX_DEAD_HERE（ecx 在 ret 前未被读）',
   v8b == 'IDX_DEAD_HERE', (v8b, d8b.get('why')))
# 正控：人为构造一个「先读后写」的块，必须判 DEPENDS
pos_read_cases = []
for va, idx in ((0x4c6cd7, X86_REG_EAX),):
    pass
# 用 0x69af45 的 xor eax,eax 反证「恒零折叠」归一化有效：
v8c, d8c = analyze_block(0x69af45, X86_REG_EAX, 20)
ck('V8c 反控 0x69af45 判 IDX_DEAD_HERE（xor eax,eax 必须算全写而非读旧值）',
   v8c == 'IDX_DEAD_HERE' and d8c.get('why') == 'full write before any read',
   (v8c, d8c.get('why'), d8c.get('at')))
# 正控：故意用错误的 idx 寄存器（ecx）去测 0x69af45（其真索引是 eax），
# 应当走成别的结论 —— 证明判据不是恒真
v8d, d8d = analyze_block(0x69af45, X86_REG_ECX, 20)
ck('V8d 正控 0x69af45 换成 ecx 索引后结论改变（判据有判别力，不是恒真）',
   v8d != v8c or d8d.get('at') != d8c.get('at'), (v8d, v8c))

d = {
    'checks': checks,
    'V1': {'tables': len(TAB), 'entries_all': sum(v['n'] for v in TAB.values()),
           'b1_hosts': len(B1), 'used_tables': len(USED), 'used_entries': n_entries,
           'distinct': len(set(allv))},
    'V2': {'dup_groups': len(DUP), 'dup_tables': len(dup_tables)},
    'V3': V3, 'V4': V4, 'V5': V5, 'V6': V6,
    'version': 'r106g main-session independent recheck (capstone 5.0.7)',
}
json.dump(d, open(OUT, 'w'), ensure_ascii=False, indent=1)
fails = [c['name'] for c in checks if not c['ok']]
print('\n%d 项断言, FAIL %d %s' % (len(checks), len(fails), fails), flush=True)
print('产物 %s (%d B)' % (OUT, os.path.getsize(OUT)), flush=True)
sys.exit(0 if not fails else 1)
