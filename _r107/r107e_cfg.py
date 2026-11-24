#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r107e_cfg.py —— 用 CFG 可达性判定「holder 属于哪个函数的函数体」

上一稿 r107d 的 P2（对齐填充判据）自错：把函数体内的立即数字节 / nop 序列当成了函数起点，
实测 16/19 给出明显错误的候选（例如 0x46e4a4 是 ret 0x10，属函数体内），已作废。

本稿换一个真正有鉴别力的判据：
  函数体是有向图；从候选入口 S 出发，按 jmp/jcc 边做 BFS（call 不跟入、ret 终止），
  若 holder 在可达集里，则 S 的体内含 holder。
  性质：若 S1 < S2 < H 且两者都是「被 call 直接引用」的函数入口，则 S1 与 S2 不可能同时可达 H
  —— 因为函数之间不会 fall-through 相接，S1 若可达 H 必经 S2，则 S2 就不是入口（矛盾）。
  所以「最近可达的入口」才是唯一答案。
另交一条消歧证据：S 是否为 .text 里**某条 ret 后接 0x90 填充到 4 字节边界**的天然边界。
"""
import hashlib, json, os, struct, sys
from collections import deque
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r107/r107e_cfg.json'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA, hashlib.sha256(raw).hexdigest()[:16])
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


tn, trva, tvs, tra, trs = next(s for s in secs if s[0] == '.text')
TS = IB + trva
TE = TS + tvs

mdl = Cs(CS_ARCH_X86, CS_MODE_32)
mdl.detail = False
mdl.skipdata = True
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

starts = []
calls = {}
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[off(pos):off(hi) + 16]
    last = pos
    for a, sz, m, o in mdl.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        starts.append(a)
        if m == 'call' and o.startswith('0x'):
            try:
                calls[a] = int(o, 16)
            except ValueError:
                pass
    if last <= pos:
        last = pos + 1
    pos = last
SSET = set(starts)
CALLT = set(calls.values())
ck('C0 指令数 1,392,592 / call 目标 6,728（与前几轮同口径）',
   len(starts) == 1392592 and len(CALLT) == 6728, (len(starts), len(CALLT)))

# 天然函数边界：ret 之后到 4 字节对齐全是 0x90/0xCC
BOUNDARY = set()
for a in starts:
    if not a < TE:
        continue
    got = next(md.disasm(raw[off(a):off(a) + 16], a), None)
    if got is None or not got.mnemonic.startswith('ret'):
        continue
    p = got.address + got.size
    q = (p + 3) & ~3
    if q == p:
        BOUNDARY.add(p)
        continue
    ok = True
    for k in range(p, q):
        if raw[off(k)] not in (0x90, 0xcc):
            ok = False
            break
    if ok:
        BOUNDARY.add(p)
print('  天然函数边界（ret 后接对齐填充）%d 个' % len(BOUNDARY), flush=True)
ck('C0b 天然边界数 > 1000（判据非空）', len(BOUNDARY) > 1000, len(BOUNDARY))


def cfg_reach(S, targets, cap=60000):
    """从 S 出发按 jmp/jcc 边 BFS；call 不跟入；ret 终止。返回 (可达地址集, 是否命中任一 target)"""
    seen = set()
    dq = deque([S])
    hit = set()
    while dq and len(seen) < cap:
        a = dq.popleft()
        while True:
            if a in seen:
                break
            if a not in SSET:
                break          # 撞到非指令起点 => 路径终止（数据/错位）
            seen.add(a)
            if a in targets:
                hit.add(a)
            got = next(md.disasm(raw[off(a):off(a) + 16], a), None)
            if got is None:
                break
            m = got.mnemonic
            if m.startswith('ret'):
                break
            ops = got.operands
            if m == 'jmp':
                if ops and ops[0].type == 2:   # IMM
                    t = ops[0].imm
                    if t in targets:
                        hit.add(t)
                    a = t
                    continue
                break                              # 间接 jmp 终止
            if m.startswith('j'):
                # 条件跳转：目标入队，继续 fall-through
                if ops and ops[0].type == 2:
                    t = ops[0].imm
                    if t in targets:
                        hit.add(t)
                    dq.append(t)
            a = got.address + got.size
    return seen, hit


D = json.load(open('_r106/r106f_switchsem.json'))['tables']
ROWS = []
for t in D:
    H = int(t['holder'], 16)
    P1 = int(t['func_by_calltarget'], 16)
    # 所有 call 直接目标里 <= H 且在 H 前 0x8000 内的，按降序逐个做可达性
    cands = sorted([c for c in CALLT if c <= H and H - c <= 0x8000], reverse=True)
    reach_from_P1, hit_P1 = cfg_reach(P1, {H})
    nearest_reaching = None
    for c in cands:
        seen, hit = cfg_reach(c, {H})
        if hit:
            nearest_reaching = c
            break
    # 天然边界判定：P1 与 H 之间是否夹着函数边界（那说明 P1 的体内不到 H）
    inner_bounds = sorted(b for b in BOUNDARY if P1 < b <= H)
    ROWS.append({
        'table': t['table'], 'holder': hex(H), 'P1': hex(P1),
        'P1_reaches_H': bool(hit_P1),
        'P1_cfg_size': len(reach_from_P1),
        'nearest_calltgt_reaching_H': hex(nearest_reaching) if nearest_reaching else None,
        'inner_boundaries': [hex(b) for b in inner_bounds[:6]],
        'n_inner_boundaries': len(inner_bounds),
        'P1_is_entry': P1 in CALLT,
    })
    print('%-10s H=%08x P1=%08x P1reach=%-5s cfg=%-6d nearestReach=%s innerBound=%d'
          % (t['table'], H, P1, bool(hit_P1), len(reach_from_P1),
             hex(nearest_reaching) if nearest_reaching else '-', len(inner_bounds)), flush=True)

ck('C1 19 张表全部找到「CFG 可达 holder」的 call 入口',
   all(r['nearest_calltgt_reaching_H'] for r in ROWS),
   [r['table'] for r in ROWS if not r['nearest_calltgt_reaching_H']])
n_eq = sum(1 for r in ROWS if r['nearest_calltgt_reaching_H'] == r['P1'])
ck('C2 P1 与「CFG 可达 holder 的最近入口」一致的表数', True, '%d / 19' % n_eq)
straddle = [r for r in ROWS if r['P1_reaches_H'] and r['n_inner_boundaries'] > 0]
ck('C3 若 P1 可达 H 但其间夹着天然函数边界 => P1 不是所属函数（矛盾数）',
   True, '%d 张' % len(straddle))
for r in straddle:
    print('     STRADDLE %s P1=%s 夹边界=%s' % (r['table'], r['P1'], r['inner_boundaries']), flush=True)
json.dump({'checks': checks, 'rows': ROWS, 'n_boundary': len(BOUNDARY)},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
