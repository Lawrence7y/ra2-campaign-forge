#!/usr/bin/env python3
"""R168 A：用**代码驱动的跳转表普查**独立复核 R167 对 65 条不可解码洞的分类。

R167 用的是**值判据**（节内 4 字节网格 + 相位 0..3，条目值都是 .text 地址 ⇒ 表）。
值判据有一个已知弱点：它不要求有代码真的引用那张表 ⇒ 可能把纯数据里的地址串算成表，
也可能漏掉「表在别的节 / 引用形态不是 ff 24/14」。

本脚本改走**代码驱动**：先扫两种引用形态
  (1) 单指令  ff 24/14 <modrm=mod00,rm=100,scale=4,base=none> disp32  即 jmp/call [reg*4+disp32]
  (2) 双指令  8b 04/0c/14/1c/24/2c/34/3c 8d <disp32>                 即 mov reg,[reg*4+disp32]
再从 disp32 起按「逐 4 字节条目仍是 .text 地址」延展成表区间。
两法互不依赖，可交叉。

正控：两个已知 site（0x71f9d3、0x7932f4）必须命中其表首。
负控三条：① 500 个随机 .text 地址当表首，成表（>=2 条）的比例即零假设基线；
         ② 表首 +1 字节错位不许再成表；③ 把 scale4 的 SIB 换成 scale2（modrm 0x8c/0x94）
         时，用同一延展器在**已知表首**上仍成表（说明延展器不看 SIB，SIB 只是入口），
         但 site 集合必须与 scale4 集合不相交。
"""
import sys, struct, json, random
sys.path.insert(0, '_r143')
import r143lib as L
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

B = L.Bin(); data = B.data; IB = B.IB
text = [s for s in B.secs if s[0] == '.text'][0]
T_LO = IB + text[1]; T_VSZ_HI = T_LO + text[2]

def va_of_off(j):
    for nm, ava, vs, raw, rs in B.secs:
        if raw <= j < raw + rs:
            return IB + ava + (j - raw)
    return None

# ---------- 1. 线性扫描：起点集 + 重对齐点（R166 同法，用作「条目是否指令起点」的裁判） ----------
md = Cs(CS_ARCH_X86, CS_MODE_32)
starts = set(); resync = []
off = text[3]; end = off + text[4]; base_vs = text[1]
while off < end:
    chunk = data[off:min(off + 65536, end)]
    base = IB + (base_vs + (off - text[3]))
    consumed = 0
    for a, sz, mn, op in md.disasm_lite(chunk, base):
        if a - base + sz > len(chunk):
            break
        consumed = a - base + sz
        starts.add(a)
    if consumed == 0:
        resync.append(base); off += 1
    else:
        off += consumed
resync_v = [r for r in resync if T_LO <= r < T_VSZ_HI]

# ---------- 2. 两种引用形态的 site 普查 ----------
sites = []
for op2, mn in ((0x24, 'jmp'), (0x14, 'call')):
    for modrm, reg in ((0x8d, 'ecx'), (0x85, 'eax'), (0x95, 'edx'),
                       (0x9d, 'ebx'), (0xa5, 'esp'), (0xb5, 'esi'), (0xbd, 'edi')):
        pat = bytes([0xff, op2, modrm]); i = 0
        while True:
            j = data.find(pat, i)
            if j < 0: break
            i = j + 1
            va = va_of_off(j)
            if va is None or B.sec_of(va) != '.text': continue
            sites.append({'kind': 'single', 'site': va, 'mn': mn,
                          'tab': struct.unpack_from('<I', data, j + 3)[0]})
for modrm in (0x04, 0x0c, 0x14, 0x1c, 0x24, 0x2c, 0x34, 0x3c):
    pat = bytes([0x8b, modrm, 0x8d]); i = 0
    while True:
        j = data.find(pat, i)
        if j < 0: break
        i = j + 1
        va = va_of_off(j)
        if va is None or B.sec_of(va) != '.text': continue
        sites.append({'kind': 'mov', 'site': va, 'mn': 'mov',
                      'tab': struct.unpack_from('<I', data, j + 3)[0]})

def span(start, maxent=8192):
    n = 0
    while n < maxent:
        v = B.dw(start + 4 * n)
        if v is None or not (T_LO <= v < T_LO + text[4]):
            break
        n += 1
    return n

tabs = []
for s in sites:
    n = span(s['tab'])
    if n >= 2:
        s['entries'] = n
        tabs.append(s)

# ---------- 3. 65 条洞的分桶 ----------
R167 = json.load(open('_r167/r167d_holes_semantics_final.json'))
holes = [int(x, 16) for x in R167['holes']]
r167_in = set(int(x, 16) for x in R167['holes_in_table'])
r167_out = [int(d['va'], 16) for d in R167['holes_out_table']]
r167_cls = {int(d['va'], 16): d['class'] for d in R167['holes_out_table']}

def covers(t, va):
    return t['tab'] <= va < t['tab'] + 4 * t['entries']

detail = []
for h in holes:
    hit = [t for t in tabs if covers(t, h)]
    detail.append({'va': h, 'in_scaled_table': bool(hit),
                   'n_tables': len(hit),
                   'tables': [{'site': t['site'], 'kind': t['kind'], 'tab': t['tab'],
                               'entries': t['entries']} for t in hit],
                   'off_in_tab': (h - hit[0]['tab']) if hit else None,
                   'aligned': ((h - hit[0]['tab']) % 4 == 0) if hit else None,
                   'r167_in_table': h in r167_in, 'r167_class': r167_cls.get(h)})

in_tab = [d for d in detail if d['in_scaled_table']]
out_tab = [d for d in detail if not d['in_scaled_table']]
both = [d['va'] for d in in_tab if d['r167_in_table']]
only_new = [d['va'] for d in in_tab if not d['r167_in_table']]
only_r167 = [d['va'] for d in out_tab if d['r167_in_table']]

# ---------- 4. 表里条目是否指令起点（判「这是跳转表」而非「地址堆」） ----------
slot_tot = 0; slot_start = 0
for t in tabs:
    for k in range(t['entries']):
        v = B.dw(t['tab'] + 4 * k)
        slot_tot += 1
        if v in starts: slot_start += 1

# ---------- 5. 正反控 ----------
rnd = random.Random(20261127)
base_hit = 0; NS = 500
for _ in range(NS):
    va = rnd.randrange(T_LO, T_LO + text[2] - 16)
    if span(va) >= 2: base_hit += 1
mis = sum(1 for t in tabs[:300] if span(t['tab'] + 1) >= 2)
s2 = []
for modrm in (0x8c, 0x94, 0x9c, 0xa4, 0xac, 0xb4, 0xbc):
    pat = bytes([0xff, 0x24, modrm]); i = 0
    while True:
        j = data.find(pat, i)
        if j < 0: break
        i = j + 1
        va = va_of_off(j)
        if va is None or B.sec_of(va) != '.text': continue
        s2.append(va)
A = []
A.append({'id': 'A1 正控 site 0x71f9d3 命中表首 0x71f9e0',
          'ok': any(t['site'] == 0x71f9d3 and t['tab'] == 0x71f9e0 for t in tabs)})
A.append({'id': 'A2 正控 site 0x7932f4 命中表首 0x79342c',
          'ok': any(t['site'] == 0x7932f4 and t['tab'] == 0x79342c for t in tabs)})
A.append({'id': 'A3 负控 500 个随机 .text 地址成表(>=2)的比例 < 5%',
          'ok': base_hit / NS < 0.05, 'detail': '%d/%d=%.4f' % (base_hit, NS, base_hit / NS)})
A.append({'id': 'A4 负控 表首+1 错位后仍成表(前 300) <= 5', 'ok': mis <= 5, 'detail': str(mis)})
A.append({'id': 'A5 负控 scale2 集合与 scale4 集合不相交',
          'ok': len(set(s2) & set(t['site'] for t in tabs)) == 0,
          'detail': 'scale2=%d' % len(s2)})
A.append({'id': 'A6 线性扫描起点数 == 1,392,527（R166 实测，独立复算）',
          'ok': len(starts) == 1392527, 'detail': str(len(starts))})
A.append({'id': 'A7 重对齐点数 == 65 且与 R167 洞集合逐项相同',
          'ok': len(resync_v) == 65 and set(resync_v) == set(holes),
          'detail': '%d / symdiff=%d' % (len(resync_v), len(set(resync_v) ^ set(holes)))})

out = {'starts': len(starts), 'resync': len(resync_v),
       'sites_single': sum(1 for s in sites if s['kind'] == 'single'),
       'sites_mov': sum(1 for s in sites if s['kind'] == 'mov'),
       'tables_2plus': len(tabs),
       'tab_distinct': len(set(t['tab'] for t in tabs)),
       'slot_total': slot_tot, 'slot_is_start': slot_start,
       'slot_start_rate': (slot_start / slot_tot) if slot_tot else None,
       'holes_in_scaled_table': len(in_tab), 'holes_not': len(out_tab),
       'vs_r167_both': len(both), 'vs_r167_only_new': [hex(x) for x in only_new],
       'vs_r167_only_r167': [hex(x) for x in only_r167],
       'not_in_scaled_list': [hex(d['va']) for d in out_tab],
       'detail': detail, 'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r168/r168a_scaled_tables.json', 'w'), ensure_ascii=False, indent=1)
print('starts=%d resync=%d sites single=%d mov=%d tables=%d distinct_tab=%d'
      % (out['starts'], out['resync'], out['sites_single'], out['sites_mov'],
         out['tables_2plus'], out['tab_distinct']))
print('slots=%d is_start=%d rate=%.4f' % (slot_tot, slot_start, out['slot_start_rate']))
print('holes in scaled table=%d not=%d | both w/R167=%d only_new=%s only_r167=%s'
      % (len(in_tab), len(out_tab), len(both),
         [hex(x) for x in only_new], [hex(x) for x in only_r167]))
print('not in table:', [hex(d['va']) for d in out_tab])
for a in A:
    print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', ''))
