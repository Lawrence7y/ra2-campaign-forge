#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r108b_resolve.py —— 6 张 AMBIGUOUS 表的所属函数：改用「硬函数边界 + ret 清理约定一致性」判据

R107 判据 P（在 r107g 里写成「S 到 H 之间 ret 数必须为 0」）本轮被判为**误判源**：
它把「同一函数内的提前返回」当成「跨函数界」，造成 6 张表降级为 AMBIGUOUS。
本脚本换两条**互不依赖**的机械事实：
  HB 硬边界：地址 p 满足  (a) p 是指令起点；(b) p 之前紧邻一条 ret 指令的结束，
            中间只允许 0x90/0xCC 填充；(c) p 4 字节对齐。
            => ret 之后跟填充再对齐，是 MSVC 的函数间分隔惯用法；单函数内的 ret 后面
               紧跟的是下一条指令（case 体），不会填充到对齐。
  RC ret 清理约定：同一函数内所有 ret / ret imm16 的 imm 必须相同（callee 弹出的栈字节
           是函数级约定）。区间内 imm 混合 => 区间跨了函数。
归属 = [HB 里 <= H 的最大者]（若无则退回 S），并用 RC 在 (owner, H] 上做一致性校验。

自证与正反控：
  正控 P1：954 个类 vtable 的 6499 个槽值里，多少比例本身是 HB（应当高——它们是函数入口）
  反控 N1：在 .text 随机取 20000 个指令起点，多少比例是 HB（应当极低，判据不能遍地发火）
  反控 N2：把判据施用于 R107 判为 OWNER(ret==0) 的 13 张，检查 owner 是否仍等于 R107 的 S
读取全部用 disasm_lite 生成的 branchmap2.bin，本脚本自身不解码整段。
"""
import array, bisect, hashlib, json, os, struct, sys

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
h = hashlib.sha256(raw).hexdigest()
ck('S0 exe sha256', h == EXE_SHA, h[:16])
IB = 0x400000
TS, TE = 0x401000, 0x7e038d
def fo(va):
    return va - IB          # .text 的 raw == rva（tra=0x1000, trva=0x1000）

D = {}
f = open('_r108/branchmap2.bin', 'rb')
while True:
    hd = f.read(12)
    if len(hd) < 12:
        break
    n, isz, kl = struct.unpack('<III', hd)
    k = f.read(kl).decode()
    a = array.array('I'); a.frombytes(f.read(n * isz)); D[k] = a
starts = D['starts']; sizes = D['sizes']
SSET = set(starts)
RETS = sorted(D['rets'])
CALLT = set(D['call_t'])
ck('S1 载入 branchmap2：指令 %d / ret %d / call 目标 %d' % (len(starts), len(RETS), len(CALLT)),
   len(starts) == 1392592 and len(RETS) == 31084 and len(CALLT) == 6728,
   (len(starts), len(RETS), len(CALLT)))

# ---------- ret 形态 ----------
def ret_imm(r):
    b = raw[fo(r)]
    if b == 0xc3: return 0
    if b == 0xc2: return struct.unpack_from('<H', raw, fo(r) + 1)[0]
    if b == 0xcb: return -1
    if b == 0xca: return -1 - struct.unpack_from('<H', raw, fo(r) + 1)[0]
    return None
def ret_size(r):
    b = raw[fo(r)]
    return 3 if b in (0xc2, 0xca) else 1

PAD = (0x90, 0xcc)
def boundary_after_ret(r, maxpad=64):
    """返回 (p, npad) 若 r 之后是填充到 4 对齐且 p 是指令起点"""
    p = r + ret_size(r)
    q = p
    n = 0
    while q < TE and raw[fo(q)] in PAD and n < maxpad:
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
ck('S2 硬函数边界 HB 个数 1000..20000（既非空也非遍地）', 1000 < len(HB) < 20000, len(HB))

# ---------- 正控 / 负控 ----------
sym = json.load(open('out/reverse/symbols.json'))['classes']
VSLOT = set()
VT = {}
for cn, c in sym.items():
    v = c.get('vtable_va')
    if not v:
        continue
    va = int(v, 16); slots = []
    for i in range(400):
        x = struct.unpack_from('<I', raw, fo(va) + i * 4)[0]
        if not (TS <= x < TE):
            break
        slots.append(x)
    if slots:
        VT[cn] = slots; VSLOT.update(slots)
ck('S3 vtable 自读 954 类 / %d distinct 槽值（与 R107 同口径）' % len(VSLOT),
   len(VT) == 954 and len(VSLOT) == 6499, (len(VT), len(VSLOT)))
p1 = sum(1 for s in VSLOT if s in HB)
ck('P1 正控：vtable 槽值里本身是 HB 的比例 > 60%（判据在已知函数入口上应当高）',
   p1 / len(VSLOT) > 0.60, '%.1f%% (%d/%d)' % (100.0 * p1 / len(VSLOT), p1, len(VSLOT)))

import random
random.seed(20261124)
samp = random.sample(range(len(starts)), 20000)
n1 = sum(1 for i in samp if starts[i] in HB)
ck('N1 反控：随机 20000 个指令起点里是 HB 的比例 < 3%（判据不能遍地发火）',
   n1 / 20000 < 0.03, '%.2f%% (%d/20000)' % (100.0 * n1 / 20000, n1))

# ---------- 19 张表逐张裁定 ----------
R107 = json.load(open('_r107/r107g_owner.json'))['rows']
def rets_in(a, b):
    i = bisect.bisect_right(RETS, a); j = bisect.bisect_right(RETS, b)
    return RETS[i:j]
def last_hb(S, H):
    i = bisect.bisect_right(HBS, H)
    return HBS[i - 1] if i and HBS[i - 1] > S else None
ROWS = []
for r107 in R107:
    tab = int(r107['table'], 16); S = int(r107['owner'], 16); H = int(r107['holder'], 16)
    if r107['table'] in ('0x728e08', '0x7291ac'):
        S = int(r107['R106_entry'], 16) if False else S   # R107 已改判，S 取 r107 owner
    B = last_hb(S, H)
    owner = B if B else S
    imm = sorted(set(ret_imm(r) for r in rets_in(owner, H)))
    immS = sorted(set(ret_imm(r) for r in rets_in(S, H)))
    ROWS.append({
        'table': r107['table'], 'holder': r107['holder'],
        'R107_owner': r107['owner'], 'R107_status': r107['owner_status'],
        'HB_last': hex(B) if B else None,
        'owner_new': hex(owner),
        'changed': owner != S,
        'ret_imm_in_new': imm,
        'ret_imm_in_R107': immS,
        'n_ret_new': len(rets_in(owner, H)),
        'new_in_calls': owner in CALLT, 'new_in_vslot': owner in VSLOT,
        'new_in_HB': owner in HB,
    })
    print('%-10s H=%s R107=%s(%s) HB=%s -> owner=%s changed=%s imm_new=%s nret_new=%d'
          % (r107['table'], r107['holder'], r107['owner'], r107['owner_status'],
             ROWS[-1]['HB_last'], ROWS[-1]['owner_new'], ROWS[-1]['changed'], imm, ROWS[-1]['n_ret_new']),
          flush=True)

amb = [r for r in ROWS if r['R107_status'] == 'AMBIGUOUS']
own = [r for r in ROWS if r['R107_status'] == 'OWNER']
ck('A1 6 张 AMBIGUOUS 里，新判据给出 HB 号的张数',
   True, '%d / 6' % sum(1 for r in amb if r['HB_last']))
ck('A2 新判据在 13 张 OWNER 上改判的张数（应当为 0，否则说明判据与旧判据冲突）',
   sum(1 for r in own if r['changed']) == 0, '%d %s' % (sum(1 for r in own if r['changed']),
   [r['table'] for r in own if r['changed']]))
mix = [r for r in ROWS if len(r['ret_imm_in_new']) > 1]
ck('A3 新 owner 到 holder 之间 ret 清理约定**混用**的表数（>1 说明该区间仍跨函数，须如实记不可判）',
   len(mix) == 0, '%d %s' % (len(mix), [(r['table'], r['ret_imm_in_new']) for r in mix]))
noev = [r['table'] for r in ROWS if not (r['new_in_calls'] or r['new_in_vslot'] or r['new_in_HB'])]
ck('A4 新 owner 是 call 直接目标 或 vtable 槽值 或 HB —— 三者皆无的（无外部证据）',
   True, '%d %s' % (len(noev), noev))

# ---------- 第四类入口：立即数取址（函数指针）----------
md = None
IMMPTR = set()
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]
    last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        if m in ('mov', 'push', 'cmp') and '[' not in o:
            tok = o.split(',')
            cand = tok[-1].strip()
            if cand.startswith('0x'):
                try:
                    v = int(cand, 16)
                except ValueError:
                    v = 0
                if TS <= v < TE and v in SSET:
                    IMMPTR.add(v)
    if last <= pos:
        last = pos + 1
    pos = last
ck('I1 立即数取址形态里落在 .text 且是指令起点的 distinct 地址数 > 500', len(IMMPTR) > 500, len(IMMPTR))
only_imm = [r for r in ROWS if r['owner_new'] and int(r['owner_new'], 16) in IMMPTR
            and not (r['new_in_calls'] or r['new_in_vslot'])]
ck('I2 新 owner 里「只靠立即数取址才有外部证据」的表数（R107 的 call∪vtable 判据结构性看不见这类入口）',
   True, '%d %s' % (len(only_imm), [(r['table'], r['owner_new']) for r in only_imm]))
n_slot_imm = sum(1 for s in VSLOT if s in IMMPTR)
n_slot_call = sum(1 for s in VSLOT if s in CALLT)
ck('I3 vtable 槽值中在 IMMPTR 里的个数 / 在 CALLT 里的个数（量化两类证据的互补性）',
   True, '%d / %d of %d' % (n_slot_imm, n_slot_call, len(VSLOT)))
# A5：6 张 AMBIGUOUS 的 R107 原窗口里，是否存在 call 直接目标（若有则 R107 的 S 取法本身有问题）
AMBW = {'0x46f5a0': (0x46de20, 0x46e4be), '0x5001e4': (0x4ffd90, 0x4ffde9),
        '0x58bda4': (0x58bc20, 0x58bd85), '0x71f2c0': (0x71e940, 0x71eea2),
        '0x71f328': (0x71e940, 0x71f092), '0x79f028': (0x79da90, 0x79ed73)}
incall = {}
for t, (S, H) in AMBW.items():
    incall[t] = sorted(hex(x) for x in CALLT if S < x <= H)
ck('A5 6 张 AMBIGUOUS 的原窗口 (S,H] 内的 call 直接目标（R107 的「最近 call 目标」判据本应已取到它们）',
   True, json.dumps(incall, ensure_ascii=False))

json.dump({'checks': checks, 'rows': ROWS, 'n_HB': len(HB), 'n_IMMPTR': len(IMMPTR),
           'inner_calltgt': incall,
           'P1_slot_is_HB': p1, 'N1_random_is_HB': n1},
          open('_r108/r108b_resolve.json', 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
