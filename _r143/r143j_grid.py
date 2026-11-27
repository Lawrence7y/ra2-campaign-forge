#!/usr/bin/env python3
"""R143 J：把历史上的「虚调用惯用法 9551 站 / 284 distinct 槽 / 最高第 342 槽」定位到具体口径。

穷举 6 个窗口参数 k ∈ {1,2,3,4,5,∞} × 2 个「是否允许窗口内改写该寄存器」× 2 个「是否要求
装载基址是对象类寄存器」= 24 个口径，一次性报出站数与 distinct 槽数与最高槽号，
看哪个三元组最接近 (9551, 284, 342)。
"""
import sys, json
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
ins = list(B.sweep(md))

def parse(i):
    a, sz, mn, op = ins[i]
    if not op: return ('nop', None)
    m = L.RE_CALL.match(op)
    if m and mn in ('call', 'jmp') and m.group(1) in L.GEN:
        return ('disp', (m.group(1), L.disp_of(m.group(2))))
    m = L.RE_LOAD.match(op)
    if m and mn == 'mov' and m.group(1) in L.GEN:
        return ('load', (m.group(1), m.group(2), L.disp_of(m.group(3))))
    if mn in L.W_MN:
        return ('write', op.partition(',')[0])
    return ('other', None)

P = [parse(i) for i in range(len(ins))]

def count(k, allow_clobber, obj_only):
    """k = 允许的最大间距（装载在 disp 之前的第 k 条）；k=None 表示数据流无限窗口。"""
    n = 0; slots = set()
    if k is not None:
        for i, (kind, d) in enumerate(P):
            if kind != 'disp': continue
            r, disp = d
            for back in range(1, k + 1):
                if i - back < 0: break
                kk, dd = P[i - back]
                if kk == 'load' and dd[0] == r:
                    if obj_only and dd[1] not in L.GEN: break
                    n += 1; slots.add(disp // 4)
                    break
                if not allow_clobber and kk in ('write',) and dd == r:
                    break
                if not allow_clobber and kk == 'disp':
                    break
        return n, len(slots), (max(slots) if slots else None)
    state = {}
    for i, (kind, d) in enumerate(P):
        if kind == 'disp':
            r, disp = d
            l = state.get(r)
            if l and (not obj_only or l[0] in L.GEN):
                n += 1; slots.add(disp // 4)
            for x in ('eax', 'ecx', 'edx'): state.pop(x, None)
        elif kind == 'load':
            state[d[0]] = (d[1], d[2], i)
        elif kind == 'write':
            state.pop(d, None)
    return n, len(slots), (max(slots) if slots else None)

out = {}
for k in (1, 2, 3, 4, 5, None):
    for allow in (True, False):
        for obj in (False, True):
            key = 'k=%s clobber=%s objbase=%s' % (k, allow, obj)
            n, ns, ms = count(k, allow, obj)
            out[key] = {'sites': n, 'slots': ns, 'max_slot': ms,
                        'dev_9551': round(abs(n - 9551) / 9551, 4)}
best = sorted(out.items(), key=lambda kv: kv[1]['dev_9551'])[:6]
print(json.dumps({'grid': out, 'best': best}, ensure_ascii=False, indent=1))
json.dump({'grid': out, 'best': best}, open('_r143/r143j_grid.json', 'w'), ensure_ascii=False, indent=1)
