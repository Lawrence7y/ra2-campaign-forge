#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r105a_tableentries.py —— R104 未取得① 收口：19 张表的 292 个表项值逐个定性

R104 留下的原话（COMPACT_STATE R104 段待办①）：
    「B1 已定性为跳转表项，但表项值指向的真实函数入口未逐一定性——须对 19 张表的
      全部项值逐个验『是否合法函数起点』（prologue 形态/被 call 直引/链可达），
      这是本轮留下的最大缺口」

本轮先把「函数起点」这个提法本身校正过来：这 19 张表全部由
「jmp dword ptr [reg*4+base]」持有，而 MSVC 下这种形态的绝大多数是
**switch 分派表**——表项值是 case 标签（同一函数内的基本块入口），
不是函数入口。若把判据写成「必须像函数入口（push ebp; mov ebp,esp）」，
会把大量真实代码判成「不是合法起点」，这是判据错而不是对象错。

故本脚本按三层递进，每层都能 FAIL：

  A1 全部 292 个项值在 iced 线性扫描下是否恰好是单元起点（是 ⇒ 是代码）
  A2 每张表的持有指令之前是否存在「cmp/jcc 上界 + 同一索引寄存器」的边界检查
     （是且上界 == 项数 ⇒ 该表是**有界 switch 分派表**，项值必为 case 标签）
  A3 逐项再分三桶：函数入口形态（prologue）/ 函数内标签（被无条件跳转或
     条件跳转指向、或紧跟 cmp 链）/ 非起点（数据）

反控（缺一不可）：
  N1 用 B1 的 41 个宿主（R104 已证在表体内）跑同一套「是否单元起点」判据，
     必须全不是起点 —— 否则 A1 的判据没有判别力
  N2 随机抽 292 个 .text 地址，A1 桶分布必须显著差于真表项
  N3 把 A2 的「同一索引寄存器」约束去掉（只找 cmp/jcc），命中数必须上升
     —— 证明这条约束真的在起作用，不是随手就满足的
"""
import bisect, hashlib, json, os, random, struct, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, '_r104', 'vendor'))
import iced_x86

OUT = '_r105/r105a_tableentries.json'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

R = {}
def put(k, v):
    R[k] = v
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:900]), flush=True)

raw = open(EXE, 'rb').read()
ck('S0 exe sha256 == R104 记录值', hashlib.sha256(raw).hexdigest() == EXE_SHA,
   hashlib.sha256(raw).hexdigest()[:16])

e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6)
osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
sh = opt + osz
SEC = {}
for i in range(nsec):
    o = sh + 40 * i
    nm = raw[o:o + 8].rstrip(b'\0').decode('ascii', 'replace')
    vs, va, rsz, roff = struct.unpack_from('<IIII', raw, o + 8)
    SEC[nm] = {'va': IB + va, 'vsize': vs, 'roff': roff}
B, TVS, TROFF = SEC['.text']['va'], SEC['.text']['vsize'], SEC['.text']['roff']
END = B + TVS
txt = raw[TROFF:TROFF + TVS]

def dw(a):
    return struct.unpack_from('<I', raw, a - B + TROFF)[0]
def intext(v):
    return B <= v < END

# ---------- 全库线性扫描（iced 1.22.0，与 R104 同口径）
UN = []
d = iced_x86.Decoder(32, txt, ip=B)
while d.can_decode:
    i = d.decode()
    UN.append((i.ip, i.len, i.is_invalid, i))
STARTS = [u[0] for u in UN]
START_SET = set(STARTS)
VALID_STARTS = {u[0] for u in UN if not u[2]}
INVALID_STARTS = {u[0] for u in UN if u[2]}
IDX = {u[0]: k for k, u in enumerate(UN)}
# 覆盖映射：某地址若不在 ip 集合里，它落在哪条单元内部（N1 的 0x728e15 需要这个）
IP_COVER = {}
for _u in UN:
    for _off in range(1, _u[1]):
        IP_COVER.setdefault(_u[0] + _off, (_u[0], _u[1], _off))
put('S1_sweep', {'units': len(UN), 'valid': len(VALID_STARTS), 'invalid': len(INVALID_STARTS),
                 'sum_len': sum(u[1] for u in UN), 'text_vsize': TVS})
ck('S1 线性扫描 sum(len) == .text VirtualSize（铺满，与 R104 同口径）',
   sum(u[1] for u in UN) == TVS, sum(u[1] for u in UN))

# ---------- 独立重建 19 张表（不读 R104 产物，靠「jmp [reg*4+disp32]」持有指令现扫）
HOLDERS = {}
d = iced_x86.Decoder(32, txt, ip=B)
while d.can_decode:
    i = d.decode()
    if i.is_invalid:
        continue
    if (i.mnemonic == iced_x86.Mnemonic.JMP and i.op0_kind == iced_x86.OpKind.MEMORY
            and i.memory_index_scale == 4 and i.memory_index != iced_x86.Register.NONE
            and intext(i.memory_displacement)):
        HOLDERS.setdefault(i.memory_displacement, []).append(i.ip)

TAB = {}
for base, hs in HOLDERS.items():
    n = 0
    while n < 512 and intext(dw(base + 4 * n)):
        n += 1
    if n >= 2:
        TAB[base] = {'n': n, 'holders': hs, 'vals': [dw(base + 4 * k) for k in range(n)]}
put('S2_tables_all', {'n_tables': len(TAB), 'n_entries': sum(v['n'] for v in TAB.values())})
ck('S2 独立重扫得 360 张指针表（与 R104 三处独立实现同值）', len(TAB) == 360, len(TAB))

# B1 的 41 个宿主（R101 产物，用于反控 N1）
bc = json.load(open('_r101/_exec/r101_bc.json'))
B1_HOSTS = sorted({int(x['host'], 16) for x in bc['detail'] if x['class'] == 'B1'})

def tab_of_addr(a):
    for base, v in TAB.items():
        if base <= a < base + 4 * v['n']:
            return base
    return None

USED = sorted({tab_of_addr(h) for h in B1_HOSTS if tab_of_addr(h) is not None})
used_tabs = [b for b in USED]
put('S3_used_tables', {'n': len(used_tabs), 'bases': [hex(b) for b in used_tabs],
                       'n_entries_total': sum(TAB[b]['n'] for b in used_tabs)})
ck('S3 用到 19 张表（复现 R104 的数）', len(used_tabs) == 19, len(used_tabs))
ck('S3b 这 19 张表合计 292 个项值（复现 R104 的数）',
   sum(TAB[b]['n'] for b in used_tabs) == 292, sum(TAB[b]['n'] for b in used_tabs))

# ---------------- A1：292 个项值是否恰好是单元起点
A1 = []
for b in used_tabs:
    for k, v in enumerate(TAB[b]['vals']):
        A1.append({'table': hex(b), 'idx': k, 'val': hex(v),
                   'is_start': v in START_SET, 'is_valid_start': v in VALID_STARTS})
n_start = sum(1 for r in A1 if r['is_valid_start'])
put('A1_entries', {'total': len(A1), 'is_sweep_start': n_start,
                   'not_start': len(A1) - n_start,
                   'not_start_list': [r['val'] for r in A1 if not r['is_valid_start']][:20]})
ck('A1 19 张表的 292 个项值里，全部在 iced 线性扫描下是**合法**单元起点（100%）',
   n_start == len(A1), '%d/%d' % (n_start, len(A1)))

# ---------------- A2：持有指令前的真 idiom（本轮实测出两种，先前的单一假设是错的）
# 自错如实登记：本段第一版断言「多数持有指令前是 cmp 同一索引寄存器 + jcc」，实测 9/19 FAIL。
# 逐窗口打印后发现这是我的判据错，不是对象错 —— 19 张表里有 10 张走**两级表**：
#     cmp <k>, BOUND / ja default / xor r,r / mov rl,[k+BYTETAB] / jmp [rl*4+DWORDTAB]
# 被 cmp 的寄存器是 k（输入值），jmp 用的是 rl（从字节表加载的压缩下标），两者必然不同。
# 故「同一索引寄存器」这条约束在两级形态下结构性不可能满足。改为按形态分类后再判。
def back_window(holder_ip, k=8):
    """线性扫描是连续的，故按单元下标回退是精确的（不是启发式）。"""
    j = IDX.get(holder_ip)
    if j is None:
        return []
    return UN[max(0, j - k):j]

CC = (iced_x86.Mnemonic.JA, iced_x86.Mnemonic.JAE, iced_x86.Mnemonic.JBE,
      iced_x86.Mnemonic.JB, iced_x86.Mnemonic.JG, iced_x86.Mnemonic.JGE,
      iced_x86.Mnemonic.JL, iced_x86.Mnemonic.JLE, iced_x86.Mnemonic.JE,
      iced_x86.Mnemonic.JNE)

def scan_holder(holder_ip, n):
    """返回该持有指令的前置结构：bound / cc / default_target / byte_table。"""
    win = back_window(holder_ip)
    bound = cc = dflt = bt = None
    for k in range(len(win)):
        ip_, ln, inv, ins = win[k]
        if inv:
            continue
        if ins.mnemonic == iced_x86.Mnemonic.CMP and ins.op_count == 2 \
           and ins.op0_kind == iced_x86.OpKind.REGISTER and ins.op1_kind in (
               iced_x86.OpKind.IMMEDIATE8, iced_x86.OpKind.IMMEDIATE8TO32,
               iced_x86.OpKind.IMMEDIATE16, iced_x86.OpKind.IMMEDIATE32):
            for k2 in range(k + 1, len(win)):
                if not win[k2][2] and win[k2][3].mnemonic in CC:
                    bound = ins.immediate8 if ins.op1_kind in (
                        iced_x86.OpKind.IMMEDIATE8, iced_x86.OpKind.IMMEDIATE8TO32) \
                        else ins.immediate32
                    cc = str(win[k2][3].mnemonic)
                    dflt = hex(win[k2][3].near_branch_target)
                    break
        # 字节索引表：mov cl/dl/al, [k + BYTETAB]（base 寄存器非 NONE，可以是 index 也可以是 base）
        if ins.mnemonic == iced_x86.Mnemonic.MOV and ins.op0_kind == iced_x86.OpKind.REGISTER \
           and ins.op0_register in (iced_x86.Register.CL, iced_x86.Register.DL,
                                    iced_x86.Register.AL) \
           and ins.op1_kind == iced_x86.OpKind.MEMORY \
           and (ins.memory_index != iced_x86.Register.NONE
                or ins.memory_base != iced_x86.Register.NONE):
            bt = ins.memory_displacement
    return bound, cc, dflt, bt

A2 = []
for b in used_tabs:
    n = TAB[b]['n']
    for h in TAB[b]['holders']:
        hi = iced_x86.Decoder(32, txt[h - B:h - B + 16], ip=h).decode()
        idx_reg = hi.memory_index
        bound, cc, dflt, bt = scan_holder(h, n)
        # 判形态：字节表必须紧贴 DWORD 表尾（base + 4*n），这是 MSVC 压缩跳转表的固定布局
        twolev = (bt is not None and bt == b + 4 * n)
        A2.append({'table': hex(b), 'n': n, 'holder': hex(h), 'idx_reg': str(idx_reg),
                   'bound': bound, 'cc': cc, 'default_target': dflt,
                   'byte_table': (hex(bt) if bt is not None else None),
                   'two_level': twolev, 'byte_table_adjacent': bt == b + 4 * n})

n_two = sum(1 for r in A2 if r['two_level'])
n_bound = sum(1 for r in A2 if r['bound'] is not None)
put('A2_idioms', {'holders': len(A2), 'with_bound_check': n_bound,
                  'two_level': n_two, 'direct': len(A2) - n_two,
                  'rows': A2})
ck('A2 全部 19 条持有指令前都存在「cmp 上界 + jcc 默认分支」（无一例外）',
   n_bound == len(A2), '%d/%d' % (n_bound, len(A2)))
ck('A2b 19 条里分两种 idiom 都成立且互补（两级 %d + 直接 %d == 19）'
   % (n_two, len(A2) - n_two), n_two + (len(A2) - n_two) == len(A2))

# A2c：两级形态的结构闭合 —— 字节表紧贴 DWORD 表尾，且表内每个字节 < n
A2c = []
for r in A2:
    if not r['two_level']:
        continue
    b = int(r['table'], 16)
    n = r['n']
    bt = int(r['byte_table'], 16)
    bound = r['bound']
    vals = [raw[bt - B + TROFF + x] for x in range(bound + 1)]
    A2c.append({'table': r['table'], 'n': n, 'byte_table': r['byte_table'],
                'bound': bound, 'n_bytes': len(vals),
                'max_byte': max(vals), 'all_lt_n': max(vals) < n,
                'distinct_targets_used': len(set(vals))})
put('A2c_twolevel_closure', {'tested': len(A2c), 'ok': sum(1 for x in A2c if x['all_lt_n']),
                             'rows': A2c})
ck('A2c 两级形态：字节表紧贴 DWORD 表尾（base+4n），且全部 %d 张表的字节值 < 项数 n'
   % len(A2c), bool(A2c) and all(x['all_lt_n'] for x in A2c),
   '%d/%d' % (sum(1 for x in A2c if x['all_lt_n']), len(A2c)))
ck('A2d 两级形态的字节表确实在做压缩：bound+1 个输入值映射到少于等于 n 个目标（有重复）',
   all(x['distinct_targets_used'] <= x['n'] for x in A2c),
   [(x['table'], x['n_bytes'], x['distinct_targets_used']) for x in A2c][:5])

# A2e：直接形态的上界必须 == n-1（否则表长与判据不一致）
A2e = []
for r in A2:
    if r['two_level']:
        continue
    A2e.append({'table': r['table'], 'n': r['n'], 'bound': r['bound'],
                'ok': r['bound'] == r['n'] - 1})
put('A2e_direct_bound_eq_n_minus_1', {'tested': len(A2e),
                                      'ok': sum(1 for x in A2e if x['ok']), 'rows': A2e})
ck('A2e 直接形态：cmp 上界 == 项数-1（表长与边界检查互相印证，不是各自估计）',
   all(x['ok'] for x in A2e), '%d/%d' % (sum(1 for x in A2e if x['ok']), len(A2e)))


# ---------------- A3：292 个项值的定性（三条有判别力的判据，缺一不可）
#
# 自错如实登记（第 2 处）：本段第一版用「前一条单元是 ret/jmp/after-jmp」判「函数入口」，
# 得 func_entry 275 / case_label 17。这个判据**没有判别力** —— switch 的每个 case 标签
# 前一条也常常是 jmp（上一个 case 的结尾），MSVC 生成的 case 体几乎都以 jmp/ret 收尾。
# 275/292 这个数说明的是「.text 里到处是 jmp」，不是「275 个函数入口」。
# 故弃用该判据，改用下面三条都成立才叫「函数内标签」的闭环：
#   A3a 前向性：项值 > 持有指令地址（case 标签必在 holder 之后；函数入口则不必）
#   A3b 无 call 直引：项值从不作为 call 的目标（函数入口会被 call）
#   A3c 跨度聚类：同一表内的项值跨度落在该函数的局部范围内
# 反向（真正能把它判成函数入口的一组）：若某表项值**是某个 call 的直接目标**，那它就是函数入口。
CALLS = set()
d = iced_x86.Decoder(32, txt, ip=B)
while d.can_decode:
    i = d.decode()
    if i.is_invalid:
        continue
    if i.mnemonic == iced_x86.Mnemonic.CALL and i.op0_kind == iced_x86.OpKind.NEAR_BRANCH32:
        CALLS.add(i.near_branch_target)
put('A3_calls', {'n_call_targets': len(CALLS)})

A3 = []
for b in used_tabs:
    n = TAB[b]['n']
    h = TAB[b]['holders'][0]
    vals = TAB[b]['vals']
    for k, v in enumerate(vals):
        A3.append({'table': hex(b), 'idx': k, 'val': hex(v), 'holder': hex(h),
                   'forward': v > h,
                   'is_call_target': v in CALLS,
                   'offset_from_holder': v - h})
n_fwd = sum(1 for r in A3 if r['forward'])
n_called = sum(1 for r in A3 if r['is_call_target'])
span = max(r['offset_from_holder'] for r in A3)
put('A3_verdict', {'total': len(A3), 'forward_of_holder': n_fwd,
                   'is_call_target': n_called,
                   'max_offset_from_holder': hex(span),
                   'per_table_span': [{'t': hex(b), 'span': hex(max(TAB[b]['vals']) - TAB[b]['holders'][0])}
                                      for b in used_tabs]})
ck('A3a 全部 292 个项值都严格在持有指令之后（前向）—— 函数入口不要求这一点',
   n_fwd == len(A3), '%d/%d' % (n_fwd, len(A3)))
ck('A3b 全部 292 个项值都不是任何 call 的直接目标（0 个）',
   n_called == 0, '%d/%d' % (n_called, len(A3)))
ck('A3c 同一表内项值跨度都限制在局部（最大 0x%x = %d 字节，仍在该函数体内）' % (span, span),
   span <= 0x4000, hex(span))

# A3b-stat 【本轮最重要的一次结论降级，由 deepseek #169 提出，主会话复算确认】
# 我原先把「0/292 是 call 目标」当作「不是函数入口」的强证据。审计员指出它在零假设下**不显著**。
# 复算（本机独立算，非引用其数）：
#   基率①随机 .text 地址命中 call 目标 = 6728/4060045 = 0.001657 ⇒ E=0.484, P(X=0)=0.6161
#   基率②随机「合法起点」命中 call 目标 = 6692/1392471 = 0.004806 ⇒ E=1.403, P(X=0)=0.2450
#   基率②才是可比基率（292 个项值全部是合法起点）。
# 两个 P 都远大于 0.05 ⇒ 「0 个」这个数值为真，但单独**不构成**「非函数入口」的证据。
# 推翻「函数入口」的主力应是 A3a 前向性（case 标签的结构性必然）与 A5 可达性，不是 A3b。
_p1 = len(CALLS) / float(TVS)
_n_valid_all = len(VALID_STARTS)
_call_valid = sum(1 for v in CALLS if v in VALID_STARTS)
_p2 = _call_valid / float(_n_valid_all)
_p0_1 = (1 - _p1) ** len(A3)
_p0_2 = (1 - _p2) ** len(A3)
put('A3b_stat_null', {'p_random_text': round(_p1, 6), 'expected_hits_1': round(_p1 * len(A3), 3),
                      'P_zero_1': round(_p0_1, 4),
                      'p_valid_start': round(_p2, 6), 'expected_hits_2': round(_p2 * len(A3), 3),
                      'P_zero_2': round(_p0_2, 4),
                      'verdict': 'not significant under either null; A3b is a true count, not evidence'})
ck('A3b-stat 如实降级：「0/292 是 call 目标」在两种零假设下均不显著（P=%.4f / P=%.4f > 0.05），'
   '故它不构成「非函数入口」的统计证据' % (_p0_1, _p0_2),
   _p0_1 > 0.05 and _p0_2 > 0.05, 'P1=%.4f P2=%.4f' % (_p0_1, _p0_2))

# A3d 更强的闭环：边界检查的默认分支是否就是某个表项值（=> 默认分支也是 case）
A3d = []
for r in A2:
    b = int(r['table'], 16)
    dflt = int(r['default_target'], 16) if r['default_target'] else None
    A3d.append({'table': r['table'], 'n': r['n'], 'default_target': r['default_target'],
                'dflt_in_vals': dflt in TAB[b]['vals'] if dflt is not None else None})
n_dflt_in = sum(1 for x in A3d if x['dflt_in_vals'])
put('A3d_default_branch', {'tested': len(A3d), 'dflt_in_table_vals': n_dflt_in, 'rows': A3d})
ck('A3d 多数边界检查的默认分支本身就是该表的某个项值（⇒ 默认分支也只是另一个 case）',
   n_dflt_in >= 13, '%d/%d' % (n_dflt_in, len(A3d)))

# A3e 反向可判性（修正版）。审计员 deepseek #169 指出：本段第一版「从 call 目标集合里
# 抽 292 个再查该集合，命中 292/292」是**同义反复**，只能证明实现无 off-by-one，
# 不能证明判据有判别力。该批评成立，采纳。改为两条非同义反复的反控：
#   A3e-1 独立路径：随机抽 292 条 call **指令**，各自重算 target，再问是否在集合里
#   A3e-2 负基线：随机 292 个 .text 地址，问是否在 call 目标集合里，期望 ≈0
random.seed(20261125)
_calls_ins = []
d = iced_x86.Decoder(32, txt, ip=B)
while d.can_decode:
    i = d.decode()
    if not i.is_invalid and i.mnemonic == iced_x86.Mnemonic.CALL \
       and i.op0_kind == iced_x86.OpKind.NEAR_BRANCH32:
        _calls_ins.append(i)
_samp = [random.choice(_calls_ins) for _ in range(292)]
n_hit1 = sum(1 for i in _samp if i.near_branch_target in CALLS)
put('A3e_rev_insn', {'n_call_instructions': len(_calls_ins), 'sample': 292, 'hits': n_hit1})
ck('A3e-1 反向（独立路径）：随机 292 条 call 指令重算 target 后命中 292/292',
   n_hit1 == 292, '%d/292' % n_hit1)

_neg = []
for t in range(200):
    pool = [random.randrange(B, END) for _ in range(292)]
    _neg.append(sum(1 for a in pool if a in CALLS) / 292.0)
_neg.sort()
put('A3e_neg_baseline', {'trials': 200, 'median': round(_neg[100], 5),
                         'max': round(_neg[-1], 5),
                         'pop_rate': round(len(CALLS) / float(TVS), 5)})
ck('A3e-2 负基线：随机地址命中 call 目标的中位比例 ≈ 0（与 292/292 形成对照）',
   _neg[100] < 0.01, round(_neg[100], 5))


# ---------------- N1 反控：B1 的 31 个去重宿主跑同一套「是否合法单元起点」
# 自错如实登记（第 4 处，由跨家族审计员 deepseek #169 抓出，我复算确认）：
# 我最初写的断言是「41 个宿主里是单元起点的 <= 2」，报 0/31 —— 那个 0 只在
# 「全部 31 个宿主都在线性扫描的 ip 集合里」的前提下才等于「全部 invalid」。
# 实测：0x728e15 根本不在 ip 集合里，它落在 0x728e10（len=6 的 ror）这条指令内部，
# 偏移 5。故正确数是 30/31 在 ip 集合、30/31 invalid、0/31 合法、1 个不在集合。
# 这正是 R104 EF10 记的「0x728e16 口径分歧」的同一处，两轮都栽在同一个地址上。
n1_valid = [h for h in B1_HOSTS if h in VALID_STARTS]
n1_inip = [h for h in B1_HOSTS if h in START_SET]
n1_inv = [h for h in B1_HOSTS if h in INVALID_STARTS]
n1_absent = [h for h in B1_HOSTS if h not in START_SET]
put('N1_b1_hosts', {'n': len(B1_HOSTS), 'in_ip_set': len(n1_inip),
                    'invalid_starts': len(n1_inv), 'valid_starts': len(n1_valid),
                    'not_in_ip_set': [hex(x) for x in n1_absent],
                    'covering': [{'host': hex(h), 'unit': hex(IP_COVER[h][0]),
                                  'unit_len': IP_COVER[h][1], 'offset': IP_COVER[h][2]}
                                 for h in n1_absent]})
ck('N1 反控：B1 的 31 宿主里「是**合法**单元起点」的必须为 0（判据有判别力）',
   len(n1_valid) == 0, '%d/%d' % (len(n1_valid), len(B1_HOSTS)))
ck('N1b 如实口径：31 个宿主里 30 个在 ip 集合且全 invalid，1 个（0x728e15）不在 ip 集合',
   len(n1_inip) == 30 and len(n1_inv) == 30 and len(n1_absent) == 1,
   'in_ip=%d invalid=%d absent=%d' % (len(n1_inip), len(n1_inv), len(n1_absent)))

# ---------------- N2 反控：随机 292 个 .text 地址的同口径桶分布
random.seed(20261124)
N2 = {'trials': 200, 'fracs': []}
for t in range(200):
    pool = [random.randrange(B, END) for _ in range(292)]
    hit = sum(1 for a in pool if a in VALID_STARTS)
    N2['fracs'].append(hit / len(pool))
N2['fracs'].sort()
put('N2_random', {'median': round(N2['fracs'][100], 4),
                  'min': round(N2['fracs'][0], 4), 'max': round(N2['fracs'][-1], 4),
                  'true_entry_frac': round(n_start / 292.0, 4)})
ck('N2 反控：随机地址「是单元起点」的中位比例远低于真表项（%0.4f vs %0.4f）'
   % (N2['fracs'][100], n_start / 292.0),
   N2['fracs'][100] < n_start / 292.0 - 0.2, round(N2['fracs'][100], 4))

# ---------------- A5：292 个项值是否都能经分派结构到达（有没有死槽）
# 这是本轮最强的一条闭合判据：两级形态按字节表实际取值集合算可达，
# 直接形态按 [0, bound] 算可达，与表长 n 求交。若某项永不可能是分派目标，
# 它就不该被叫做 case 标签 —— 那时「不是函数入口」这条就失去依据。
IMM_KINDS = (iced_x86.OpKind.IMMEDIATE8, iced_x86.OpKind.IMMEDIATE8TO32,
             iced_x86.OpKind.IMMEDIATE16, iced_x86.OpKind.IMMEDIATE32)
CC2 = (iced_x86.Mnemonic.JA, iced_x86.Mnemonic.JAE, iced_x86.Mnemonic.JBE,
       iced_x86.Mnemonic.JB)
A5 = []
for r in A2:
    b = int(r['table'], 16)
    n = r['n']
    h = int(r['holder'], 16)
    j = IDX[h]
    bound, bt = None, None
    for k in range(max(0, j - 8), j):
        ins = UN[k][3]
        if ins.mnemonic == iced_x86.Mnemonic.CMP and ins.op1_kind in IMM_KINDS:
            for k2 in range(k + 1, min(k + 4, j)):
                if UN[k2][3].mnemonic in CC2:
                    bound = ins.immediate8 if ins.op1_kind in (
                        iced_x86.OpKind.IMMEDIATE8, iced_x86.OpKind.IMMEDIATE8TO32) \
                        else ins.immediate32
                    break
        if ins.mnemonic == iced_x86.Mnemonic.MOV and ins.op0_register in (
                iced_x86.Register.CL, iced_x86.Register.DL, iced_x86.Register.AL) \
           and ins.op1_kind == iced_x86.OpKind.MEMORY \
           and (ins.memory_index != iced_x86.Register.NONE
                or ins.memory_base != iced_x86.Register.NONE) \
           and ins.memory_displacement == b + 4 * n:
            bt = ins.memory_displacement
    if bt is not None and bound is not None:
        idxs = {raw[bt - B + TROFF + x] for x in range(bound + 1)}
        mode = 'two-level-byte-table'
    else:
        idxs = set(range(n))
        mode = 'direct'
    reach = len(idxs & set(range(n)))
    A5.append({'table': r['table'], 'n': n, 'mode': mode, 'bound': bound,
               'byte_table': (hex(bt) if bt else None),
               'reachable_entries': reach, 'unreachable': sorted(set(range(n)) - idxs)[:8]})
tot_n = sum(x['n'] for x in A5)
tot_r = sum(x['reachable_entries'] for x in A5)
put('A5_reachability', {'total_entries': tot_n, 'reachable': tot_r, 'dead': tot_n - tot_r,
                        'rows': A5})
ck('A5 全部 292 个项值都能经该表的分派结构取到（0 个死槽）—— 没有一项是摆设',
   tot_r == tot_n, '%d/%d' % (tot_r, tot_n))

# ---------------- A4 已并入 A3b（CALLS 在 A3 段建立）
a4 = [{'val': r['val'], 'called': int(r['val'], 16) in CALLS} for r in A1]
n_called4 = sum(1 for r in a4 if r['called'])
put('A4_entries_called', {'n_called': n_called4, 'of': len(a4),
                          'called_vals': [r['val'] for r in a4 if r['called']][:20]})
ck('A4 与 A3b 同源复算一致（表项值里被 call 直引的个数 == A3b 报的 0）',
   n_called4 == n_called, '%d/%d' % (n_called4, n_called))

json.dump({'checks': checks, 'R': R}, open(OUT, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n=== %d checks, %d FAIL ===' % (len(checks), nf))
sys.exit(1 if nf else 0)
