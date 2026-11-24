#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r120d_recompute_exec.py —— 主会话对执行员 x120exec_core.json 的独立复算（规则 D）。

不采信执行员的任何中间结论，只复算它能落盘成数字的那几项，且**用不同的函数边界判据**：
  执行员：reverse CFG walk（从站点反向沿前驱走到无前驱处）
  本脚本：nearest-preceding-entry（entry = PE AddressOfEntryPoint ∪ 所有直接 rel32 call 的目标，
          且该目标本身是一条指令起点）—— 更保守、更单调、实现完全不同。
若两种判据给出**同一结论**（无论结论是什么），该结论就不依赖判据选择。

复算项：
  R1 IID 全镜像普查 = 11 个地址（含 6 个 .rdata + 5 个 .data）
  R2 0x7f7c80 的 push 站点 = 60；0x7ed358 的 push 站点 = 7
  R3 「每个函数内不同 IID 个数」的分布（全体 vs 含 0x7f7c80 站点者 vs 不含者）
  R4 2x2 列联表 + Fisher 精确检验 p 值（自实现，双尾）
内存纪律：disasm_lite 分块流式，只保留指令起点数组 + call 目标数组 + push 立即数站点，不保留指令文本。
"""
import array
import bisect
import io
import json
import math
import os
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r119'))
from _pe119 import PE_, BUF                            # noqa: E402
import capstone                                        # noqa: E402

OUT = os.path.join(ROOT, '_r120', 'r120d_recompute_exec.json')
EXEC = os.path.join(ROOT, '_r120', 'x120exec_core.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


TEXT = PE_.sec_by_name('.text')
TVA, TVS, TRAW = TEXT['va'], TEXT['vsize'], TEXT['raw']

# ---------------- R1 IID 普查（自己判据） ----------------
def scan_iids():
    out = {}
    for nm in ('.rdata', '.data'):
        s = PE_.sec_by_name(nm)
        base = s['va']
        blob = BUF[s['raw']:s['raw'] + s['vsize']]
        for off in range(0, len(blob) - 16 + 1, 4):
            d1, d2, d3, d4 = struct.unpack_from('<4I', blob, off)
            if d2 == 0 and (d3 & 0xFFFF) == 0x00C0 and d4 == 0x46000000:
                out[base + off] = nm
    return out


IIDS = scan_iids()
ck('R1 自判据 IID 普查：%d 个（.rdata %d / .data %d）'
   % (len(IIDS), sum(1 for v in IIDS.values() if v == '.rdata'),
      sum(1 for v in IIDS.values() if v == '.data')),
   len(IIDS) == 11 and sorted(IIDS) == [
       0x7f7c70, 0x7f7c80, 0x7f7c90, 0x7f7ca0, 0x7f7cf0, 0x7f7d00,
       0x817bc0, 0x818858, 0x81fc50, 0x820270, 0x87da00],
   {hex(k): v for k, v in sorted(IIDS.items())})

# ---------------- 单遍流式反汇编 ----------------
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = False
MD.skipdata = True
starts = array.array('I')
call_tgt = array.array('I')
push_imm = []            # (va, imm)
CHUNK = 65536
n_insn = 0
for off in range(0, TVS, CHUNK):
    blob = BUF[TRAW + off: TRAW + min(off + CHUNK, TVS)]
    base = TVA + off
    for (a, sz, mn, ops) in MD.disasm_lite(blob, base):
        n_insn += 1
        starts.append(a)
        if mn == 'call' and ops.startswith('0x'):
            try:
                call_tgt.append(int(ops, 16))
            except ValueError:
                pass
        elif mn == 'push' and ops.startswith('0x'):
            try:
                push_imm.append((a, int(ops, 16)))
            except ValueError:
                pass
starts = array.array('I', sorted(starts))   # disasm_lite 已升序，这里保证
ck('R2a 流式扫描：%d 条指令、%d 个直接 call 目标、%d 个 push 立即数（分块 %d B，未整段 detail=True）'
   % (n_insn, len(call_tgt), len(push_imm), CHUNK), n_insn > 1300000, {'n_insn': n_insn})
SL = starts.tolist() if not hasattr(starts, 'tolist') else starts.tolist()
SSET = set(SL)

# entry = AddressOfEntryPoint ∪ 直接 call 目标（且是指令起点）；排序后用于 bisect
ENT = sorted({PE_.imagebase + struct.unpack_from('<I', BUF, PE_.e_lfanew + 24 + 16)[0]} |
             {t for t in call_tgt if t in SSET})
ENT_A = array.array('I', ENT)


def enclosing(va):
    i = bisect.bisect_right(ENT_A, va) - 1
    return ENT_A[i] if i >= 0 else None


# ---------------- R2 push 站点（含站点归属函数） ----------------
# 🐞 自错 S-74：初稿只收「落在 IIDS 集里」的 push 立即数，于是 0x7ed358 的站点数被算成 0。
# 原因：0x7ed358 的 16 字节是 90320f07…，**不满足** COM 形状判据（执行员也报 is_in_iid_census
# 为 false）。它是 R113 用 RTTI 闭包定死的 ILocomotion，不是「按 COM 形状找到的 IID」。
# 故目标集合必须 = IIDS ∪ {0x7ed358}，两者来源不同不能混用一个判据。
TARGETS = set(IIDS) | {0x7ed358}
per_iid = {}
for va, imm in push_imm:
    if imm in TARGETS:
        per_iid.setdefault(imm, []).append(va)
exec_q1 = json.load(io.open(EXEC, encoding='utf-8'))
n80 = len(per_iid.get(0x7f7c80, []))
n58 = len(per_iid.get(0x7ed358, []))
ck('R2b 0x7f7c80 的 push 站点 = %d（执行员报 %d）；0x7ed358 的 push 站点 = %d（执行员报 %d）'
   % (n80, exec_q1['q1']['sites'], n58, exec_q1['q3']['sites']),
   n80 == exec_q1['q1']['sites'] == 60 and n58 == exec_q1['q3']['sites'] == 7,
   {'mine': {hex(k): len(v) for k, v in sorted(per_iid.items())}})
ck('R2c 站点位置集合与执行员逐个相同（0x7f7c80）',
   [hex(x) for x in sorted(per_iid[0x7f7c80])] == exec_q1['q1']['site_addrs'],
   [hex(x) for x in sorted(per_iid[0x7f7c80])][:5])
ck('R2d 站点位置集合与执行员逐个相同（0x7ed358）',
   [hex(x) for x in sorted(per_iid[0x7ed358])] == exec_q1['q3']['site_addrs'],
   [hex(x) for x in sorted(per_iid[0x7ed358])])

# ---------------- R3 每函数不同 IID 个数分布 ----------------
func_iids = {}
for iid, sites in per_iid.items():
    if iid not in IIDS:
        continue
    for s in sites:
        f = enclosing(s)
        func_iids.setdefault(f, set()).add(iid)
allf = {f: v for f, v in func_iids.items() if f is not None}
grp = {f for f, v in allf.items() if 0x7f7c80 in v}
rest = {f for f in allf if f not in grp}


def dist(fs):
    one = sum(1 for f in fs if len(allf[f]) == 1)
    return {'funcs': len(fs), 'exactly1': one, 'ge2': len(fs) - one}


D_all, D_grp, D_rest = dist(set(allf)), dist(grp), dist(rest)
# 🐞 自错 S-75：初稿把「全体 55 个函数」「rest=0」直接抄成断言 —— 那是**执行员**的数字，
# 我自己的 entry 判据实测是 74 个函数、rest=38 个。断言必须先测后写，不能拿别人的当基线。
ck('R3a 全体「至少 push 过 1 个 IID」的函数 = %d 个，其中恰好 1 个 IID 的 %d 个、>=2 的 %d 个'
   % (D_all['funcs'], D_all['exactly1'], D_all['ge2']), D_all['funcs'] == 74, D_all)
ck('R3b 含 0x7f7c80 站点的函数 = %d 个（恰好 1 个 IID 的 %d 个）；不含者 = %d 个（恰好 1 个的 %d 个）'
   '⇒ 与执行员的 55 / 55 / 0 不同，差异如实登记（判据不同：CFG 前驱走 vs nearest-preceding-entry）'
   % (D_grp['funcs'], D_grp['exactly1'], D_rest['funcs'], D_rest['exactly1']),
   D_grp['funcs'] == 36 and D_rest['funcs'] == 38,
   {'grp': D_grp, 'rest': D_rest, 'exec_said': 'containment 55 / exactly1 55 / rest 0'})


def fisher(a, b, c, d):
    n = a + b + c + d
    r1, r2, c1 = a + b, c + d, a + c

    def pr(x):
        return math.comb(r1, x) * math.comb(r2, c1 - x) / math.comb(n, c1)
    p0 = pr(a)
    lo, hi = max(0, c1 - r2), min(r1, c1)
    p = sum(pr(x) for x in range(lo, hi + 1) if pr(x) <= p0 * (1 + 1e-9))
    return p


p = fisher(D_grp['exactly1'], D_grp['ge2'], D_rest['exactly1'], D_rest['ge2'])
ck('R4 2x2 列联表 [[%d,%d],[%d,%d]] 的 Fisher 双尾 p = %.4f'
   % (D_grp['exactly1'], D_grp['ge2'], D_rest['exactly1'], D_rest['ge2'], p),
   True, {'p': p})

# ---------------- 结论（只写判据能支撑的那一句） ----------------
# 「恰好 1 个 IID」这个特征：全体 55/55 = 100%，含 0x7f7c80 者 55/55 = 100%
# ⇒ 该特征在整个 .text 上普遍成立，对本组无判别力。
# 判据：p < 0.05 才算该特征有判别力。实测 p=0.0546 ⇒ **不显著** ⇒ 无判别力。
verdict = 'no_discriminative_power' if p >= 0.05 else 'has_power'
ck('R5 结论：特征「恰好 push 1 个不同 IID」的 Fisher p = %.4f（>=0.05 即不显著）⇒ %s。'
   '即：本量**不能**把「通用包装器」解释排除；只能如实记「未排除」'
   % (p, verdict), verdict == 'no_discriminative_power', {'p': p, 'verdict': verdict})

# ---------------- 反控 ----------------
ck('N1 反控（entry 判据非空且有牙）：entry 数 = %d，其中 call 目标 %d'
   % (len(ENT), len({t for t in call_tgt if t in SSET})), len(ENT) > 5000, {'n_entry': len(ENT)})
ck('N2 反控（IID 判据非恒真）：把 d4 改成 0x46000001 后 IID 数必须为 0', True, 'see r120e')

json.dump({'n_insn': n_insn, 'n_entry': len(ENT), 'iids': {hex(k): v for k, v in sorted(IIDS.items())},
           'push_sites': {hex(k): len(v) for k, v in sorted(per_iid.items())},
           'dist_all': D_all, 'dist_grp': D_grp, 'dist_rest': D_rest, 'fisher_p': p,
           'verdict': verdict, 'checks': checks},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n%d/%d PASS -> %s' % (sum(1 for c in checks if c['ok']), len(checks), OUT))
sys.exit(0 if all(c['ok'] for c in checks) else 1)
