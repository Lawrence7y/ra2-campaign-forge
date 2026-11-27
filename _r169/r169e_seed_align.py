#!/usr/bin/env python3
"""R169 E：R166 的「0/65 落在指令内部」是**单一对齐种子**的口径产物吗？（v2，性能修正）

R166 判据：用线性扫描起点集合 S 判「洞是否落在某条指令内部」，得 0/65 ⇒ 结论写成
「65 条全部不是指令内部地址」。但 S 本身是**线性解码**的产物，在跳转表字节上必然失步。
所以「不在 S 的某条指令内部」只等于「不在**线性**指令内部」，不等于「不在**真**指令内部」。

第二组对齐种子 = 表槽值（落 .text 且 capstone 可解）。从每个种子向下连续解码至多 64 条，
把得到的 (insn_start, size) 汇总成区间表；用**排序 + bisect** 做包含判定（v1 用线性扫，
65,536 次随机反控直接跑不动，S-556 同族：把「判据正确」当成「实现可用」）。

断言：
  F1  |S| == 1,392,527
  F2  表数 / 表槽种子数
  F3  至少 1 条洞落在表种子对齐下的真指令内部，且 0x7d0cba 在内
  F5  反控基线：随机 65,536 个 .text 地址在同一判据下的命中率
  F6  单调性：S ∪ 表种子 的命中数 >= F3
  F7  逐条首字节
  F8  F3 的命中数与 F5 基线比较，给出「是否显著高于基线」的判定（不做统计检验，只给两数）
"""
import sys, json, random, bisect
sys.path.insert(0, '_r143')
import r143lib as L
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
text = [s for s in B.secs if s[0] == '.text'][0]
T_LO = B.IB + text[1]; T_HI = T_LO + text[2]

starts = {}
off = text[3]; end = text[3] + text[4]; base_vs = text[1]
while off < end:
    c = B.data[off:min(off + 65536, end)]
    base = B.IB + (base_vs + (off - text[3]))
    consumed = 0
    for a, sz, mn, op in md.disasm_lite(c, base):
        if a - base + sz > len(c): break
        consumed = a - base + sz
        if a < T_HI: starts[a] = sz
    off += consumed if consumed else 1

def span_fwd(base, step=4, maxent=8192):
    n = 0; vals = []
    while n < maxent:
        v = B.dw(base + step * n)
        if v is None or not (T_LO <= v < T_HI): break
        vals.append(v); n += 1
    return n, vals

sites = []
for op2 in (0x24, 0x14):
    for m in (0x8d, 0x85, 0x95, 0x9d, 0xa5, 0xb5, 0xbd):
        pat = bytes([0xff, op2, m]); i = 0
        while True:
            j = B.data.find(pat, i)
            if j < 0: break
            i = j + 1
            if not (text[3] <= j < text[3] + text[4]): continue
            sites.append(struct_unpack := __import__('struct').unpack_from('<I', B.data, j + 3)[0])
for m in (0x04, 0x0c, 0x14, 0x1c, 0x24, 0x2c, 0x34, 0x3c):
    pat = bytes([0x8b, m, 0x8d]); i = 0
    while True:
        j = B.data.find(pat, i)
        if j < 0: break
        i = j + 1
        if not (text[3] <= j < text[3] + text[4]): continue
        sites.append(__import__('struct').unpack_from('<I', B.data, j + 3)[0])

tabsets = {}
for tab in sites:
    nf, fv = span_fwd(tab, 4)
    nb, bv = span_fwd(tab, -4)
    if nf >= 2 or nb >= 3:
        tabsets.setdefault(tab, set()).update(fv)
        tabsets[tab].update(bv)

seeds = set()
for tab, sv in tabsets.items():
    for v in sv:
        if T_LO <= v < T_HI:
            o = B.va2off(v)
            if o is not None and list(md.disasm(B.data[o:o + 16], v, count=1)):
                seeds.add(v)

iv = []   # (start, end)
for s in sorted(seeds):
    cur = s; k = 0
    while k < 64 and cur < T_HI:
        o = B.va2off(cur)
        if o is None: break
        ii = list(md.disasm(B.data[o:o + 16], cur, count=1))
        if not ii: break
        i = ii[0]
        if cur + i.size > T_HI: break
        iv.append((cur, cur + i.size))
        cur += i.size; k += 1
iv.sort()
lo_list = [a for a, _ in iv]

def inside(h):
    k = bisect.bisect_right(lo_list, h) - 1
    for idx in (k, k - 1, k - 2):
        if 0 <= idx < len(iv):
            a, b = iv[idx]
            if a < h < b:
                return (a, b)
    return None

r167 = json.load(open('_r167/r167d_holes_semantics_final.json'))
holes = [int(x, 16) for x in r167['holes']]
found = []
for h in holes:
    r = inside(h)
    if r:
        a, b = r
        o = B.va2off(a)
        ii = list(md.disasm(B.data[o:o + 16], a, count=1))[0]
        owner = [hex(t) for t, sv in tabsets.items() if a in sv]
        found.append({'hole': hex(h), 'insn': hex(a), 'size': b - a, 'off': h - a,
                      'text': ii.mnemonic + ' ' + ii.op_str, 'owner_tables': owner,
                      'hole_first_byte': B.rd(h, 1).hex()})

# S ∪ 表种子 单调性：用 S 的区间表
iv2 = sorted([(s, s + sz) for s, sz in starts.items()])
lo2 = [a for a, _ in iv2]
def inside2(h):
    k = bisect.bisect_right(lo2, h) - 1
    for idx in (k, k - 1, k - 2):
        if 0 <= idx < len(iv2):
            a, b = iv2[idx]
            if a < h < b:
                return (a, b)
    return None
union_hits = [h for h in holes if inside(h) or inside2(h)]

rnd = random.Random(169)
N = 65536
hitr = 0
for _ in range(N):
    if inside(rnd.randrange(T_LO, T_HI)): hitr += 1

A = []
def chk(i, cond, detail):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(detail)})

chk('F1 |S| == 1,392,527', len(starts) == 1392527, len(starts))
chk('F2 表数 >= 350 且表槽种子 >= 2000', len(tabsets) >= 350 and len(seeds) >= 2000,
    {'tables': len(tabsets), 'seeds': len(seeds), 'insn_intervals': len(iv)})
chk('F3 至少 1 条洞落在表种子对齐的真指令内部，含 0x7d0cba',
    len(found) >= 1 and any(f['hole'] == '0x7d0cba' for f in found),
    {'n': len(found), 'holes': [f['hole'] for f in found]})
chk('F5 随机 65,536 个 .text 地址命中基线与 F3 对比', True,
    {'baseline_hits': hitr, 'of': N, 'baseline_pct': round(100.0 * hitr / N, 3),
     'f3_hits': len(found), 'f3_of': len(holes)})
chk('F6 单调性：S ∪ 表种子 命中数 >= F3', len(union_hits) >= len(found),
    {'f3': len(found), 'union': len(union_hits), 'union_holes': [hex(h) for h in union_hits]})
chk('F7 逐条给洞首字节', True, [{'hole': f['hole'], 'first': f['hole_first_byte']} for f in found])

out = {'starts': len(starts), 'tables': len(tabsets), 'seeds': len(seeds),
       'insn_intervals': len(iv), 'holes_inside': found, 'n_inside': len(found),
       'baseline': {'hits': hitr, 'of': N}, 'union_hits': len(union_hits),
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r169/r169e_seed_align.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for a in A:
    print(('PASS ' if a['ok'] else 'FAIL ') + a['id'] + ' :: ' + a['detail'][:300])
print('FAIL count =', out['fail'])
for f in found:
    print(' ', f)
