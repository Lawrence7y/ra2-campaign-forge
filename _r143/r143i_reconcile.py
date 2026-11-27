#!/usr/bin/env python3
"""R143 I：口径对账 —— 历史正文里的「虚调用惯用法 9551 站」到底是什么定义。

四个候选口径，一次算完：
  V1 严格相邻：mov rX, dword ptr [rY(+d)] 之后紧邻的下一条是 call/jmp dword ptr [rX+4k]
  V2 允许插入：装载后 <=2 条指令内出现 call/jmp dword ptr [rX+4k]
  V3 数据流：装载后该寄存器未被改写，直到出现 call/jmp dword ptr [rX+4k]（本脚本主口径）
  V4 = V3 再限制槽号 /4 <= 400（历史正文提到「最高第 342 槽」）
另外把 V3 按「装载位移是否为 0」拆开，回答 vt==[obj] 这条判读。

判据：V1/V2/V3/V4 里哪个能给出 9551（±2%）；若都不是，判断正文明示的口径缺项。
"""
import sys, json, re, collections
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin()
md = Cs(CS_ARCH_X86, CS_MODE_32)
ins = list(B.sweep(md))          # 一次列表化（1.39M 条，元组很小，可接受）

def is_load(mn, op):
    if mn != 'mov': return None
    m = L.RE_LOAD.match(op)
    if not m: return None
    return m.group(1), m.group(2), L.disp_of(m.group(3))

def is_disp(mn, op):
    if mn not in ('call', 'jmp'): return None
    m = L.RE_CALL.match(op)
    if not m: return None
    r = m.group(1)
    if r not in L.GEN: return None
    return r, L.disp_of(m.group(2))

V1 = []; V2 = []; V3 = []
state = {}
for i, (a, sz, mn, op) in enumerate(ins):
    if not op: continue
    dd = is_disp(mn, op)
    if dd:
        r, d = dd
        if i >= 1:
            p = is_load(ins[i-1][2], ins[i-1][3])
            if p and p[0] == r: V1.append((a, r, d, p[1], p[2]))
        for back in (1, 2):
            if i >= back:
                p = is_load(ins[i-back][2], ins[i-back][3])
                if p and p[0] == r:
                    V2.append((a, r, d, p[1], p[2])); break
        l = state.get(r)
        if l: V3.append((a, r, d, l[0], l[1], l[2]))
        for x in ('eax', 'ecx', 'edx'): state.pop(x, None)
        continue
    p = is_load(mn, op)
    if p:
        state[p[0]] = (p[1], p[2], a)
        continue
    if mn == 'lea' and ',' in op:
        state.pop(op.partition(',')[0], None)
    elif mn in L.W_MN:
        state.pop(op.partition(',')[0], None)

V4 = [x for x in V3 if 0 <= x[2] // 4 <= 400]
def slots(v): return len({x[2] // 4 for x in v})
def maxslot(v): return max((x[2] // 4 for x in v), default=None)
def d0share(v):
    z = sum(1 for x in v if x[4] == 0)
    return round(z / max(1, len(v)), 4)

res = {
 'instructions': len(ins),
 'V1_adjacent': len(V1), 'V2_within2': len(V2), 'V3_dataflow': len(V3), 'V4_slot_le400': len(V4),
 'V3_distinct_slots': slots(V3), 'V3_max_slot': maxslot(V3),
 'V1_distinct_slots': slots(V1), 'V2_distinct_slots': slots(V2),
 'V3_disp0_share': d0share(V3),
 'V3_disp0_sites': sum(1 for x in V3 if x[4] == 0),
 'V3_disp4_sites': sum(1 for x in V3 if x[4] == 4),
 'V3_disp8_sites': sum(1 for x in V3 if x[4] == 8),
 'V3_load_base_regs': dict(collections.Counter(x[3] for x in V3)),
 'V3_obj_base': sum(1 for x in V3 if x[3] in L.GEN),
 'V3_stk_base': sum(1 for x in V3 if x[3] in L.STK),
 'V3_load_disp_top': collections.Counter(x[4] for x in V3).most_common(10),
 'match_9551': {k: v for k, v in (('V1', len(V1)), ('V2', len(V2)), ('V3', len(V3)), ('V4', len(V4)))
                if abs(v - 9551) <= 0.02 * 9551},
}
print(json.dumps(res, ensure_ascii=False, indent=1))
json.dump(res, open('_r143/r143i_reconcile.json', 'w'), ensure_ascii=False, indent=1)
