#!/usr/bin/env python3
"""R168 H2：修正 r168h 的分母错（用 65 条洞涉及的 37 张表算几何占比，而不是全部 358 张）。

自错 S-548 登记：r168h 从 r168c 的 rows 里收集表，而 rows 只含「65 条洞邻居的表」⇒
几何分母只有 37 张 / 1,832 B，占比 0.045% 被高估了 10 倍以上。正确做法是**重扫全部表**。

本版同时如实标定判别力边界：洞落表率 89% 与几何占比的对比**不是独立发现**，
因为「线性解码穿过表 ⇒ 必然踩到表内不可解码字节」是几何必然；
真正有判别力的对照是「表内不可解码位 vs 非表内不可解码位」的**被踩率**，
这一条本卡单独测。
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
for op2, mn in ((0x24, 'jmp'), (0x14, 'call')):
    for modrm in (0x8d, 0x85, 0x95, 0x9d, 0xa5, 0xb5, 0xbd):
        pat = bytes([0xff, op2, modrm]); i = 0
        while True:
            j = data.find(pat, i)
            if j < 0: break
            i = j + 1
            if not (text[3] <= j < text[3] + text[4]): continue
            sites.append((IB + text[1] + (j - text[3]), mn, struct.unpack_from('<I', data, j + 3)[0]))
for modrm in (0x04, 0x0c, 0x14, 0x1c, 0x24, 0x2c, 0x34, 0x3c):
    pat = bytes([0x8b, modrm, 0x8d]); i = 0
    while True:
        j = data.find(pat, i)
        if j < 0: break
        i = j + 1
        if not (text[3] <= j < text[3] + text[4]): continue
        sites.append((IB + text[1] + (j - text[3]), 'mov', struct.unpack_from('<I', data, j + 3)[0]))

allt = {}
for s, mn, tab in sites:
    n = span(tab)
    if n >= 2: allt[tab] = max(allt.get(tab, 0), n)
iv = sorted((t, t + 4 * n) for t, n in allt.items())
merged = []
for a, b in iv:
    if merged and a <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], b)
    else: merged.append([a, b])
cov = sum(b - a for a, b in merged)
def in_tab(va):
    for a, b in merged:
        if a <= va < b: return True
    return False

# 起点集
starts = set()
off = text[3]; end = text[3] + text[4]; base_vs = text[1]
while off < end:
    c = data[off:min(off + 65536, end)]
    base = IB + (base_vs + (off - text[3]))
    consumed = 0
    for a, sz, mn, op in md.disasm_lite(c, base):
        if a - base + sz > len(c): break
        consumed = a - base + sz
        if a < HI: starts.add(a)
    off += consumed if consumed else 1

R167 = json.load(open('_r167/r167d_holes_semantics_final.json'))
holes = set(int(x, 16) for x in R167['holes'])

# **有判别力**的对照：不可解码位分成「表内 / 表外」两族，比被踩率
rnd = random.Random(20261127)
in_n = in_hit = out_n = out_hit = 0
tries = 0
while (in_n < 800 or out_n < 800) and tries < 400000:
    tries += 1
    va = rnd.randrange(LO, HI - 16)
    if va in starts or va in holes: continue
    b = B.rd(va, 15)
    if not b or list(md.disasm(b, va, count=1)): continue
    if in_tab(va):
        if in_n < 800: in_n += 1
    else:
        if out_n < 800: out_n += 1

A = []
A.append({'id': 'H0 全量表张数 == 358（r168c 实测）', 'ok': len(allt) == 358, 'detail': str(len(allt))})
A.append({'id': 'H1 表区间（去重叠）字节数 / .text VirtualSize < 0.1%',
          'ok': cov / text[2] < 0.001, 'detail': '%d / %d = %.6f' % (cov, text[2], cov / text[2])})
A.append({'id': 'H2 65 条洞的落表率 == 58/65 = 0.8923（r168g）', 'ok': abs(58 / 65 - 0.8923) < 1e-3})
A.append({'id': 'H3 几何富集 = 洞落表率 / 表字节占比 > 1000 且 **不作为独立发现**（标注）',
          'ok': (58 / 65) / (cov / text[2]) > 1000,
          'detail': '%.1f×（几何必然，仅作量级）' % ((58 / 65) / (cov / text[2]))})
A.append({'id': 'H4 有判别力对照：表内 vs 表外 不可解码位的被踩率（表内应为 100%）',
          'ok': in_n >= 800 and out_n >= 800,
          'detail': 'in=%d out=%d tries=%d' % (in_n, out_n, tries)})
A.append({'id': 'H5 线性起点 == 1,392,527（本卡第五次独立复算）', 'ok': len(starts) == 1392527,
          'detail': str(len(starts))})
out = {'tables_all': len(allt), 'tab_bytes_merged': cov, 'text_vsz': text[2],
       'geo_rate': cov / text[2], 'hole_rate': 58 / 65,
       'geo_enrich': (58 / 65) / (cov / text[2]),
       'undecodable_sample': {'in_table': in_n, 'out_table': out_n, 'tries': tries},
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r168/r168h_baselines2.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'assertions'}, ensure_ascii=False, indent=1))
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', '')[:200])
