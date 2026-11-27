#!/usr/bin/env python3
"""R168 B：两套独立方法对 65 条不可解码洞的分类对账，并定位 4 条差异的参数根源。

方法 V（R167，值判据）：节内 4 字节网格 + 相位 0..3，要求 >=3 条且每条都是 .text 地址。
方法 C（R168，代码驱动）：先扫引用形态 ff 24/14 <SIB scale4,no base> disp32 与
                       8b <modrm r/m=100,scale4,no base> 8d disp32，再从 disp32 逐 4 字节延展。
两法只在（最小条目数、条目宽度）两个参数上不同 ⇒ 差异必须能被这两个参数逐条解释。

自错登记（本轮）：R168 首版把线性扫描的上界写成 SizeOfRawData(4,063,232)，
得起点 1,394,120（R166 的 raw_starts），而 VirtualSize(4,060,045) 口径是 1,392,527 ⇒ A6 假 FAIL。
本版同时报两个口径并各自给期望值，尾部 3,187 B 填充的解释一并给出。
"""
import sys, struct, json, random
sys.path.insert(0, '_r143')
import r143lib as L
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

B = L.Bin(); data = B.data; IB = B.IB
text = [s for s in B.secs if s[0] == '.text'][0]
T_LO = IB + text[1]; T_VSZ_HI = T_LO + text[2]; T_RAW_HI = T_LO + text[4]
md = Cs(CS_ARCH_X86, CS_MODE_32)

def linear(hi, chunk=65536):
    starts, resync = set(), []
    off = text[3]; end = text[3] + text[4]; base_vs = text[1]
    while off < end:
        c = data[off:min(off + chunk, end)]
        base = IB + (base_vs + (off - text[3]))
        consumed = 0
        for a, sz, mn, op in md.disasm_lite(c, base):
            if a - base + sz > len(c): break
            consumed = a - base + sz
            if a < hi: starts.add(a)
        off += consumed if consumed else 1
        if consumed == 0 and base < hi: resync.append(base)
    return starts, resync

st_v, rs_v = linear(T_VSZ_HI)   # VirtualSize 口径
st_r, rs_r = linear(1 << 40)    # 全 raw 口径

def span(start, width=4, maxent=8192, hi=None):
    hi = hi or T_VSZ_HI
    n = 0
    while n < maxent:
        v = B.dw(start + width * n)
        if v is None or not (T_LO <= v < hi): break
        n += 1
    return n

# ---- 方法 C 的引用站点 ----
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

def tabs_at(minent, width=4):
    out = []
    for s, mn, tab in sites:
        n = span(tab, width, hi=T_VSZ_HI)
        if n >= minent:
            out.append({'site': s, 'mn': mn, 'tab': tab, 'entries': n})
    return out

T2 = tabs_at(2); T3 = tabs_at(3)
R167 = json.load(open('_r167/r167d_holes_semantics_final.json'))
holes = [int(x, 16) for x in R167['holes']]
r167_in = set(int(x, 16) for x in R167['holes_in_table'])
r167_cls = {int(d['va'], 16): d['class'] for d in R167['holes_out_table']}
r167_w = R167['table_entry_width']

def cover(ts, va):
    hits = [t for t in ts if t['tab'] <= va < t['tab'] + 4 * t['entries']]
    return hits

def bucket(ts):
    return {h: cover(ts, h) for h in holes}

b2 = bucket(T2); b3 = bucket(T3)
in2 = [h for h in holes if b2[h]]; in3 = [h for h in holes if b3[h]]

# ---- 差异逐条归因 ----
diff_C_vs_167 = [h for h in holes if bool(b2[h]) != (h in r167_in)]
why = []
for h in diff_C_vs_167:
    nC = b2[h][0]['entries'] if b2[h] else 0
    w = r167_w.get(hex(h)) or r167_w.get('0x%x' % h)
    why.append({'va': hex(h), 'C_in': bool(b2[h]), 'C_entries': nC,
                'R167_in': h in r167_in, 'R167_class': r167_cls.get(h),
                'R167_entry_width': w,
                'reason': ('entry threshold 3 -> 2' if (b2[h] and nC == 2)
                           else ('entry width 3 vs 4' if (not b2[h] and w == 3)
                                 else 'UNEXPLAINED'))})

# ---- 剩余 7 条的证据：是否落在 3 字节 stride / 字节查表 ----
rest = [h for h in holes if not b2[h]]
rest_ev = []
for h in rest:
    n3 = span(h, 3, hi=T_VSZ_HI); n4 = span(h, 4, hi=T_VSZ_HI)
    inc = 0
    while inc < 32:
        a = B.rd(h + inc, 1); b_ = B.rd(h + inc + 1, 1)
        if not a or not b_ or b_[0] != a[0] + 1: break
        inc += 1
    rest_ev.append({'va': hex(h), 'span_w3_from_here': n3, 'span_w4_from_here': n4,
                    'asc_run_len': inc, 'R167_class': r167_cls.get(h),
                    'R167_in_table': h in r167_in, 'C_in3': bool(b3[h])})

# ---- 正反控 ----
A = []
A.append({'id': 'A0 VirtualSize 口径线性起点 == 1,392,527（R166 实测）',
          'ok': len(st_v) == 1392527, 'detail': str(len(st_v))})
A.append({'id': 'A1 全 raw 口径线性起点 == 1,394,120（R166 raw_starts）',
          'ok': len(st_r) == 1394120, 'detail': str(len(st_r))})
A.append({'id': 'A2 raw − vsz 恰 = 1,593 且全 >= VirtualSize 尾界（尾填充）',
          'ok': len(st_r - st_v) == 1593 and all(x >= T_VSZ_HI for x in st_r - st_v),
          'detail': str(len(st_r - st_v))})
A.append({'id': 'A3 VirtualSize 口径重对齐点 == 65 且与 R167 洞集合逐项相同',
          'ok': len(rs_v) == 65 and set(rs_v) == set(holes),
          'detail': '%d symdiff=%d' % (len(rs_v), len(set(rs_v) ^ set(holes)))})
A.append({'id': 'A4 正控 site 0x71f9d3 -> 表首 0x71f9e0（2 条目）被方法 C 找到',
          'ok': any(t['site'] == 0x71f9d3 and t['tab'] == 0x71f9e0 for t in T2)})
A.append({'id': 'A5 正控 site 0x7932f4 -> 表首 0x79342c 被方法 C 找到',
          'ok': any(t['site'] == 0x7932f4 and t['tab'] == 0x79342c for t in T2)})
# 负控 1：call [disp32]（ff 15）的目标必是函数入口、不是表 —— 同一延展器的假阳性基线
neg = 0; negN = 0
i = 0
while True:
    j = data.find(b'\xff\x15', i)
    if j < 0: break
    i = j + 1
    if not (text[3] <= j < text[3] + text[4]): continue
    negN += 1
    if span(struct.unpack_from('<I', data, j + 2)[0]) >= 2: neg += 1
A.append({'id': 'A6 负控 ff 15 call[disp32] 目标成表比例 < 5%（假阳性基线）',
          'ok': negN > 0 and neg / negN < 0.05, 'detail': '%d/%d=%.4f' % (neg, negN, neg / max(negN, 1))})
# 负控 2：表首 +1 错位不许再成表
mis = sum(1 for t in T2[:300] if span(t['tab'] + 1) >= 2)
A.append({'id': 'A7 负控 表首+1 错位后仍成表（前 300）<= 5', 'ok': mis <= 5, 'detail': str(mis)})
# 负控 3：500 个随机 .text 地址起延展成表(>=2)的比例即零假设基线
rnd = random.Random(20261127); bh = 0; NS = 500
for _ in range(NS):
    if span(rnd.randrange(T_LO, T_VSZ_HI - 16)) >= 2: bh += 1
A.append({'id': 'A8 负控 随机 500 个 .text 地址成表比例 < 5%', 'ok': bh / NS < 0.05,
          'detail': '%d/%d=%.4f' % (bh, NS, bh / NS)})
# 负控 4：条目里「指令起点」比例 —— 表若真是跳转表应高
slot_tot = slot_start = 0
for t in T2:
    for k in range(t['entries']):
        slot_tot += 1
        if B.dw(t['tab'] + 4 * k) in st_v: slot_start += 1
A.append({'id': 'A9 表内槽值落指令起点的比例 > 90%', 'ok': slot_tot and slot_start / slot_tot > 0.90,
          'detail': '%d/%d=%.4f' % (slot_start, slot_tot, slot_start / max(slot_tot, 1))})
A.append({'id': 'A10 差异 4 条全部可被（阈值 3->2 / 宽度 3vs4）解释',
          'ok': len(diff_C_vs_167) == 4 and all(x['reason'] != 'UNEXPLAINED' for x in why),
          'detail': repr([(x['va'], x['reason']) for x in why])})
A.append({'id': 'A11 两法在「阈值=3 且宽度=4」下 in 集合逐条相同',
          'ok': set(in3) == r167_in, 'detail': 'C3=%d R167=%d symdiff=%d'
          % (len(in3), len(r167_in), len(set(in3) ^ r167_in))})
A.append({'id': 'A12 65 = 58(方法C) + 5(字节查表) + 2(未归类) 逐项闭合',
          'ok': len(in2) + sum(1 for e in rest_ev if e['R167_class'] == 'byte_lookup_table') + 2 == 65,
          'detail': '%d + %d + 2' % (len(in2), sum(1 for e in rest_ev if e['R167_class'] == 'byte_lookup_table'))})

out = {'starts_vsz': len(st_v), 'starts_raw': len(st_r), 'resync_vsz': len(rs_v),
       'sites': len(sites), 'tables_ge2': len(T2), 'tables_ge3': len(T3),
       'distinct_tab_ge2': len(set(t['tab'] for t in T2)),
       'slot_total': slot_tot, 'slot_is_start': slot_start,
       'in_table_C': len(in2), 'in_table_C3': len(in3), 'in_table_R167': len(r167_in),
       'diff_C_vs_167': why, 'rest_7': rest_ev,
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r168/r168b_reconcile.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k not in ('rest_7',)}, ensure_ascii=False, indent=1)[:3500])
print('--- rest 7 ---')
for e in rest_ev: print(json.dumps(e, ensure_ascii=False))
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', ''))
