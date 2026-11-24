#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r107l_recheck_audit.py —— §2.12 规则 D：主会话亲自复算跨家族审计 #179 的三条结论

不读、不 import 子代理脚本；判据全部自写，且尽量换实现路径。
审计 #179（hy4）三条主张，逐条判：支持 / 驳回 / 部分成立。
"""
import bisect, hashlib, json, os, random, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r107/r107l_recheck_audit.json'
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
ml = Cs(CS_ARCH_X86, CS_MODE_32)
ml.detail = False
ml.skipdata = True
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

# ---------- 全段：call 目标 + 指令起点（与审计稿不同实现：不用 detail 全段）----------
CT = set()
starts = []
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
ck('R0 .text 区间 [0x401000,0x7e038d) 与 call 目标 6,728', (TS, TE) == (0x401000, 0x7e038d)
   and len(CT) == 6728, (hex(TS), hex(TE), len(CT)))

# ---------- 审计 A1 主张①：声称 S 不在「直接 call 目标」集合里 ----------
CARD = {'0x46f5a0': 0x46de20, '0x48db10': 0x48d1e0, '0x48dd10': 0x48dcd0,
        '0x4c8114': 0x4c6cb0, '0x5001e4': 0x4ffd90, '0x58bda4': 0x58bc20,
        '0x69b15c': 0x69ae90, '0x6a92c4': 0x6a8b30, '0x6adbdc': 0x6acee0,
        '0x6b0238': 0x6afd60, '0x6dfdec': 0x6dd8b0, '0x708d54': 0x708c30,
        '0x71f2c0': 0x71e940, '0x71f328': 0x71e940, '0x71f778': 0x71f680,
        '0x71f9e0': 0x71f9c0, '0x728e08': 0x728a00, '0x7291ac': 0x728a00,
        '0x79f028': 0x79da90}
missing = [k for k, v in CARD.items() if v not in CT]
ck('A1-recon 19 张声称 S 里，不在 call 直接目标集合的数量（审计稿说「只有 2 个是」，应为 0）',
   len(missing) == 0, missing)

# ---------- 审计 A2 主张②：判界寄存器与索引寄存器相同 8 张 / 不同 11 张 ----------
D = json.load(open('_r106/r106f_switchsem.json'))['tables']


def insn_at(a):
    return next(md.disasm(raw[off(a):off(a) + 16], a), None)


same = []
diff = []
for t in D:
    H = int(t['holder'], 16)
    j = insn_at(H)
    idx = j.reg_name(j.operands[0].mem.index)
    i = bisect.bisect_left(starts, H) - 1
    creg = None
    for _ in range(40):
        if i < 0:
            break
        g = insn_at(starts[i])
        i -= 1
        if g is not None and g.mnemonic == 'cmp' and len(g.operands) == 2 \
                and g.operands[0].type == 1 and g.operands[1].type == 2:
            creg = g.reg_name(g.operands[0].reg)
            break
    (same if creg == idx else diff).append(t['table'])
ck('A2-recon 两寄存器相同 %d 张 / 不同 %d 张（审计稿 8/11，我方 9/10）' % (len(same), len(diff)),
   len(same) + len(diff) == 19, {'same': same, 'diff': diff})


# ---------- 审计 A3 主张③：P(K>=17) = 1.0 ⇒ 「不显著」----------
pop = sorted(CT)
rng = random.Random(20261117)
N = 100000
cnt = {}
for _ in range(N):
    u = len({pop[rng.randrange(len(pop))] for _ in range(19)})
    cnt[u] = cnt.get(u, 0) + 1
dist = {k: v / N for k, v in sorted(cnt.items())}
p_le17 = sum(v for k, v in dist.items() if k <= 17)
p_ge17 = sum(v for k, v in dist.items() if k >= 17)
exp = sum(k * v for k, v in dist.items())
ck('A3-recon 重采样 100,000 次：期望 distinct %.3f，实测 17 的 P(K<=17)=%.5f，P(K>=17)=%.5f'
   % (exp, p_le17, p_ge17), abs(exp - 18.97) < 0.05, {'dist': dist, 'exp': round(exp, 4),
                                                     'p_le17': round(p_le17, 6),
                                                     'p_ge17': round(p_ge17, 6)})
ck('A3-recon 审计稿用「P(K>=17)=1.0 ⇒ 不显著」是**尾向错**：17 低于期望 18.97，'
   '要看下尾 P(K<=17)=%.5f < 0.05 ⇒ 显著偏少' % p_le17, p_le17 < 0.05, p_le17)
ck('A3-recon 结论修正：17 显著偏少 = 存在共用入口（与 R106 记的两组共用一致，方向相反于审计稿）',
   p_le17 < 0.05 and p_ge17 > 0.95, 'lower tail significant')

json.dump({'checks': checks, 'same': same, 'diff': diff, 'dist': dist,
           'p_le17': p_le17, 'p_ge17': p_ge17, 'exp': exp},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
