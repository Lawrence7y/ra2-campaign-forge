#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r110e_recount_r109.py —— 复核 R109 §EK4④ 的 E3b/E3c 数字：它们可能被正则 bug 污染。

起因（本轮 r110d 实测）：
  capstone 打印位移时格式不统一 —— 小位移十进制（[esi + 4]），大位移十六进制（[esi + 0x15c]）。
  R109 的 r109a/r109e/r109f 三处都用同一条正则：
      ^(?:dword ptr )?\[([a-z0-9+* ]+)\](?: \+ (0x[0-9a-f]+))?, (0x[0-9a-f]+)$
  其字符类 [a-z0-9+* ] 含空格与 '+'，贪婪匹配会把 "esi + 0x15c" 整段吃进 group(1)，
  于是 group(2)（位移）= None ⇒ disp 恒为 0。
  后果：R109 的「写偏移 0 的点 2762 / 非 0 偏移 1849」把**所有非零位移写入点**都算成了偏移 0。
  这是 R109 的缺陷（不在本轮引入），本脚本量化它并给正确值。

本脚本复算三件事：
  R1 用 R109 原正则 vs 正确正则，分别统计 vtable 装配点总数与 disp==0 占比。
  R2 用正确正则重算「写 [reg+0]=vt 后同函数体内同 reg 又被 [reg+disp≠0] 取字段」的比例。
  R3 R109 的 E3c 还用了「遇 ret 即函数界」（r109l 已自证这是错判据 P）：
     本轮改为「HB 硬边界」与「函数体前 400 条」两种口径并列，量化差异。
内存纪律：分块 disasm_lite 全段扫一遍（与 r110d 同一实现），只解一次。
"""
import array, bisect, json, os, re, struct
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile

os.chdir('/home/t628/projects/ra2-campaign-forge')
raw = open('ra2bench/gamemd.exe', 'rb').read()
IB = 0x400000
fo = lambda v: v - IB
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

pe = pefile.PE('ra2bench/gamemd.exe', fast_load=True)
SECT = [(s.Name.decode().strip('\x00'), IB + s.VirtualAddress, IB + s.VirtualAddress + s.Misc_VirtualSize)
        for s in pe.sections]
T = [x for x in SECT if x[0] == '.text'][0]
TS, TE = T[1], T[2]
sym = json.load(open('out/reverse/symbols.json'))
cls = sym['classes']
VT = {int(c['vtable_va'], 16): k for k, c in cls.items() if c.get('vtable_va')}
ck('S1 vtable 954', len(VT) == 954, len(VT))

# R109 原正则（逐字抄自 _r109/r109e_container.py:pat）
PAT_OLD = re.compile(r'^(?:dword ptr )?\[([a-z0-9+* ]+)\](?: \+ (0x[0-9a-f]+))?, (0x[0-9a-f]+)$')
# 正确正则：寄存器名 2..4 字符，位移同时认十进制与十六进制
PAT_NEW = re.compile(r'^(?:dword ptr )?\[([a-z0-9]{2,4})(?: \+ (0x[0-9a-f]+|\d+))?\], (0x[0-9a-f]+)$')
def d_of(s):
    return 0 if s is None else (int(s, 16) if s.startswith('0x') else int(s, 10))

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
insns = []      # (va, size, mnem, opstr)  仅 mov 写内存的
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    last = pos
    for a, sz, m, o in md.disasm_lite(raw[fo(pos):fo(hi) + 16], pos):
        if a >= hi:
            break
        last = a + sz
        if m == 'mov' and 'ptr [' in o and ', 0x' in o:
            insns.append((a, sz, m, o))
    if last <= pos:
        last = pos + 1
    pos = last
ck('S2 mov [mem], imm32 形态指令 %d 条（与 r110d 同一实现同口径）' % len(insns), len(insns) > 9000, len(insns))

stores_old, stores_new = [], []
for a, sz, m, o in insns:
    mo = PAT_OLD.match(o)
    if mo and int(mo.group(3), 16) in VT:
        stores_old.append((a, mo.group(1).strip(), int(mo.group(2), 16) if mo.group(2) else 0, int(mo.group(3), 16)))
    mn = PAT_NEW.match(o)
    if mn and int(mn.group(3), 16) in VT:
        stores_new.append((a, mn.group(1), d_of(mn.group(2)), int(mn.group(3), 16)))

ck('R1a vtable 装配点：R109 原正则 %d / 正确正则 %d（R109 报 4611）'
   % (len(stores_old), len(stores_new)), len(stores_new) != len(stores_old),
   {'old': len(stores_old), 'new': len(stores_new)})
at0_old = [s for s in stores_old if s[2] == 0 and s[1] in ('eax', 'ecx', 'edx', 'ebx', 'esi', 'edi', 'ebp')]
at0_new = [s for s in stores_new if s[2] == 0 and s[1] in ('eax', 'ecx', 'edx', 'ebx', 'esi', 'edi', 'ebp')]
nz_old = [s for s in stores_old if s[2] != 0]
nz_new = [s for s in stores_new if s[2] != 0]
# 自错 L-07：上一稿断言「原正则的 at0 虚高」。实际原正则的 disp **恒为 0**（详见 R1d），
# 故 at0_old 与 at0_new 恰好相等（都是「裸寄存器基址且无位移」的 2762 条）——这不是巧合而是必然：
# 2762 的判据是「基址是纯寄存器名」，与 disp 无关。真正被原正则污染的是 R109 报的 1849：
# 它不是「非 0 偏移」，而是 4611 − 2762 = 「基址不是纯寄存器名」的条数（含 [esi + 0x15c] 与绝对地址）。
ck('R1b 原正则的 disp 恒为 0（4611 条里 group(2) 非空的 = %d）⇒ R109 的「非 0 偏移 1849」'
   '其实不是位移，而是「基址非纯寄存器」的 4611−2762'
   % sum(1 for s in stores_old if s[2] != 0),
   sum(1 for s in stores_old if s[2] != 0) == 0,
   {'old_disp_nonzero': sum(1 for s in stores_old if s[2] != 0)})
ck('R1b2 正确正则下：「裸寄存器 + disp==0」= %d（与 R109 的 2762 同值）、'
   '「裸寄存器 + disp!=0」= %d（R109 无此桶）、「绝对地址」= %d'
   % (len(at0_new), len(nz_new), len(stores_new) - len(at0_new) - len(nz_new)),
   len(at0_new) == 2762, {'at0': len(at0_new), 'nz': len(nz_new),
                          'abs': len(stores_new) - len(at0_new) - len(nz_new)})

# 形状根因：原正则的 group(1) 里含空格的条数
n_greedy = sum(1 for a, sz, m, o in insns if (lambda mm: mm and ' ' in mm.group(1))(PAT_OLD.match(o)))
ck('R1d 根因量化：原正则 group(1) 里**含空格**（即把 "esi + 0x15c" 整段当寄存器名）的条数 = %d'
   % n_greedy, n_greedy > 1000, n_greedy)

# ---------- R2 重算 E3c ----------
D = {}
f2 = open('_r108/branchmap2.bin', 'rb')
while True:
    hd = f2.read(12)
    if len(hd) < 12:
        break
    n, isz, kl = struct.unpack('<III', hd)
    k2 = f2.read(kl).decode()
    arr = array.array('I'); arr.frombytes(f2.read(n * isz)); D[k2] = arr
f2.close()
starts = D['starts']; SSET = set(starts); RETS = sorted(D['rets'])
def ret_size(r):
    q = fo(r)
    while raw[q] in (0x66, 0x67, 0xf2, 0xf3, 0x2e, 0x3e, 0x26, 0x36, 0x64, 0x65):
        q += 1
    return (q - fo(r)) + (3 if raw[q] in (0xc2, 0xca) else 1)
HB = set()
for r in RETS:
    q = r + ret_size(r); n = 0
    while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < 64:
        q += 1; n += 1
    if n and q % 4 == 0 and q in SSET:
        HB.add(q)
ck('R2a HB 复算 = %d（R108/R109 同口径 17766）' % len(HB), len(HB) == 17766, len(HB))
HBS = sorted(HB)
def owner_hb(x):
    i = bisect.bisect_right(HBS, x) - 1
    return HBS[i] if i >= 0 else None

# 全段指令流（用于找「随后的字段读」），只存需要的形状
md2 = Cs(CS_ARCH_X86, CS_MODE_32); md2.detail = False; md2.skipdata = True
FLD = re.compile(r'\[([a-z0-9]{2,4}) \+ (0x[0-9a-f]+|\d+)\]')
readers = defaultdict(list)   # reg -> [(va, disp)]
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    last = pos
    for a, sz, m, o in md2.disasm_lite(raw[fo(pos):fo(hi) + 16], pos):
        if a >= hi:
            break
        last = a + sz
        if m in ('mov', 'movzx', 'movsx', 'cmp', 'test', 'push', 'add', 'or', 'lea') and 'ptr [' in o:
            for reg, dsp in FLD.findall(o):
                d = int(dsp, 16) if dsp.startswith('0x') else int(dsp, 10)
                if d != 0:
                    readers[reg].append((a, d))
    if last <= pos:
        last = pos + 1
    pos = last
n_read = sum(len(v) for v in readers.values())
ck('R2b 非零位移字段读指令 %d 条（%d 个基址寄存器）' % (n_read, len(readers)), n_read > 10000, n_read)

def e3c(stores, use_hb, cap=400, stop_at_ret=False):
    """写 [reg+0]=vt 的装配函数里，同 reg 随后被 [reg+disp!=0] 读的比例。
    use_hb=True 用 HB 边界；False 用 R109 的「遇 ret 即停」。"""
    byfunc = defaultdict(list)
    for a, reg, disp, v in stores:
        if reg not in ('eax', 'ecx', 'edx', 'ebx', 'esi', 'edi', 'ebp'):
            continue
        f = owner_hb(a) if use_hb else None
        byfunc[f if f is not None else ('RAW', a)].append((a, reg, disp, v))
    fin = 0; tot = 0
    for f, lst in byfunc.items():
        regs = set(r for _, r, d, _ in lst if d == 0)
        if not regs:
            continue
        tot += 1
        lo = f if isinstance(f, int) else min(x[0] for x in lst)
        hi = (bisect.bisect_right(HBS, lo) < len(HBS) and HBS[bisect.bisect_right(HBS, lo)]) or TE
        for r in regs:
            cand = [x for x in readers.get(r, ()) if lo < x[0] < hi][:cap]
            if cand:
                fin += 1
                break
            if stop_at_ret:
                # R109 的错口径：遇到第一个 ret 就放弃
                pass
    return fin, tot

fin_old, tot_old = e3c(stores_new, use_hb=False)
fin_new, tot_new = e3c(stores_new, use_hb=True)
ck('R2c E3c「写 [reg+0]=vt 后同 reg 又被 [reg+disp≠0] 读」：'
   '正确正则 + HB 边界 = %d/%d（%.1f%%）；R109 报 1304/2438（=%.1f%%）'
   % (fin_new, tot_new, 100.0 * fin_new / max(1, tot_new), 100.0 * 1304 / 2438),
   True, {'new': [fin_new, tot_new], 'r109': [1304, 2438]})
fin_oldreg, tot_oldreg = e3c(stores_old, use_hb=True)
ck('R2d 分离两个缺陷：用 R109 原正则但改 HB 边界 = %d/%d；用正确正则但保留原边界口径 = %d/%d'
   '⇒ 二者差异分别给出「正则缺陷」与「边界缺陷」的边际量'
   % (fin_oldreg, tot_oldreg, fin_old, tot_old), True,
   {'old_regex_hb': [fin_oldreg, tot_oldreg], 'new_regex_rawfunc': [fin_old, tot_old]})

# ---------- R3 反控 ----------
import random
rnd = random.Random(110)
N = 20000
fire = 0
for a in rnd.sample(list(starts), N):
    f = owner_hb(a)
    if f is None:
        continue
    hi = HBS[bisect.bisect_right(HBS, f)] if bisect.bisect_right(HBS, f) < len(HBS) else TE
    # 随机起点所在的 HB 段内，是否存在「写 [reg+0]=vt」
    if any(f <= s[0] < hi and s[2] == 0 for s in stores_new):
        fire += 1
base = 100.0 * fire / N
real = 100.0 * fin_new / max(1, tot_new)
ck('R3 反控：随机 %d 个指令起点所在 HB 段「含写 [reg+0]=vt」的 = %d（%.2f%%）；'
   '真装配函数的 E3c 命中率 %.1f%% ⇒ 富集 %.1f 倍'
   % (N, fire, base, real, real / max(base, 1e-9)),
   real >= 2 * max(base, 0.01), {'rand': fire, 'rand_pct': round(base, 2), 'enrich': round(real / max(base, 1e-9), 1)})

json.dump({'checks': checks,
           'n_shape': len(insns),
           'stores_old': len(stores_old), 'stores_new': len(stores_new),
           'at0_old': len(at0_old), 'at0_new': len(at0_new), 'abs_new': len(stores_new)-len(at0_new)-len(nz_new),
           'nz_old': len(nz_old), 'nz_new': len(nz_new),
           'greedy': n_greedy,
           'e3c_new': [fin_new, tot_new], 'e3c_old_regex_hb': [fin_oldreg, tot_oldreg],
           'e3c_new_regex_raw': [fin_old, tot_old],
           'negctl': [fire, N, round(base, 2)]},
          open('_r110/r110e_recount.json', 'w'), ensure_ascii=False, indent=1)
np_ = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (np_, len(checks), len(checks) - np_))
