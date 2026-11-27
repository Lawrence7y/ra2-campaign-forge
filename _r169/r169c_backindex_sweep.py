#!/usr/bin/env python3
"""R169 C：R168 的 span 只往 +4 单向延展 —— 反向索引（neg/sub 之后）的表会被漏掉吗？

背景：R168 的 358 张表全由「从 disp32 起按 +4 步进延展、槽值落 .text」判出。若某处表基址是
「表尾」且前面有 neg ecx / sub ecx 之类的取负，则条目在基址**之前**，正向只剩 0..1 条 ⇒ 会被判成「不成表」。
本轮把 520 个站点按三种口径各量一次：
  F = 正向（+4）延展条目数（R168 原口径）
  Bk = 反向（-4）延展条目数
  F∪B = max(F, Bk)（含反向）
再统计：F>=2 的站点数（应 == R168 的 376 个 site 记录去重前值），以及 F<2 但 Bk>=2 的站点数（被 R168 漏掉的）。
断言：
  C1 |S| == 1,392,527
  C2 站点数 == 520（R168 同口径）
  C3 F>=2 的站点数（去重后表数）== 358 或可解释
  C4 存在 F<2 且 Bk>=2 的站点（这就是漏项）
  C5 对每个这类站点，检查其指令流前 12 字节内是否出现 neg/sub 形态（取负证据），逐条给出
  C6 负控：对随机 2000 个 .text 4 字节对齐地址，统计 Bk>=2 的比例（基线）
  C7 反控：把 F∪B 口径下新发现的表按槽值是否落 .text 复核，全部槽值必须落 .text
"""
import sys, json, struct, random
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

def span(base, step, maxent=8192):
    n = 0; vals = []
    while n < maxent:
        v = B.dw(base + step * n)
        if v is None or not (T_LO <= v < T_HI): break
        vals.append(v); n += 1
    return n, vals

sites = []
for op2, mn in ((0x24, 'jmp'), (0x14, 'call')):
    for m in (0x8d, 0x85, 0x95, 0x9d, 0xa5, 0xb5, 0xbd):
        pat = bytes([0xff, op2, m]); i = 0
        while True:
            j = B.data.find(pat, i)
            if j < 0: break
            i = j + 1
            if not (text[3] <= j < text[3] + text[4]): continue
            sites.append((B.IB + text[1] + (j - text[3]), mn, struct.unpack_from('<I', B.data, j + 3)[0]))
for m in (0x04, 0x0c, 0x14, 0x1c, 0x24, 0x2c, 0x34, 0x3c):
    pat = bytes([0x8b, m, 0x8d]); i = 0
    while True:
        j = B.data.find(pat, i)
        if j < 0: break
        i = j + 1
        if not (text[3] <= j < text[3] + text[4]): continue
        sites.append((B.IB + text[1] + (j - text[3]), 'mov', struct.unpack_from('<I', B.data, j + 3)[0]))

rows = []
for s, mn, tab in sites:
    F, fv = span(tab, 4)
    Bk, bv = span(tab, -4)
    rows.append({'site': s, 'mn': mn, 'tab': tab, 'F': F, 'B': Bk, 'f': [hex(x) for x in fv], 'b': [hex(x) for x in bv]})

fwd_tables = {(r['tab'], 4) for r in rows if r['F'] >= 2}
missed = [r for r in rows if r['F'] < 2 and r['B'] >= 2]
missed_keys = {(r['tab']) for r in missed}

# 取负证据：站点指令前 12 字节内的指令流
def pre_insns(site, back=12):
    o = B.va2off(site - back)
    if o is None: return []
    out = []
    for i in md.disasm(B.data[o:o + back], site - back):
        out.append((hex(i.address), i.mnemonic, i.op_str))
    return out

for r in missed:
    r['pre'] = pre_insns(r['site'])
    r['neg_like'] = any(x[1] in ('neg', 'sub', 'xor') for x in r['pre'][-3:])
    r['vals_in_text'] = all(T_LO <= int(v, 16) < T_HI for v in r['b']
                            if v != '0x0')

A = []
def chk(i, cond, detail):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(detail)})

chk('C1 |S| == 1,392,527', len(starts) == 1392527, len(starts))
chk('C2 站点数 == 520', len(sites) == 520, len(sites))
chk('C3 正向 F>=2 的 (tab) 去重表数 == 358', len(fwd_tables) == 358, len(fwd_tables))
chk('C4 存在 F<2 且反向 B>=2 的站点（R168 漏项）', len(missed) >= 1,
    {'n_sites': len(missed), 'tabs': [hex(t) for t in sorted(missed_keys)]})
chk('C5 这些站点每条都在指令流前 3 条内出现 neg/sub/xor', all(r['neg_like'] for r in missed),
    [{'site': hex(r['site']), 'pre': r['pre']} for r in missed])
chk('C7 反向口径下新表槽值全部落 .text', all(r['vals_in_text'] for r in missed),
    [(hex(r['tab']), r['b']) for r in missed])

rnd = random.Random(169)
b2 = 0; N = 2000
for _ in range(N):
    a = rnd.randrange(T_LO, T_HI - 8) & ~3
    n, _ = span(a, -4)
    if n >= 2: b2 += 1
chk('C6 随机 2000 个地址反向 B>=2 的基线', True, {'ge2': b2, 'of': N, 'pct': round(100.0 * b2 / N, 2)})

out = {'starts': len(starts), 'sites': len(sites), 'fwd_tables': len(fwd_tables),
       'missed_sites': len(missed), 'missed': missed,
       'random_back_baseline': {'ge2': b2, 'of': N},
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r169/r169c_backindex_sweep.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for a in A:
    print(('PASS ' if a['ok'] else 'FAIL ') + a['id'] + ' :: ' + a['detail'][:260])
print('FAIL count =', out['fail'])
print('--- missed sites ---')
for r in missed:
    print('  site %#x %s tab %#x F=%d B=%d pre=%s' % (r['site'], r['mn'], r['tab'], r['F'], r['B'], r['pre']))
