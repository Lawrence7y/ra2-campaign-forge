# -*- coding: utf-8 -*-
"""R127 共用：向后切片（backward slice）解析「某个 call dword ptr [R + K] 的 R 从哪来」。

不做跨基本块的控制流分析，沿线性序列取最近写者；回溯窗口 14 条；遇到 call 即停
（不再信任更早的写入）。这是本库既有判据口径（LEAD_LOCK DS6 已记其局限性），
本轮只把它用于「是否出现过某个虚槽」这一存在性命题，不用于否定不可达性。
"""
REGS = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')


def num(t):
    t = t.strip()
    if t and t[0] in '0123456789':
        try:
            return int(t, 0)
        except ValueError:
            pass
    return None


def mem_base(op):
    s = op.strip()
    for pfx in ('dword ptr [', 'byte ptr [', 'word ptr ['):
        if s.startswith(pfx):
            s = s[len(pfx):]
            if not s.endswith(']'):
                return (None, None)
            s = s[:-1]
            break
    else:
        return (None, None)
    if ' + ' in s:
        b, d = s.rsplit(' + ', 1)
        return b.strip(), num(d)
    if ' - ' in s:
        b, d = s.rsplit(' - ', 1)
        v = num(d)
        return b.strip(), (None if v is None else -v)
    return s.strip(), 0


def split_base(op):
    """解析 'reg + K' / 'reg - K' / 'reg' 形式，返回 (reg, K)。"""
    s = op.strip()
    if ' + ' in s:
        b, d = s.rsplit(' + ', 1)
        return b.strip(), num(d)
    if ' - ' in s:
        b, d = s.rsplit(' - ', 1)
        v = num(d)
        return b.strip(), (None if v is None else -v)
    return s, 0


def writer(ins, i, reg, back=14):
    """返回 (idx, kind, detail)：kind in orig / from_stack / from_mem / imm / unknown。"""
    for j in range(i - 1, max(0, i - back) - 1, -1):
        a, m, o = ins[j]
        if m == 'call':
            return None
        if m in ('mov', 'lea') and ',' in o:
            d, src = [x.strip() for x in o.split(',', 1)]
            if d != reg:
                continue
            if m == 'lea':
                return (j, 'orig', src)
            if src.startswith('dword ptr [esp'):
                return (j, 'from_stack', mem_base(src))
            if src.startswith('dword ptr ['):
                return (j, 'from_mem', mem_base(src))
            if src in REGS:
                return (j, 'from_reg', src)
            n = num(src)
            if n is not None:
                return (j, 'imm', n)
            return (j, 'unknown', src)
        if m == 'xor' and ',' in o:
            d, s2 = [x.strip() for x in o.split(',', 1)]
            if d == reg and s2 == reg:
                return (j, 'imm', 0)
    return None


def ppv_slot_of(ins, icall, back=8):
    """QI 形态：lea R,[esp+K] ; ... push R ; push riid ; push this ; call [reg]。
    返回 K（相对该 lea 的 esp），或用 None。"""
    for b in range(2, back + 1):
        if icall - b < 0:
            break
        p = ins[icall - b]
        if p[1] != 'lea' or '[esp + ' not in p[2]:
            continue
        tgt = p[2].split(',', 1)[0].strip()
        k = num(p[2].rsplit(' + ', 1)[1].rstrip(']'))
        if k is None:
            return None
        if any(ins[j][1] == 'push' and ins[j][2].strip() == tgt
               for j in range(icall - b + 1, icall + 1)):
            return k
    return None
