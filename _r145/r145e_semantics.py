#!/usr/bin/env python3
"""R145 E：负位移装表站点的语义定性 —— 基址寄存器偏置 + 同日槽多次写（last-store-wins）。

r145d 已证：宽容解析器把 R144 残余从 5 张压到 4 张，唯一新增覆盖是 0x7E6060，
站点在 0x4A8660 `mov dword ptr [eax - 8],0x7e6060`，循环 `add eax,0x18` 共 5 轮。
本脚本回答三件事：
 Q1 基址偏置：若把 eax 记作「对象起点 + B」，则循环内所有写相对对象起点的偏移是多少？
    用「同一循环里写到的最大正偏移 + 0x18 对齐」反推 B，并检验 B=8 时布局是否自洽（无重叠、无空洞）。
 Q2 三重写：同一槽在一轮里被写 3 次不同虚表（0x7E192C / 0x7E4F64 / 0x7E6060）⇒
    运行时只有最后一个生效 ⇒「该地址被装过」与「该地址是活虚表」不是同一命题。
 Q3 那 5 轮覆盖的静态数组（.data）在文件里是否为 0 ⇒ 为什么 F6（.data 初值 == vt）抓不到它。
"""
import sys, re, json, struct, collections, hashlib
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
lo, hi = 0x4A863C, 0x4A866C
body = [(a, sz, mn, L.norm(op)) for a, sz, mn, op in md.disasm_lite(B.rd(lo, hi - lo), lo)]
TOL = re.compile(r'^(?:dword|byte) ptr \[(.+?)\](?:,(.+))?$')
def memoff(s):
    s = s.replace(' ', '')
    m = re.fullmatch(r'([a-z0-9]+)([+-])(0x[0-9a-f]+|\d+)', s)
    if m:
        v = int(m.group(3), 16) if m.group(3).startswith('0x') else int(m.group(3))
        return m.group(1), (-v if m.group(2) == '-' else v)
    m = re.fullmatch(r'([a-z0-9]+)', s)
    if m: return m.group(1), 0
    return None

writes = []
for a, sz, mn, op in body:
    if mn != 'mov': continue
    m = TOL.match(op)
    if not m: continue
    bo = memoff(m.group(1))
    if bo is None: continue
    writes.append({'va': hex(a), 'base': bo[0], 'disp': bo[1],
                   'size': 4 if op.startswith('dword') else 1,
                   'src': (m.group(2) or '').strip()})
bases = collections.Counter(w['base'] for w in writes)
spans = collections.Counter(w['base'] for w in writes)  # placeholder
disp_min = min(w['disp'] for w in writes if w['base'] == 'eax')
disp_max = max(w['disp'] + w['size'] for w in writes if w['base'] == 'eax')
# 步进与轮数
step = None; rounds = None
for a, sz, mn, op in body:
    if mn == 'add' and op.startswith('eax,'): step = int(op.split(',')[1], 16)
    if mn == 'dec': rounds = op
arr_base = 0x8a0368           # mov eax,0x8a0368 处（在 lo 之前一条，单独读）
b0 = B.rd(0x4A8630, 8)
first = [(hex(a), mn, L.norm(op)) for a, sz, mn, op in md.disasm_lite(b0, 0x4A8630)]
arr_lo = 0
for a, sz, mn, op in md.disasm_lite(b0, 0x4A8630):
    opn = L.norm(op)
    if mn == 'mov' and opn.startswith('eax,0x'): arr_lo = int(opn.split(',')[1], 16)
N = 5
array_offs = [arr_lo + i * step for i in range(N)]
array_vals = [[B.dw(x + 4 * k) for k in range(6)] for x in array_offs]
secs = {hex(x): B.sec_of(x) for x in array_offs}
# 文件内是否真有这些字节（.data 的 RawSize 只到 0x87E000，其后是未初始化尾）
in_file = {hex(x): (B.va2off(x) is not None) for x in array_offs}
data_sec = [s2 for s2 in B.secs if s2[0] == '.data'][0]
data_raw_end = B.IB + data_sec[1] + data_sec[4]
data_vs_end = B.IB + data_sec[1] + data_sec[2]
td_of_vt = {}
for vt in (0x7E192C, 0x7E4F64, 0x7E6060):
    c = B.dw(vt - 4)
    td_of_vt[hex(vt)] = hex(B.dw(c + 12) or 0) if c else None
# 基址偏置反推：对象起点 = eax + B，要求 B = -disp_min 且 array_lo + B 是元素起点
B_bias = -disp_min
obj0 = arr_lo + B_bias
layout = sorted(((w['disp'] + B_bias, w['size'], w['src']) for w in writes if w['base'] == 'eax'))
# 同一槽多次写不算重叠：先按槽去重（保留最大宽度）
by_slot = {}
for off, size, src in layout:
    by_slot[off] = max(by_slot.get(off, 0), size)
uniq = sorted((o, z) for o, z in by_slot.items())
overlap = False
for i in range(len(uniq) - 1):
    if uniq[i][0] + uniq[i][1] > uniq[i + 1][0]: overlap = True
slots = sorted(set(x[0] for x in layout))
layout_ok = (slots[0] == 0 and not overlap and max(o + z for o, z in uniq) <= step)
same_slot_writes = [w for w in writes if w['disp'] == -8 and w['src'].startswith('0x')]
res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(),
 'loop_head': first, 'array_base_va': hex(arr_lo), 'step': step, 'rounds_reg': rounds,
 'writes': writes,
 'disp_range_eaх': [disp_min, disp_max],
 'B_bias_derived': B_bias,
 'object0_va': hex(obj0),
 'layout_offsets': [[o, s, v] for o, s, v in layout],
 'layout_ok': layout_ok, 'layout_overlap': overlap,
 'slots': slots, 'object_size': step,
 'same_slot_writes': same_slot_writes,
 'same_slot_srcs': [w['src'] for w in same_slot_writes],
 'last_store_wins': same_slot_writes[-1]['src'] if same_slot_writes else None,
 'array_elems': [hex(x) for x in array_offs], 'array_secs': secs,
 'array_file_values_zero': all(all(v == 0 for v in row) for row in array_vals),
 'array_in_file': in_file, 'data_raw_end': hex(data_raw_end), 'data_vs_end': hex(data_vs_end),
 'td_of_three_vt': td_of_vt,
 'array_file_first6': array_vals[0],
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('正控：循环步进 0x18、计数寄存器 edx=5', step == 0x18 and rounds == 'edx', [step, rounds])
chk('正控：循环内写基址只有 eax', set(bases) == {'eax'}, dict(bases))
chk('位移下界 -8、上界 0xc+4=0x10（跨度恰 0x18）', disp_min == -8 and disp_max == 0x10, [disp_min, disp_max])
chk('反推基址偏置 B=8（eax = 对象起点 + 8）', B_bias == 8, B_bias)
chk('B=8 时布局无重叠且首槽落在 0（vptr 在对象偏移 0）', layout_ok, [uniq, overlap, step])
chk('同一槽 [-8] 在一轮里被写 3 次', len(same_slot_writes) == 3, len(same_slot_writes))
chk('最后一次写的虚表 = 0x7E6060（last-store-wins）', (same_slot_writes[-1]['src'] if same_slot_writes else '').lower() == '0x7e6060', same_slot_writes[-1] if same_slot_writes else None)
chk('5 个元素地址全在 .data', all(s == '.data' for s in secs.values()), secs)
chk('文件里没有这 5 个元素的字节（.data 未初始化尾，va2off=None）', not any(in_file.values()), in_file)
chk('反控：.data RawEnd < 数组 VA <= .data VEnd（确属 BSS 尾）', data_raw_end < 0x8A0368 <= data_vs_end, [hex(data_raw_end), hex(data_vs_end)])
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r145/r145e_semantics.json', 'w'), indent=1)
for k in ('loop_head','array_base_va','step','B_bias_derived','object0_va','layout_offsets','slots','same_slot_srcs','last_store_wins','array_elems','array_file_values_zero'):
    print(k, '=', json.dumps(res[k], ensure_ascii=False))
for p in POS: print(('PASS ' if p[1] else 'FAIL ') + '%-52s %s' % (p[0], p[2]))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))
