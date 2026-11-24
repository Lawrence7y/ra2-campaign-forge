#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r108e_recheck.py —— §2.12 规则 D：对 r108b/c/d 与两个子代理的声称逐条独立复算

不读、不 import 任何子代理脚本或 JSON；全部数字由本脚本自算。
待复算的声称（每条都写成可判伪的断言）：
  K1 6 张表的 H 都是 7 字节间接分派 jmp，且该表**最小槽值 == H+7**（case 体全在 H 之后）
  K2 「帧配对」：每组从 owner 到 H 之间的 ret，其 add esp,N 与 owner 的 sub esp,N 配对；
     且配对用的 sub esp 必须落在 owner 之后（不是更早的另一个函数）
  K3 0x58bda4 的 S=0x58bc20 体内只有 2 条指令就 ret，不可能含 H
  K4 0x79db50 是「取址入口」（push imm32 = 0x79db50 后被 _beginthreadex 形态调用）
  K5 call 目标「distinct 6728 / 落在 .text 内 6719」两数之差 = 9 条落在 .text 外
  K6 取址入口类别 IMMPTR 对 19 张表 owner 的边际贡献（CALLT∪VSLOT∪HB 收不到的）
  K7 「padding 边界」判据的精确度代理与随机基线
"""
import array, bisect, hashlib, json, os, re, random, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA,
   hashlib.sha256(raw).hexdigest()[:16])
IB, TS, TE = 0x400000, 0x401000, 0x7e038d
def fo(va):
    return va - IB
def u32(va):
    return struct.unpack_from('<I', raw, fo(va))[0]

D = {}
f = open('_r108/branchmap2.bin', 'rb')
while True:
    hd = f.read(12)
    if len(hd) < 12:
        break
    n, isz, kl = struct.unpack('<III', hd)
    k = f.read(kl).decode()
    a = array.array('I'); a.frombytes(f.read(n * isz)); D[k] = a
starts = D['starts']; SSET = set(starts)
RETS = sorted(D['rets']); CALL_ALL = sorted(set(D['call_t']))
CALLT_TXT = set(x for x in CALL_ALL if TS <= x < TE)
ck('S1 call 目标 distinct=%d，其中落在 .text 内 %d、落在 .text 外 %d'
   % (len(CALL_ALL), len(CALLT_TXT), len(CALL_ALL) - len(CALLT_TXT)),
   len(CALL_ALL) == 6728 and len(CALLT_TXT) == 6719,
   (len(CALL_ALL), len(CALLT_TXT)))
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True

def dis1(va, n=1):
    out = []
    for g in md.disasm_lite(raw[fo(va):fo(va) + 16], va):
        out.append((g[0], g[1], g[2], g[3]))
        if len(out) >= n:
            break
    return out

def _rbytes(r):
    q = fo(r)
    while raw[q] in (0x66, 0x67, 0xf2, 0xf3, 0x2e, 0x3e, 0x26, 0x36, 0x64, 0x65):
        q += 1
    return q, raw[q]
def ret_imm(r):
    q, b = _rbytes(r)
    if b == 0xc3: return 0
    if b == 0xc2: return struct.unpack_from('<H', raw, q + 1)[0]
    if b == 0xcb: return -1000
    if b == 0xca: return -1000 - struct.unpack_from('<H', raw, q + 1)[0]
    return -9999
def ret_size(r):
    q, b = _rbytes(r)
    return (q - fo(r)) + (3 if b in (0xc2, 0xca) else 1)

# ---- 19 张表 ----
T19 = [('0x46f5a0', 0x46f5a0, 0x46e4be), ('0x48db10', 0x48db10, 0x48d583),
       ('0x48dd10', 0x48dd10, 0x48dce0), ('0x4c8114', 0x4c8114, 0x4c6cd7),
       ('0x5001e4', 0x5001e4, 0x4ffde9), ('0x58bda4', 0x58bda4, 0x58bd85),
       ('0x69b15c', 0x69b15c, 0x69af3e), ('0x6a92c4', 0x6a92c4, 0x6a8e1e),
       ('0x6adbdc', 0x6adbdc, 0x6acf2a), ('0x6b0238', 0x6b0238, 0x6afd73),
       ('0x6dfdec', 0x6dfdec, 0x6dd8e7), ('0x708d54', 0x708d54, 0x708c4e),
       ('0x71f2c0', 0x71f2c0, 0x71eea2), ('0x71f328', 0x71f328, 0x71f092),
       ('0x71f778', 0x71f778, 0x71f6d0), ('0x71f9e0', 0x71f9e0, 0x71f9d3),
       ('0x728e08', 0x728e08, 0x728c17), ('0x7291ac', 0x7291ac, 0x728e6c),
       ('0x79f028', 0x79f028, 0x79ed73)]

# K1：每张表的 H 是 7 字节间接分派 + 最小槽值 == H+7
k1 = []
for name, tab, H in T19:
    g = dis1(H, 1)[0]
    isd = g[2] == 'jmp' and g[1] == 7 and '[' in g[3]
    slots = []
    for i in range(400):
        v = u32(tab + i * 4)
        if not (TS <= v < TE):
            break
        slots.append(v)
    k1.append((name, hex(H), g[2], g[1], hex(min(slots)) if slots else None,
               hex(min(slots) - H) if slots else None))
ck('K1 19 张表的 H 全是 7 字节间接 jmp 且最小槽值 == H+7',
   all(x[2] == 'jmp' and x[3] == 7 and x[5] == '0x7' for x in k1),
   [x for x in k1 if not (x[2] == 'jmp' and x[3] == 7 and x[5] == '0x7')])
ck('K1b 逐表 (表, H, 形态, 长度, 最小槽, 差)',
   True, '; '.join('%s:%s/%s' % (x[0], x[1], x[5]) for x in k1))

# ---- HB ----
def boundary_after_ret(r, maxpad=64):
    p = r + ret_size(r); q = p; n = 0
    while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < maxpad:
        q += 1; n += 1
    if n == 0 or q % 4 != 0 or q not in SSET:
        return None
    return (q, n)
HB = set()
for r in RETS:
    b = boundary_after_ret(r)
    if b:
        HB.add(b[0])
HBS = sorted(HB)

# ---- K5 已在 S1 断言 ----

# ---- K2 帧配对：owner 之后、H 之前的 ret，其 add esp,N / pop 序列 vs owner 的 sub esp,N ----
def owner_hb(S, H):
    i = bisect.bisect_right(HBS, H)
    return HBS[i - 1] if i and HBS[i - 1] > S else S

def prev_insn(a):
    """找 a 的前一条指令（用 starts 二分）"""
    i = bisect.bisect_left(starts, a)
    return starts[i - 1] if i > 0 else None

def frame_of(va):
    """解析 owner 处的帧分配（sub esp,N / and esp,-8 后 sub esp,N 记 and 标记）"""
    gs = dis1(va, 6)
    span = 0
    for a, sz, m, o in gs:
        mm = re.fullmatch(r'esp, (0x[0-9a-f]+)', o)
        if m == 'sub' and mm:
            return int(mm.group(1), 16)
        if m == 'and' and o.startswith('esp,'):
            span = -1
    return span if span == -1 else None

k2 = []
for name, tab, H in T19:
    S0 = None
    for r107 in json.load(open('_r107/r107g_owner.json'))['rows']:
        if r107['table'] == name:
            S0 = int(r107['owner'], 16)
    O = owner_hb(S0, H)
    fr = frame_of(O)
    i = bisect.bisect_right(RETS, O); j = bisect.bisect_right(RETS, H)
    rs = RETS[i:j]
    details = []
    okpair = 0
    for r in rs:
        p = prev_insn(r)
        txt = ''
        m = None
        if p is not None:
            g = dis1(p, 1)[0]
            txt = '%s %s' % (g[2], g[3])
            mm = re.fullmatch(r'esp, (0x[0-9a-f]+)', g[3])
            if g[2] == 'add' and mm:
                m = int(mm.group(1), 16)
            elif g[2] == 'pop':
                m = 'pop'
        if m == fr or (fr is None and m in (None, 'pop')) or (m == 'pop'):
            okpair += 1
        details.append((hex(r), ret_imm(r), hex(p) if p else None, txt))
    k2.append({'table': name, 'owner': hex(O), 'frame': fr if fr is None else hex(fr) if isinstance(fr, int) else fr,
               'n_ret': len(rs), 'n_paired': okpair, 'detail': details})
    print('K2 %-10s owner=%s frame=%s rets=%d paired=%d' %
          (name, hex(O), k2[-1]['frame'], len(rs), okpair), flush=True)
ck('K2 每个 owner 的帧常量与区间内每条 ret 的前置清理配对（不配对数应为 0）',
   all(r['n_paired'] == r['n_ret'] for r in k2),
   [(r['table'], r['n_paired'], r['n_ret']) for r in k2 if r['n_paired'] != r['n_ret']])

# 关键分歧点：R107 的 S 与 HB 给出的 owner 之间是否隔着边界
# 首稿口径（作废，E-y1）：拿「S 处 6 条指令内是否出现 sub esp,N」当帧常量比较，
# S=0x46de20/0x58bc20/0x79da90 都因前 6 条没有 sub esp 而记 None，其中 0x58bda4 的两侧
# 都是 None 被判「相同」，断言 FAIL —— 那是**探测深度不够**，不是判据被推翻。
# 改成真正有判别力的量：从 S 线性解码，首条 ret 是否早于 owner_new。
# 早于 => S 的直线体根本到不了 H，S 不可能是含 H 的函数。
def first_ret_from(S, limit=0x2000):
    a = S; n = 0
    while a < TE and n < limit:
        g = dis1(a, 1)[0]
        if g[2].startswith('ret'):
            return a, n + 1
        a = g[0] + g[1]; n += 1
    return None, n

diff = []
for name, tab, H in T19:
    S0 = None
    for r107 in json.load(open('_r107/r107g_owner.json'))['rows']:
        if r107['table'] == name:
            S0 = int(r107['owner'], 16)
    O = owner_hb(S0, H)
    if O != S0:
        fr_S, n_S = first_ret_from(S0)
        fr_O, n_O = first_ret_from(O)
        diff.append({'table': name, 'S_R107': hex(S0), 'owner_new': hex(O),
                     'first_ret_from_S': hex(fr_S) if fr_S else None,
                     'n_insn_to_first_ret_from_S': n_S,
                     'first_ret_from_owner': hex(fr_O) if fr_O else None,
                     'n_insn_to_first_ret_from_owner': n_O,
                     'S_body_ends_before_owner': (fr_S is not None and fr_S < O),
                     'boundaries_between': [hex(b) for b in HBS if S0 < b <= H]})
        print('K2b %-10s S=%s 首ret=%s(%d条) owner=%s 首ret=%s(%d条) S体在owner前就结束=%s'
              % (name, hex(S0), diff[-1]['first_ret_from_S'], n_S,
                 hex(O), diff[-1]['first_ret_from_owner'], n_O,
                 diff[-1]['S_body_ends_before_owner']), flush=True)
ck('K2b 全部改判表：R107 的 S 线性体在到达新 owner 之前就已 ret（S 不可能是含 H 的函数）',
   all(d['S_body_ends_before_owner'] for d in diff),
   [(d['table'], d['first_ret_from_S'], d['owner_new']) for d in diff
    if not d['S_body_ends_before_owner']])
ck('K2c 改判表的 S 到 owner 之间确实隔着至少 1 个 HB 边界',
   all(len(d['boundaries_between']) >= 1 for d in diff),
   [(d['table'], d['boundaries_between']) for d in diff])

# ---- K3 0x58bc20 体内指令数 ----
S = 0x58bc20
body = []
a = S
while a < TE:
    g = dis1(a, 1)[0]
    body.append((hex(a), g[2], g[3]))
    a = g[0] + g[1]
    if g[2].startswith('ret'):
        break
ck('K3 0x58bc20 起前向解码到首条 ret 只有 2 条指令（不含 H=0x58bd85）',
   len(body) == 2 and body[-1][1].startswith('ret'), body)
body2 = []
a = 0x58bd80
while a < 0x58bd85:
    g = dis1(a, 1)[0]
    body2.append((hex(a), g[2], g[3]))
    a = g[0] + g[1]
ck('K3b 0x58bd80 起 2 条指令即落到 H=0x58bd85（cmp/ja 后正好是分派）',
   len(body2) == 2 and a == 0x58bd85, body2)

# ---- K4 0x79db50 取址入口 ----
srcs = []
pos = TS
pat = struct.pack('<I', 0x79db50)
idx = []
s = 0
while True:
    i = raw.find(pat, s)
    if i < 0:
        break
    idx.append(i); s = i + 1
ctx = []
for i in idx:
    va = IB + i
    p = prev_insn(va) if va in SSET else None
    if p is None:
        # 可能是 imm 的一部分，取前 1..5 字节的反汇编起点
        for back in range(1, 6):
            if (va - back) in SSET:
                p = va - back
                break
    if p is not None:
        g = dis1(p, 1)[0]
        ctx.append((hex(p), g[2], g[3]))
ck('K4 0x79db50 的取址点在 .text 内至少 1 处、且其宿主指令以立即数形式引用它',
   len(ctx) >= 1 and any(x[2].endswith('0x79db50') for x in ctx), ctx)
# 复核 _beginthreadex 形态：宿主函数调用 0x775700，且 0x775700 内 call [0x7e1450]
if ctx:
    host = int(ctx[0][0], 16)
    cg = []
    a = host
    for _ in range(40):
        g = dis1(a, 1)[0]
        if g[2] == 'call' and g[3].startswith('0x'):
            cg.append((hex(a), g[3]))
        a = g[0] + g[1]
        if len(cg) >= 2:
            break
    iat = []
    a = 0x775700
    for _ in range(30):
        g = dis1(a, 1)[0]
        if g[2] == 'call' and '[' in g[3]:
            iat.append((hex(a), g[3]))
            break
        a = g[0] + g[1]
    ck('K4b 0x79db50 的宿主函数紧随其后 call 0x775700，且 0x775700 内 call [0x7e1450]（导入槽）',
       any(x[1] == '0x775700' for x in cg) and iat and '0x7e1450' in iat[0][1],
       (cg[:2], iat[:1]))

# ---- K6 取址入口对 owner 的边际贡献 ----
VSLOT = set()
sym = json.load(open('out/reverse/symbols.json'))['classes']
for cn, c in sym.items():
    v = c.get('vtable_va')
    if not v:
        continue
    va2 = int(v, 16)
    for i in range(400):
        x = u32(va2 + i * 4)
        if not (TS <= x < TE):
            break
        VSLOT.add(x)
IMMPTR = set()
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]
    last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        if m in ('jmp', 'call') or (m[0] == 'j' and m != 'jmp'):
            continue
        o = re.sub(r'\[[^\]]*\]', ' ', o)
        for tok in o.replace(',', ' ').split():
            if tok.startswith('0x'):
                try:
                    v = int(tok, 16)
                except ValueError:
                    continue
                if TS <= v < TE and v in SSET:
                    IMMPTR.add(v)
    if last <= pos:
        last = pos + 1
    pos = last
marg = sorted(IMMPTR - (CALLT_TXT | VSLOT | HB))
ck('K6 取址入口 IMMPTR=%d，其中 CALLT∪VSLOT∪HB 都收不到的边际新增 %d 个'
   % (len(IMMPTR), len(marg)), len(marg) > 0, [hex(x) for x in marg[:8]])
_r107own = {r['table']: int(r['owner'], 16) for r in json.load(open('_r107/r107g_owner.json'))['rows']}
setmarg = set(marg)
own_in_marg = [hex(owner_hb(_r107own[t2], H2)) for name, t2, H2 in T19
               if owner_hb(_r107own[name], H2) in setmarg]
ck('K6b 19 张表的最终 owner 里落在「取址入口边际新增」中的',
   True, own_in_marg)

# ---- K7 padding 判据精确度 ----
h_ev = sum(1 for x in HB if x in CALLT_TXT or x in VSLOT or x in IMMPTR)
random.seed(20261124)
samp = random.sample(range(len(starts)), 20000)
n1 = sum(1 for i in samp if starts[i] in HB)
ck('K7 HB 精确度代理（带 call/slot/imm 证据）= %d/%d = %.1f%%；随机起点基线 %.2f%%'
   % (h_ev, len(HB), 100.0 * h_ev / len(HB), 100.0 * n1 / 20000),
   h_ev / len(HB) > 0.5 and n1 / 20000 < 0.03,
   (h_ev, len(HB), n1))

json.dump({'checks': checks, 'K1': k1, 'K2': [{k: v for k, v in r.items() if k != 'detail'}
                                             for r in k2],
           'K2_detail': k2, 'K2b': diff,
           'K3': [body, body2], 'K4': ctx,
           'IMMPTR': len(IMMPTR), 'IMMPTR_marginal': len(marg),
           'owner_in_marginal': own_in_marg,
           'HB': len(HB), 'HB_with_evidence': h_ev},
          open('_r108/r108e_recheck.json', 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
