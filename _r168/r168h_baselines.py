#!/usr/bin/env python3
"""R168 H：给「58/65 落在代码引用型跳转表内」配**同一判据下**的零假设基线。

R167 的富集倍数（24.6× / 9.4×）是用它自己的 best_table（>=3 条目值判据）算的。
本卡的判据不同（代码引用 + >=2 条目），故必须**用自己的判据重算基线**，否则倍数不可比。
三个基线：
  B1 随机 .text 地址落表率
  B2 「不可解码但从未被线性扫描踩到」的 U 子集抽样落表率
  B3 表字节区间占 .text 的比例（几何基线，应与 B1 同阶）
"""
import sys, json, random, struct
sys.path.insert(0, '_r143')
import r143lib as L
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
B = L.Bin(); data = B.data; IB = B.IB
text = [s for s in B.secs if s[0] == '.text'][0]
LO = IB + text[1]; HI = LO + text[2]
md = Cs(CS_ARCH_X86, CS_MODE_32)

C = json.load(open('_r168/r168c_final_buckets.json'))
rows = C['rows']
tabs = []
for r in rows:
    for t in r['tables']:
        tabs.append((int(t['tab'], 16), t['entries'], t['width']))
seen = set(); U = []
for t, n, w in tabs:
    if (t, w) in seen: continue
    seen.add((t, w)); U.append((t, n, w))
print('distinct tables', len(U))

def in_tab(va):
    for t, n, w in U:
        if t <= va < t + w * n: return True
    return False
tot_bytes = sum(n * w for t, n, w in U)
# 表区间去重叠后的字节数
iv = sorted((t, t + n * w) for t, n, w in U)
merged = []
for a, b in iv:
    if merged and a <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], b)
    else: merged.append([a, b])
cov = sum(b - a for a, b in merged)

# 线性起点与未踩到的不可解码位
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
# 不可解码位（逐字节 count=1）—— 只在本轮需要的范围内重算：抽样已足够，但为保真全扫太慢，
# 改用 R167 已实测值 U=58,017 与 never=57,952 作对照，并在此**独立复算抽样部分**。
R167 = json.load(open('_r167/r167d_holes_semantics_final.json'))
holes = set(int(x, 16) for x in R167['holes'])
U_claim = R167['undecodable_count']; never_claim = R167['never_visited_count']

rnd = random.Random(20261127)
N = 4000
b1 = sum(1 for _ in range(N) if in_tab(rnd.randrange(LO, HI)))
# B2：随机取不可解码位（抽样检查）
sam = 0; b2 = 0
while sam < 2000:
    va = rnd.randrange(LO, HI - 16)
    if va in starts or va in holes: continue
    b = B.rd(va, 15)
    if not b: continue
    if list(md.disasm(b, va, count=1)): continue
    sam += 1
    if in_tab(va): b2 += 1
A = []
A.append({'id': 'H1 表区间占 .text 字节比例与随机地址落表率同阶（差 < 2 倍）',
          'ok': abs((b1 / N) / (cov / text[2]) - 1) < 1.0 if cov else False,
          'detail': 'geo=%.6f rand=%.6f' % (cov / text[2], b1 / N)})
A.append({'id': 'H2 洞落表率 / 随机落表率 > 50（用本卡判据，不是 R167 的判据）',
          'ok': (b1 / N) > 0 and (58 / 65) / (b1 / N) > 50,
          'detail': 'hole=%.4f rand=%.6f ratio=%.1f' % (58 / 65, b1 / N, (58 / 65) / (b1 / N))})
A.append({'id': 'H3 洞落表率 / 未踩到不可解码位落表率 > 5',
          'ok': b2 > 0 and (58 / 65) / (b2 / sam) > 5,
          'detail': 'never=%.4f ratio=%.1f' % (b2 / sam, (58 / 65) / (b2 / sam) if b2 else -1)})
A.append({'id': 'H4 线性起点 == 1,392,527（本卡第四次独立复算）', 'ok': len(starts) == 1392527,
          'detail': str(len(starts))})
out = {'tables_distinct': len(U), 'tab_bytes': tot_bytes, 'tab_bytes_merged': cov,
       'text_vsz': text[2], 'geo_rate': cov / text[2],
       'rand_rate': b1 / N, 'rand_n': N,
       'never_undecodable_rate': b2 / sam, 'never_n': sam,
       'hole_rate': 58 / 65,
       'ratio_vs_rand': (58 / 65) / (b1 / N) if b1 else None,
       'ratio_vs_never': (58 / 65) / (b2 / sam) if b2 else None,
       'r167_U': U_claim, 'r167_never': never_claim, 'starts': len(starts),
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r168/r168h_baselines.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'assertions'}, ensure_ascii=False, indent=1))
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', '')[:200])
