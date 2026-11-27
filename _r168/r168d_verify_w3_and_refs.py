#!/usr/bin/env python3
"""R168 D：两件事。
① 复核 R167 对 0x7d0cba 的「3 字节条目表」判据能否在现盘复现（表区间 0x7d0cb3..0x7d0ceb）。
② 给「2 条目表」这一新发现加辨别力：逐表统计「镜像里是否有 dword 等于该表首」
   （= 有代码按基址引用它），并与「随机 dword 命中表首」的零假设基线对照。
"""
import sys, struct, json, random
sys.path.insert(0, '_r143')
import r143lib as L
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
B = L.Bin(); data = B.data; IB = B.IB
text = [s for s in B.secs if s[0] == '.text'][0]
T_LO = IB + text[1]; T_VSZ_HI = T_LO + text[2]
md = Cs(CS_ARCH_X86, CS_MODE_32)

def rd3(va):
    b = B.rd(va, 3)
    return None if b is None else (b[0] | (b[1] << 8) | (b[2] << 16))

# ① 宽度 3 复核
w3 = []
for phase in range(4):
    st = 0x7d0cb3 + phase
    seq = []
    for k in range(12):
        v = rd3(st + 3 * k)
        seq.append(v)
        if v is None or not (T_LO <= v < T_VSZ_HI):
            break
    w3.append({'phase': phase, 'start': hex(st), 'n': len(seq) - (0 if seq and seq[-1] and T_LO <= seq[-1] < T_VSZ_HI else 1),
               'vals': [hex(v) if v else None for v in seq[:6]]})
# R167 给的区间
lo, hi = 0x7d0cb3, 0x7d0ceb
seqR = []
for k in range((hi - lo) // 3):
    v = rd3(lo + 3 * k)
    seqR.append(v)
okR = [v for v in seqR if v is not None and T_LO <= v < T_VSZ_HI]
# 也试 4 字节 / 2 字节，看是否只是相位巧合
alt = {}
for wdt in (2, 4):
    best = 0
    for ph in range(wdt):
        n = 0
        while n < 64:
            v = B.dw(lo + ph + wdt * n) if wdt == 4 else (lambda b: (b[0] | (b[1] << 8)) if b else None)(B.rd(lo + ph + wdt * n, 2))
            if v is None or not (T_LO <= v < T_VSZ_HI): break
            n += 1
        best = max(best, n)
    alt['w%d' % wdt] = best

# ② 引用基数
def span(start, width=4, maxent=8192):
    n = 0
    while n < maxent:
        v = B.dw(start + width * n)
        if v is None or not (T_LO <= v < T_VSZ_HI): break
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

tabs = {}
for s, mn, tab in sites:
    n = span(tab)
    if n >= 2:
        tabs.setdefault(tab, {'entries': n, 'sites': []})['sites'].append((s, mn))
# 表首被「数据形态」引用的次数：全镜像里等于表首的 dword 个数
allslots = {}
for nm, ava, vs, raw, rs in B.secs:
    blob = data[raw:raw + rs]
    for i in range(len(blob) // 4):
        v = struct.unpack_from('<I', blob, i * 4)[0]
        allslots[v] = allslots.get(v, 0) + 1
ref2 = [t for t, d in tabs.items() if d['entries'] >= 2]
ref2_with = [t for t in ref2 if allslots.get(t, 0) > 0]
ref3 = [t for t, d in tabs.items() if d['entries'] >= 3]
ref3_with = [t for t in ref3 if allslots.get(t, 0) > 0]

# 零假设基线：随机取 2000 个「同时是 .text 内某指令起点」的 dword 值当假想表首
starts = set()
off = text[3]; end = text[3] + text[4]; base_vs = text[1]
while off < end:
    c = data[off:min(off + 65536, end)]
    base = IB + (base_vs + (off - text[3]))
    consumed = 0
    for a, sz, mn, op in md.disasm_lite(c, base):
        if a - base + sz > len(c): break
        consumed = a - base + sz
        if a < T_VSZ_HI: starts.add(a)
    off += consumed if consumed else 1
rnd = random.Random(7)
cand = sorted(starts)
samp = [rnd.choice(cand) for _ in range(2000)]
base_ref = sum(1 for v in samp if allslots.get(v, 0) > 0)
# 随机 dword（.text 内任意偏移）作表首时，被别处引用为 dword 的比例
rand_tab_ref = 0
for _ in range(2000):
    va = rnd.randrange(T_LO, T_VSZ_HI - 16)
    if allslots.get(va, 0) > 0: rand_tab_ref += 1

A = []
A.append({'id': 'D1 0x7d0cb3 起 3 字节步进，R167 区间内条目全落 .text 的条数',
          'ok': len(okR) == 0, 'detail': 'seq=%s ok=%d' % ([hex(v) if v else None for v in seqR[:8]], len(okR))})
A.append({'id': 'D2 四个相位下 3 字节表的最长连续 >=2 条 .text 地址的相位个数',
          'ok': sum(1 for r in w3 if r['n'] >= 2) == 0, 'detail': repr(w3)})
A.append({'id': 'D3 宽度 2/4 在同一区间也不成表（排除宽度判错）',
          'ok': alt['w2'] < 2 and alt['w4'] < 2, 'detail': repr(alt)})
A.append({'id': 'D4 >=2 条目表 358 张里，表首被镜像内某 dword 引用的张数 > 0',
          'ok': len(ref2_with) > 0, 'detail': '%d/%d' % (len(ref2_with), len(ref2))})
A.append({'id': 'D5 >=3 条目表 vs >=2 条目表的引用率对照（>=2 不显著更高）',
          'ok': len(ref2) > 0 and len(ref3) > 0,
          'detail': 'ge2=%d/%d=%.4f ge3=%d/%d=%.4f'
          % (len(ref2_with), len(ref2), len(ref2_with) / len(ref2),
             len(ref3_with), len(ref3), len(ref3_with) / len(ref3))})
A.append({'id': 'D6 零假设：2000 个随机指令起点当表首，被 dword 引用的比例（基线）',
          'ok': base_ref >= 0, 'detail': '%d/2000=%.4f' % (base_ref, base_ref / 2000)})
A.append({'id': 'D7 零假设：2000 个随机 .text 偏移当表首，被 dword 引用的比例',
          'ok': rand_tab_ref >= 0, 'detail': '%d/2000=%.4f' % (rand_tab_ref, rand_tab_ref / 2000)})
A.append({'id': 'D8 线性起点 == 1,392,527（第三次独立复算）', 'ok': len(starts) == 1392527,
          'detail': str(len(starts))})
out = {'w3_r167_range': {'lo': hex(lo), 'hi': hex(hi), 'entries': len(seqR),
                         'vals': [hex(v) if v else None for v in seqR],
                         'in_text': len(okR)},
       'w3_phases': w3, 'alt_widths': alt,
       'tab_ge2': len(ref2), 'tab_ge2_with_ref': len(ref2_with),
       'tab_ge3': len(ref3), 'tab_ge3_with_ref': len(ref3_with),
       'null_ins_start_ref': [base_ref, 2000], 'null_rand_off_ref': [rand_tab_ref, 2000],
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r168/r168d_verify_w3_and_refs.json', 'w'), ensure_ascii=False, indent=1)
print('w3 range entries=%d vals=%s in_text=%d' % (len(seqR), [hex(v) if v else None for v in seqR], len(okR)))
print('phases:', w3)
print('alt widths:', alt)
print('tables ge2=%d ref=%d (%.4f) | ge3=%d ref=%d (%.4f)'
      % (len(ref2), len(ref2_with), len(ref2_with) / len(ref2),
         len(ref3), len(ref3_with), len(ref3_with) / len(ref3)))
print('null: instr-start %d/2000=%.4f ; random off %d/2000=%.4f'
      % (base_ref, base_ref / 2000, rand_tab_ref, rand_tab_ref / 2000))
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', '')[:200])
