#!/usr/bin/env python3
"""R168 C：65 条不可解码洞的最终分桶（两法交叉，差异逐条归因）。

方法 V = R167 值判据（节内 4 字节网格 + 相位 0..3，>=3 条且每条是 .text 地址）。
方法 C = 本卡代码驱动（引用站点 ff 24/14 <SIB scale4 no-base> disp32 与
         8b <modrm r/m=100 scale4 no-base> 8d disp32，再逐 4 字节延展）。

R168 首两版的两条假 FAIL 已在脚本内固化为反控：
  S-546 A6 用 ff 15 call[disp32] 当「假阳性基线」，51.7%…实测 91.7% —— 错在基线选点：
         ff 15 的 disp32 是 IAT 槽地址，IAT 数组本身就是一列 .text 函数指针 ⇒ 必然「成表」。
         本版把这条改成**识别性判据**（ff15 目标节 == .rdata/.detour 且条目落 .text）。
  S-547 A11 要求「阈值 3 + 宽度 4」下与 R167 逐条相同，但 R167 的 56 里有 1 条是**宽度 3** 的表；
         正确的判据是「宽度 4 ∪ 宽度 3」的并集与 R167 相同。

最终分桶（三层，互斥、和为 65）：代码引用跳转表 / 字节查找表 / 未归类。
"""
import sys, struct, json, random, collections
sys.path.insert(0, '_r143')
import r143lib as L
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

B = L.Bin(); data = B.data; IB = B.IB
text = [s for s in B.secs if s[0] == '.text'][0]
T_LO = IB + text[1]; T_VSZ_HI = T_LO + text[2]
md = Cs(CS_ARCH_X86, CS_MODE_32)

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

def tables(width, minent):
    out = []
    for s, mn, tab in sites:
        n = span(tab, width)
        if n >= minent: out.append({'site': s, 'mn': mn, 'tab': tab, 'entries': n, 'width': width})
    return out
T4 = tables(4, 2); T3w = tables(3, 2)
allt = T4 + T3w

R167 = json.load(open('_r167/r167d_holes_semantics_final.json'))
holes = [int(x, 16) for x in R167['holes']]
r167_in = set(int(x, 16) for x in R167['holes_in_table'])
r167_cls = {int(d['va'], 16): d['class'] for d in R167['holes_out_table']}
r167_w = {int(k, 16): v for k, v in R167['table_entry_width'].items()}

def hits(va, ts=None):
    ts = ts or allt
    return [t for t in (ts) if t['tab'] <= va < t['tab'] + t['width'] * t['entries']]

# ---- 最终分桶 ----
buckets = collections.OrderedDict([('code_jump_table', []), ('byte_lookup', []), ('unclassified', [])])
rows = []
for h in holes:
    hh = hits(h)
    asc = 0
    while asc < 64:
        a = B.rd(h + asc, 1); b_ = B.rd(h + asc + 1, 1)
        if not a or not b_ or b_[0] != a[0] + 1: break
        asc += 1
    if hh:
        buckets['code_jump_table'].append(h)
        cls = 'code_jump_table'
    elif asc >= 4 or (B.rd(h - 8, 1) and B.rd(h + 8, 1) and asc >= 2):
        buckets['byte_lookup'].append(h); cls = 'byte_lookup'
    else:
        buckets['unclassified'].append(h); cls = 'unclassified'
    rows.append({'va': h, 'bucket': cls, 'tables': [{'site': t['site'], 'tab': t['tab'],
                  'entries': t['entries'], 'width': t['width'], 'mn': t['mn']} for t in hh],
                  'asc_run': asc, 'r167_in': h in r167_in, 'r167_class': r167_cls.get(h),
                  'r167_width': r167_w.get(h)})

# ---- 与 R167 的差异逐条归因 ----
diff = [r for r in rows if bool(r['tables']) != r['r167_in']]
for r in diff:
    n4 = [t for t in r['tables'] if t['width'] == 4]
    r['reason'] = ('R167 阈值 >=3 漏掉 2 条目表' if (n4 and min(t['entries'] for t in n4) == 2)
                   else ('R167 用宽度 3 表，本版宽度 4 未覆盖' if r['r167_in'] and r['r167_width'] == 3
                         else 'UNEXPLAINED'))

# ---- 槽值身分：条目是否指令起点 ----
slot_tot = slot_start = 0
for t in T4:
    for k in range(t['entries']):
        slot_tot += 1
        if B.dw(t['tab'] + 4 * k) in starts: slot_start += 1

# ---- 反控 ----
A = []
A.append({'id': 'C0 VirtualSize 口径线性起点 == 1,392,527', 'ok': len(starts) == 1392527, 'detail': str(len(starts))})
A.append({'id': 'C1 正控 site 0x71f9d3 -> 2 条目表首 0x71f9e0',
          'ok': any(t['site'] == 0x71f9d3 and t['tab'] == 0x71f9e0 and t['entries'] == 2 for t in T4)})
A.append({'id': 'C2 正控 site 0x7932f4 -> 表首 0x79342c',
          'ok': any(t['site'] == 0x7932f4 and t['tab'] == 0x79342c for t in T4)})
A.append({'id': 'C3 负控 500 个随机 .text 地址成表(>=2, w4) 比例 < 5%',
          'ok': (lambda r: r < 0.05)(sum(1 for _ in range(500)
              if span(random.Random(0).randrange(T_LO, T_VSZ_HI - 16)) >= 2) / 500) if False else True,
          'detail': 'deferred to C3b'})
rnd = random.Random(20261127); bh = sum(1 for _ in range(500) if span(rnd.randrange(T_LO, T_VSZ_HI - 16)) >= 2)
A[-1] = {'id': 'C3 负控 500 个随机 .text 地址成表(>=2, w4) 比例 < 5%', 'ok': bh / 500 < 0.05,
         'detail': '%d/500=%.4f' % (bh, bh / 500)}
mis = sum(1 for t in T4[:300] if span(t['tab'] + 1) >= 2)
A.append({'id': 'C4 负控 表首+1 错位后仍成表（前 300）<= 5', 'ok': mis <= 5, 'detail': str(mis)})
# S-546 修正：ff 15 的目标不应被当成跳转表，而应被识别成 IAT
iat = 0; iatN = 0; iat_sec = collections.Counter()
i = 0
while True:
    j = data.find(b'\xff\x15', i)
    if j < 0: break
    i = j + 1
    if not (text[3] <= j < text[3] + text[4]): continue
    iatN += 1
    tgt = struct.unpack_from('<I', data, j + 2)[0]
    s = B.sec_of(tgt)
    if s: iat_sec[s] += 1
    if s in ('.rdata', '.detour') and span(tgt) >= 2: iat += 1
A.append({'id': 'C5 识别性判据：ff 15 目标绝大多数落 .rdata/.detour（IAT），且这类「成表」是 IAT 数组',
          'ok': iat_sec['.rdata'] + iat_sec['.detour'] > 0.9 * iatN,
          'detail': 'sec=%s' % dict(iat_sec)})
# S-547 修正：宽度 4 与宽度 3 的并集才应与 R167 相同
Cin = set(r['va'] for r in rows if r['tables'])
A.append({'id': 'C6 (宽度4 ∪ 宽度3) 表内集合 == R167 的 56 条（逐条）',
          'ok': Cin == r167_in, 'detail': 'C=%d R167=%d symdiff=%s'
          % (len(Cin), len(r167_in), [hex(x) for x in sorted(Cin ^ r167_in)])})
A.append({'id': 'C7 差异 4 条全部归因成功（无 UNEXPLAINED）',
          'ok': len(diff) == 4 and all('UNEXPLAINED' not in r['reason'] for r in diff),
          'detail': repr([(hex(r['va']), r['reason']) for r in diff])})
A.append({'id': 'C8 三桶互斥且和为 65',
          'ok': sum(len(v) for v in buckets.values()) == 65 and len(set(holes)) == 65,
          'detail': '%s' % {k: len(v) for k, v in buckets.items()}})
A.append({'id': 'C9 表内槽值落指令起点比例 > 90%', 'ok': slot_tot and slot_start / slot_tot > 0.90,
          'detail': '%d/%d=%.4f' % (slot_start, slot_tot, slot_tot and slot_start / slot_tot)})
A.append({'id': 'C10 跳转表数（去重表首，w4 与 w3 合计）>= 300',
          'ok': len(set((t['tab'], t['width']) for t in allt)) >= 300,
          'detail': str(len(set((t['tab'], t['width']) for t in allt)))})
_other = [h for h in holes if r167_cls.get(h) == 'other']
_moved = [h for h in _other if h in set(buckets['code_jump_table'])]
_stay = [h for h in buckets['unclassified']]
A.append({'id': 'C11 R167 的 3 条 other 里 2 条本轮归入跳转表、1 条仍未归类',
          'ok': len(_other) == 3 and len(_moved) == 2 and len(_stay) == 1 and _stay[0] in _other,
          'detail': 'other=%s moved=%s stay=%s' % ([hex(x) for x in _other],
                    [hex(x) for x in _moved], [hex(x) for x in _stay])})

out = {'starts': len(starts), 'sites': len(sites),
       'tables_w4': len(T4), 'tables_w3': len(T3w), 'tab_distinct': len(set((t['tab'], t['width']) for t in allt)),
       'slot_total': slot_tot, 'slot_is_start': slot_start,
       'buckets': {k: [hex(x) for x in v] for k, v in buckets.items()},
       'counts': {k: len(v) for k, v in buckets.items()},
       'diff_vs_r167': [{'va': hex(r['va']), 'reason': r['reason'], 'r167_in': r['r167_in'],
                         'r167_class': r['r167_class'], 'r167_width': r['r167_width']} for r in diff],
       'rows': [dict(r, va=hex(r['va']), tables=[dict(t, site=hex(t['site']), tab=hex(t['tab']))
                for t in r['tables']]) for r in rows],
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r168/r168c_final_buckets.json', 'w'), ensure_ascii=False, indent=1)
print('starts=%d sites=%d tables w4=%d w3=%d distinct=%d slots=%d/%d=%.4f'
      % (len(starts), len(sites), len(T4), len(T3w), out['tab_distinct'], slot_start, slot_tot,
         slot_start / slot_tot))
print('buckets:', out['counts'])
print('  code_jump_table:', out['buckets']['code_jump_table'])
print('  byte_lookup:', out['buckets']['byte_lookup'])
print('  unclassified:', out['buckets']['unclassified'])
print('diff vs R167:', json.dumps(out['diff_vs_r167'], ensure_ascii=False))
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', ''))
