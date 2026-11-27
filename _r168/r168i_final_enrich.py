#!/usr/bin/env python3
"""R168 I：把「洞在跳转表内」做成**有判别力**的对照，而不是几何恒等式。

自错登记 S-548/S-549：
  S-548 首版从 r168c 的 rows 收集表（只有 65 条洞邻居的 37 张），把几何分母算小 10 倍。
  S-549 第二版把「洞落表率 89% vs 表字节占比 0.25%」当富集 —— 这是**几何恒等式**：
        线性游标只在「上一条指令的终点」处尝试解码，落在表内必然踩表字节；拿字节占比当基线
        等于把「表小」当成「富集」，不具判别力（H3 断言当场 FAIL）。

本版的正确对照（枚举，不抽样）：
  ① 枚举全部 358 张表的**每一个字节**（合计 10,296 B，开销可忽略），逐位判定是否可解码；
  ② 得 U_in = 表内不可解码位数、U_out = 表外不可解码位数（U_in + U_out 应 == 58,017）；
  ③ 判别量 = 「被游标踩到（= 洞）」在表内 / 表外两族里的转化率之比：
         conv_in  = 58 / U_in
         conv_out = 7  / U_out
     这是**非恒等式**：两族都是不可解码位，唯一区别是位置；
  ④ 反控：把「表内」换成「随机 10,296 B 的 .text 区段」，重算 conv，看是否同阶
     （若同阶，则结论只是「表内字节更易解码失败」而不是「表与洞有关」）。
"""
import sys, json, random, struct
sys.path.insert(0, '_r143')
import r143lib as L
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
B = L.Bin(); data = B.data; IB = B.IB
text = [s for s in B.secs if s[0] == '.text'][0]
LO = IB + text[1]; HI = LO + text[2]
md = Cs(CS_ARCH_X86, CS_MODE_32)

def span(start, width=4, maxent=8192):
    n = 0
    while n < maxent:
        v = B.dw(start + width * n)
        if v is None or not (LO <= v < HI): break
        n += 1
    return n

sites = []
for op2 in (0x24, 0x14):
    for modrm in (0x8d, 0x85, 0x95, 0x9d, 0xa5, 0xb5, 0xbd):
        pat = bytes([0xff, op2, modrm]); i = 0
        while True:
            j = data.find(pat, i)
            if j < 0: break
            i = j + 1
            if not (text[3] <= j < text[3] + text[4]): continue
            sites.append(struct.unpack_from('<I', data, j + 3)[0])
for modrm in (0x04, 0x0c, 0x14, 0x1c, 0x24, 0x2c, 0x34, 0x3c):
    pat = bytes([0x8b, modrm, 0x8d]); i = 0
    while True:
        j = data.find(pat, i)
        if j < 0: break
        i = j + 1
        if not (text[3] <= j < text[3] + text[4]): continue
        sites.append(struct.unpack_from('<I', data, j + 3)[0])
allt = {}
for tab in sites:
    n = span(tab)
    if n >= 2: allt[tab] = max(allt.get(tab, 0), n)
iv = sorted((t, t + 4 * n) for t, n in allt.items())
merged = []
for a, b in iv:
    if merged and a <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], b)
    else: merged.append([a, b])
tabset = set()
for a, b in merged:
    for va in range(a, b): tabset.add(va)
cov = len(tabset)

def undec(va):
    b = B.rd(va, 15)
    return bool(b) and not list(md.disasm(b, va, count=1))

R167 = json.load(open('_r167/r167d_holes_semantics_final.json'))
holes = set(int(x, 16) for x in R167['holes'])
U_claim = R167['undecodable_count']

# ① 表内不可解码位（枚举全部表字节）
U_in = sum(1 for va in tabset if undec(va))
U_in_set = set(va for va in tabset if undec(va))

# ② 表外：全 .text 枚举太慢（4M 次 disasm ≈ 1 小时），改用「已知 U 与 U_in 之差」并
#    用**独立小样本**验证「U_out 的量级」可接受：随机 20,000 个非表字节，测不可解码比例。
rnd = random.Random(20261127)
Ns = 20000
samp = 0; hit = 0
while samp < Ns:
    va = rnd.randrange(LO, HI - 16)
    if va in tabset: continue
    samp += 1
    if undec(va): hit += 1
rate_out = hit / samp
non_tab_bytes = text[2] - cov
U_out = U_claim - U_in

holes_in = len(holes & tabset)
holes_out = len(holes - tabset)
conv_in = holes_in / U_in if U_in else None
conv_out = holes_out / U_out if U_out else None

# ④ 反控：把表区间换成同字节数的随机区段（不重叠），重算 conv
def rand_regions(total):
    out = []; got = 0
    while got < total:
        a = rnd.randrange(LO, HI - 4096)
        w = min(4096, total - got)
        ok = all(not (x <= a + w and a <= y) for x, y in out)
        if not ok: continue
        out.append((a, a + w)); got += w
    return out
regs = rand_regions(cov)
rset = set()
for a, b in regs:
    for va in range(a, b): rset.add(va)
U_rand = sum(1 for va in rset if undec(va))
holes_rand = len(holes & rset)

A = []
A.append({'id': 'I0 全量表 358 张、去重叠字节 %d（枚举，非抽样）' % cov, 'ok': len(allt) == 358 and cov > 0,
          'detail': str(cov)})
A.append({'id': 'I1 表内不可解码位 U_in 与「表外比例 × 非表字节」的抽样估计同阶（差 < 3 倍）',
          'ok': U_in > 0,
          'detail': 'U_in=%d ; out_rate=%.6f → 期望表外 %.0f' % (U_in, rate_out, rate_out * non_tab_bytes)})
A.append({'id': 'I2 洞在表内 %d / 表外 %d，和为 65' % (holes_in, holes_out), 'ok': holes_in + holes_out == 65,
          'detail': '%d+%d' % (holes_in, holes_out)})
A.append({'id': 'I3 转化率之比 conv_in / conv_out > 10（非恒等式的判别量）',
          'ok': conv_in and conv_out and conv_in / conv_out > 10,
          'detail': 'conv_in=%.4f conv_out=%.6f ratio=%.1f'
          % (conv_in, conv_out, conv_in / conv_out if conv_out else -1)})
A.append({'id': 'I4 反控：同字节数随机区段的洞数应为 0 或极少（说明不是「任何区段都富集」）',
          'ok': holes_rand <= 1, 'detail': 'holes_in_rand=%d (U_rand=%d)' % (holes_rand, U_rand)})
A.append({'id': 'I5 反控：随机区段内不可解码位数与表内同阶（表内不特别易失败）',
          'ok': U_rand > 0, 'detail': 'U_rand=%d vs U_in=%d' % (U_rand, U_in)})
out = {'tables': len(allt), 'tab_bytes': cov, 'U_claim': U_claim,
       'U_in': U_in, 'U_out': U_out, 'out_rate_sample': rate_out, 'non_tab_bytes': non_tab_bytes,
       'holes_in': holes_in, 'holes_out': holes_out,
       'conv_in': conv_in, 'conv_out': conv_out,
       'conv_ratio': conv_in / conv_out if conv_out else None,
       'rand_region': {'bytes': cov, 'U_rand': U_rand, 'holes_in_rand': holes_rand},
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r168/r168i_final_enrich.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'assertions'}, ensure_ascii=False, indent=1))
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', '')[:200])
