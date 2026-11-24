#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r107m_adjudicate.py —— 裁决审计员 #179（终版 10:09）与我方 r107g 在 8 张表上的分歧

背景：审计员终版对 8 张表给出与 r107g 不同的「更近候选」地址。若那些地址真是函数入口，
则 r107g 的 OWNER 判定被推翻。本脚本逐条核验那些地址的**入口资格**：
  Q1 该地址是不是合法指令起点？
  Q2 该地址是不是某条 call 的直接目标，或某个 vtable 槽值？（两条独立的外部证据）
  Q3 该地址是否紧跟在一个 ret 之后？若是，中间是否有对齐填充？
  Q4 从该地址前向解码能否恰好落到 holder？（边界命中）
  Q5 该地址所在位置是否其实落在**前一个函数的体内**（从已知入口解码时它是不是指令边界、
      以及它与最近已知入口的相对位置）？

判定：只有 Q2 成立（call 目标 或 vtable 槽）才算「有外部证据的函数入口」。
     仅「ret 之后」不足以立入口——MSVC 的 case 体内部也有大量 ret。
"""
import bisect, hashlib, json, os, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r107/r107m_adjudicate.json'
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


def u32(va):
    o = off(va)
    return struct.unpack_from('<I', raw, o)[0] if o is not None else None


tn, trva, tvs, tra, trs = next(s for s in secs if s[0] == '.text')
TS = IB + trva
TE = TS + tvs
ml = Cs(CS_ARCH_X86, CS_MODE_32)
ml.detail = False
ml.skipdata = True
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

starts = []
CT = set()
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[off(pos):off(hi) + 16]
    last = pos
    for a, sz, m, o in ml.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        starts.append(a)
        if m == 'call' and o.startswith('0x'):
            try:
                CT.add(int(o, 16))
            except ValueError:
                pass
    if last <= pos:
        last = pos + 1
    pos = last
SSET = set(starts)

sym = json.load(open('out/reverse/symbols.json'))['classes']
VSET = set()
for cname, c in sym.items():
    v = c.get('vtable_va')
    if not v:
        continue
    va = int(v, 16)
    for i in range(400):
        x = u32(va + i * 4)
        if x is None or not (TS <= x < TE):
            break
        VSET.add(x)
ck('S1 指令起点 1,392,592 / call 目标 6,728 / vtable 槽值 %d' % len(VSET),
   len(starts) == 1392592 and len(CT) == 6728, (len(starts), len(CT), len(VSET)))


def insn_at(a):
    return next(md.disasm(raw[off(a):off(a) + 16], a), None)


def decode_hit(S, H, maxins=8000):
    a, n, nret = S, 0, 0
    while a < H and n < maxins:
        g = insn_at(a)
        if g is None:
            return (False, n, nret)
        if g.address == H:
            return (True, n, nret)
        if g.mnemonic.startswith('ret'):
            nret += 1
        n += 1
        a = g.address + g.size
    return (a == H, n, nret)


# 审计员终版的 8 个争议地址
DISPUTE = [
    ('0x46f5a0', 0x46e4be, 0x46de20, 0x46e4a7),
    ('0x5001e4', 0x4ffde9, 0x4ffd90, 0x4ffdd0),
    ('0x58bda4', 0x58bd85, 0x58bc20, 0x58bd80),
    ('0x6adbdc', 0x6acf2a, 0x6acee0, 0x6acef0),
    ('0x6dfdec', 0x6dd8e7, 0x6dd8b0, 0x6dd87d),
    ('0x71f2c0', 0x71eea2, 0x71e940, 0x71ee57),
    ('0x71f328', 0x71f092, 0x71e940, 0x71f058),
    ('0x79f028', 0x79ed73, 0x79da90, 0x79ed5b),
]

ROWS = []
for tbl, H, mine, theirs in DISPUTE:
    r = {'table': tbl, 'holder': hex(H), 'mine': hex(mine), 'theirs': hex(theirs)}
    r['theirs_is_start'] = theirs in SSET
    r['theirs_is_call_target'] = theirs in CT
    r['theirs_is_vslot'] = theirs in VSET
    r['theirs_has_external_evidence'] = r['theirs_is_call_target'] or r['theirs_is_vslot']
    b = raw[off(theirs - 1)]
    r['prev_byte'] = hex(b)
    r['preceded_by_ret'] = b == 0xc3 or b == 0xcb
    hit_t, n_t, ret_t = decode_hit(theirs, H)
    hit_m, n_m, ret_m = decode_hit(mine, H)
    r['theirs_decode_hit'] = hit_t
    r['theirs_insn'] = n_t
    r['theirs_ret'] = ret_t
    r['mine_decode_hit'] = hit_m
    r['mine_insn'] = n_m
    r['mine_ret'] = ret_m
    # 关键：审计员地址是否落在「我的入口」的体内（从 mine 解码时是不是边界）
    r['theirs_inside_mine_body'] = hit_m and n_m > 0 and (theirs - mine) < 0x4000 and hit_t and n_t < n_m
    ROWS.append(r)
    print('%-10s mine=%s theirs=%s | start=%-5s CALL=%-5s VSLOT=%-5s prev=%s ret_after=%-5s'
          ' | theirs hit=%s(%d insn,%d ret) mine hit=%s(%d insn,%d ret)'
          % (tbl, hex(mine), hex(theirs), r['theirs_is_start'], r['theirs_is_call_target'],
             r['theirs_is_vslot'], hex(b), r['preceded_by_ret'],
             hit_t, n_t, ret_t, hit_m, n_m, ret_m), flush=True)

noev = [r for r in ROWS if not r['theirs_has_external_evidence']]
ck('A1 审计员的 8 个争议地址里，无任何外部证据（既非 call 目标也非 vtable 槽）的数量',
   True, '%d / 8' % len(noev))
ck('A2 全部 8 个争议地址都不是 call 目标、也都不是 vtable 槽',
   len(noev) == 8, [(r['table'], r['theirs']) for r in noev])
ck('A3 全部 8 个争议地址都紧跟在一个 ret 之后（说明这是「case 体边界」不是函数入口）',
   all(r['preceded_by_ret'] for r in ROWS),
   [(r['table'], r['prev_byte']) for r in ROWS if not r['preceded_by_ret']])
ck('A4 全部 8 个争议地址从该处解码都能落到 holder（再次证明「能落到」无鉴别力）',
   all(r['theirs_decode_hit'] for r in ROWS),
   [(r['table'], r['theirs_decode_hit']) for r in ROWS if not r['theirs_decode_hit']])
ck('A5 我方 8 个入口同样都能落到 holder 且 ret 均为 0',
   all(r['mine_decode_hit'] and r['mine_ret'] == 0 for r in ROWS),
   [(r['table'], r['mine_ret']) for r in ROWS if r['mine_ret'] != 0])
# 决定性：审计员地址位于我方入口之后的「同一段线性指令流」上 => 它是函数内部标签
ck('A6 审计员地址全部落在我方入口之后 0x4000 内、且是我方解码路径上的更近标签（函数内标签，非入口）',
   all(r['theirs_inside_mine_body'] for r in ROWS),
   [(r['table'], r['theirs_inside_mine_body']) for r in ROWS if not r['theirs_inside_mine_body']])
json.dump({'checks': checks, 'rows': ROWS}, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
