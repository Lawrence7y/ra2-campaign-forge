#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r108h_drift.py —— 线性扫描漂移：27 个 call 直接目标不在指令起点集合里

r108g 的自错 E-z1：C1 断言「call 目标落 .text 内 6719 个全部是指令起点」实测 6692/6719，
**27 个不是**。这不是「call 目标错」，而是**我的整段线性扫描漂移了**：
.skipdata 线性扫在遇到内联数据（跳转表）后失去同步，把真函数入口含在一条假指令里。
后果：SSET 作「合法指令起点」判据时会对这 27 个地址撒谎；HB 需要 q∈SSET，涉及它们的
边界会被漏掉。

本脚本量化影响面：
  Q1 27 个漂移锚点的共同特征（前一条假指令跨度是否跨过锚点）
  Q2 把锚点并入 SSET 后，HB 增加多少个
  Q3 19 张表的 owner / HB 是否改变（若不变，说明本轮结论不受影响）
  Q4 全量 387 站点里，owner 落在「漂移锚点并入后才成立的 HB」上的个数
"""
import array, bisect, hashlib, json, os, re, struct, sys
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
D = {}
f = open('_r108/branchmap2.bin', 'rb')
while True:
    hd = f.read(12)
    if len(hd) < 12:
        break
    n, isz, kl = struct.unpack('<III', hd)
    k = f.read(kl).decode()
    a = array.array('I'); a.frombytes(f.read(n * isz)); D[k] = a
starts = D['starts']; SSET = set(starts); RETS = sorted(D['rets'])
CALLT = set(x for x in D['call_t'] if TS <= x < TE)
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
def d1(a, n=1):
    return [(g[0], g[1], g[2], g[3]) for g in md.disasm_lite(raw[fo(a):fo(a) + 16], a)][:n]

drift = sorted(x for x in CALLT if x not in SSET)
ck('Q1 漂移锚点（call 目标但不在指令起点集合）%d 个' % len(drift), len(drift) == 27,
   [hex(x) for x in drift])
feat = []
for t in drift:
    back = None
    for b in range(1, 16):
        if (t - b) in SSET:
            back = t - b
            break
    span = None
    if back is not None:
        g = d1(back, 1)[0]
        span = (g[0], g[1], g[2], g[3], g[0] + g[1])
    feat.append({'anchor': hex(t), 'prev_start': hex(back) if back else None,
                 'prev_insn': span})
straddle = sum(1 for x in feat if x['prev_insn'] and x['prev_insn'][4] > int(x['anchor'], 16))
ck('Q1b 锚点被上一条（假）指令**跨过**的个数 = %d/%d（证明是扫描漂移而非目标错）'
   % (straddle, len(feat)), straddle == len(feat),
   [x for x in feat if not (x['prev_insn'] and x['prev_insn'][4] > int(x['anchor'], 16))][:4])

SSET2 = SSET | set(drift)
def ret_size(r):
    q = fo(r)
    while raw[q] in (0x66, 0x67, 0xf2, 0xf3, 0x2e, 0x3e, 0x26, 0x36, 0x64, 0x65):
        q += 1
    return (q - fo(r)) + (3 if raw[q] in (0xc2, 0xca) else 1)
def hb_of(ss):
    out = set()
    for r in RETS:
        p = r + ret_size(r); q = p; n = 0
        while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < 64:
            q += 1; n += 1
        if n and q % 4 == 0 and q in ss:
            out.add(q)
    return out
HB1 = hb_of(SSET); HB2 = hb_of(SSET2)
ck('Q2 HB 由 %d 增至 %d（新增 %d 个，即漂移掩掉的函数边界）'
   % (len(HB1), len(HB2), len(HB2) - len(HB1)), len(HB2) >= len(HB1),
   [hex(x) for x in sorted(HB2 - HB1)][:10])

# Q3 19 张表：owner 是否改变
T19 = [(0x46f5a0, 0x46de20, 0x46e4be), (0x48db10, 0x48d1e0, 0x48d583),
       (0x48dd10, 0x48dcd0, 0x48dce0), (0x4c8114, 0x4c6cb0, 0x4c6cd7),
       (0x5001e4, 0x4ffd90, 0x4ffde9), (0x58bda4, 0x58bc20, 0x58bd85),
       (0x69b15c, 0x69ae90, 0x69af3e), (0x6a92c4, 0x6a8b30, 0x6a8e1e),
       (0x6adbdc, 0x6acee0, 0x6acf2a), (0x6b0238, 0x6afd60, 0x6afd73),
       (0x6dfdec, 0x6dd8b0, 0x6dd8e7), (0x708d54, 0x708c30, 0x708c4e),
       (0x71f2c0, 0x71e940, 0x71eea2), (0x71f328, 0x71e940, 0x71f092),
       (0x71f778, 0x71f680, 0x71f6d0), (0x71f9e0, 0x71f9c0, 0x71f9d3),
       (0x728e08, 0x728c00, 0x728c17), (0x7291ac, 0x728e30, 0x728e6c),
       (0x79f028, 0x79da90, 0x79ed73)]
def owner_of(S, H, hb):
    hs = sorted(hb)
    i = bisect.bisect_right(hs, H)
    return hs[i - 1] if i and hs[i - 1] > S else S
chg = []
for tab, S, H in T19:
    o1 = owner_of(S, H, HB1); o2 = owner_of(S, H, HB2)
    if o1 != o2:
        chg.append((hex(tab), hex(o1), hex(o2)))
ck('Q3 19 张表的 owner 在漂移修正前后是否改变（改变数应为 0）', not chg, chg)
ck('Q3b 19 张表里 owner 落在「新增 HB」上的张数',
   True, [(hex(t), hex(owner_of(S, H, HB2))) for t, S, H in T19
          if owner_of(S, H, HB2) in (HB2 - HB1)])

# Q4 全量站点影响
SITES = []
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]
    last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        if m == 'jmp' and '[' in o and '*4' in o:
            m2 = re.findall(r'0x[0-9a-f]+', o)
            if m2:
                SITES.append((a, int(m2[-1], 16)))
    if last <= pos:
        last = pos + 1
    pos = last
nchg = 0
ex = []
for site, tab in SITES:
    cts = sorted(CALLT)
    i = bisect.bisect_right(cts, site)
    S = cts[i - 1] if i and site - cts[i - 1] <= 0x8000 else TS
    if S not in SSET:
        S = owner_of(TS, S, HB2)
    o1 = owner_of(S, site, HB1); o2 = owner_of(S, site, HB2)
    if o1 != o2:
        nchg += 1
        if len(ex) < 6:
            ex.append((hex(site), hex(o1), hex(o2)))
ck('Q4 全量 387 站点里 owner 因漂移修正而改变的个数 = %d（%.1f%%）'
   % (nchg, 100.0 * nchg / len(SITES)), True, ex)

json.dump({'checks': checks, 'drift': [hex(x) for x in drift], 'feat': feat,
           'HB_before': len(HB1), 'HB_after': len(HB2),
           'HB_added': [hex(x) for x in sorted(HB2 - HB1)],
           'owner_changed_19': chg, 'owner_changed_all': nchg},
          open('_r108/r108h_drift.json', 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
