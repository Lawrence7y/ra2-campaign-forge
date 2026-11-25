# -*- coding: utf-8 -*-
"""R127 共用：窗口内的小步符号执行（带分支分叉），判定「QI 返回指针被怎样使用」。

值域：
  ('Q',)     本次 QI 返回的接口指针
  ('VT',)    从 ('Q',) 偏移 0 读出的虚表指针
  ('IMM',k)  整数常量
其余一律「未知」（保守丢弃，不做猜测）。

栈：dsp 为相对「QI 调用返回那一刻的 esp」的位移。push 减 4；stdcall 调用把
自上次调用以来累计的 push 数 4*nargs 加回（nargs 在每次 call 与显式 add esp
之后清零）。这条假设与本映像里 QI 体一律 ret 0xc 的观察一致，且只影响栈槽编号
的相对一致性，不影响虚槽判据本身。

分支：条件跳转展开落空与跳转两支，工作集上限 MAXSTEP。结果 slots 是所有可
达路径上「以 ('VT',) 为基址、偏移为 K」的调用偏移并集 —— 上近似。
因此两类命题强度不同：
  「存在过槽 K」  —— 上近似为真 ⇒ 真实可达（只要至少一支路径真实可行）；
  「从未出现 >= 4」—— 上近似下都没有 ⇒ 真实可达路径上更没有（这一支是硬的）。
"""
REGS = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')
MEMPFX = ('dword ptr [', 'byte ptr [', 'word ptr [')
MAXSTEP = 20000


def num(t):
    t = t.strip()
    if t and t[0] in '0123456789':
        try:
            return int(t, 0)
        except ValueError:
            pass
    return None


def parse_mem(op):
    s = op.strip()
    for pfx in MEMPFX:
        if s.startswith(pfx):
            s = s[len(pfx):]
            if not s.endswith(']'):
                return None, None
            s = s[:-1]
            break
    else:
        return None, None
    if ' + ' in s:
        b, d = s.rsplit(' + ', 1)
        d = num(d)
    elif ' - ' in s:
        b, d = s.rsplit(' - ', 1)
        v = num(d)
        d = None if v is None else -v
    else:
        b, d = s, 0
    b = b.strip()
    if d is None:
        return None, None
    if b == 'esp' or b in REGS:
        return b, d
    if b.startswith('0x'):
        return ('abs', num(b)), d
    return None, None


def qi_ppv_key(ins, icall, back=8):
    """QI 形态：lea R,[esp+K] ; push R ; push riid ; push this ; ... call [reg]。
    因 lea 与 call 之间净 esp 变化为 0（push 3 个实参、callee ret 0xc 弹回），
    ppv 槽相对「调用返回时的 esp」的位移恰为 K。返回 K 或 None。"""
    for b in range(2, back + 1):
        if icall - b < 0: break
        p = ins[icall - b]
        if p[1] != 'lea' or '[esp + ' not in p[2]: continue
        tgt = p[2].split(',', 1)[0].strip()
        k = num(p[2].rsplit(' + ', 1)[1].rstrip(']'))
        if k is None: return None
        if not any(ins[j][1] == 'push' and ins[j][2].strip() == tgt
                   for j in range(icall - b + 1, icall + 1)):
            continue
        return k
    return None


def walk(ins, i0, window, seed_objin='eax', seed_ppv=None):
    lo, hi = i0, min(len(ins), i0 + window)
    init_stk = {} if seed_ppv is None else {seed_ppv: ('Q',)}
    work = [(i0, 0, {seed_objin: ('Q',)}, init_stk, 0)]
    seen = set()
    slots, iatcalls, stk_writes = set(), [], []
    steps = 0
    truncated = False
    while work:
        pc, dsp, reg0, stk0, nargs = work.pop()
        reg, stk = dict(reg0), dict(stk0)
        last_q = False
        while True:
            steps += 1
            if steps > MAXSTEP:
                truncated = True
                break
            if pc < lo or pc >= hi:
                break
            sig = (pc, dsp, tuple(sorted(reg.items())),
                   tuple(sorted((k, v) for k, v in stk.items() if v == ('Q',))))
            if sig in seen:
                break
            seen.add(sig)
            a, m, o = ins[pc]
            if m == 'ret' or m == '.byte':
                break
            if m == 'push':
                # 记录本次 push 的值是不是 Q 派生：OleSaveToStream 的第 1 实参
                # 是否就是 QI 结果，正是 L2 判据。
                _pv = _eval(o, reg, stk, dsp)
                last_q = (_pv == ('Q',))
                dsp -= 4; nargs += 1; pc += 1; continue
            if m == 'pop':
                dsp += 4; nargs = max(0, nargs - 1)
                if o.strip() in REGS: reg.pop(o.strip(), None)
                pc += 1; continue
            if m in ('add', 'sub') and o.strip().startswith('esp, '):
                v = num(o.split(',', 1)[1]) or 0
                dsp += v if m == 'add' else -v
                nargs = 0
                pc += 1; continue
            if m == 'mov' and ',' in o:
                d, src = [x.strip() for x in o.split(',', 1)]
                v = _eval(src, reg, stk, dsp)
                if d in REGS:
                    if v is None: reg.pop(d, None)
                    else: reg[d] = v
                else:
                    b, disp = parse_mem(d)
                    if b == 'esp':
                        k = dsp + disp
                        if v is None: stk.pop(k, None)
                        else:
                            stk[k] = v
                            stk_writes.append((a, k))
                    elif b in REGS:
                        # 写对象字段：把基址寄存器与 ('Q',) 的关系记下来不值得，
                        # 本轮判据不需要 —— 记一次事件即可（见报告边界）。
                        pass
                pc += 1; continue
            if m.startswith('set') and o.strip() in ('cl', 'bl', 'al', 'dl'):
                # 条件码 -> 8 位掩码位。只用于识别 setl cl / dec ecx / and ecx,edx
                # 这一条「失败则清零否则保留指针」的编译器惯用法（0x5046a6）。
                reg[{ 'cl': 'ecx', 'bl': 'ebx', 'al': 'eax', 'dl': 'edx'}[o.strip()]] = ('MASK',)
                pc += 1
                continue
            if m == 'dec' and o.strip() in REGS and reg.get(o.strip()) == ('MASK',):
                reg[o.strip()] = ('MASKALL',)
                pc += 1
                continue
            if m == 'and' and ',' in o:
                d, s2 = [x.strip() for x in o.split(',', 1)]
                if d in REGS and reg.get(d) == ('MASKALL',) and reg.get(s2) == ('Q',):
                    reg[d] = ('Q',)
                elif d in REGS:
                    reg.pop(d, None)
                pc += 1
                continue
            if m == 'xor' and ',' in o:
                d, s2 = [x.strip() for x in o.split(',', 1)]
                if d == s2 and d in REGS: reg[d] = ('IMM', 0)
                pc += 1; continue
            if m == 'lea' and ',' in o:
                d = o.split(',', 1)[0].strip()
                if d in REGS: reg.pop(d, None)
                pc += 1; continue
            if m == 'call':
                tgt = o.strip()
                if tgt.startswith('dword ptr ['):
                    inner = tgt[len('dword ptr ['):-1]
                    b, disp = parse_mem('dword ptr [%s]' % inner)
                    if b in REGS:
                        if reg.get(b) == ('VT',) and disp is not None:
                            slots.add(disp)
                    elif b and b[0] == 'abs':
                        iatcalls.append((a, b[1], last_q))
                reg.pop('eax', None)
                dsp += 4 * nargs
                nargs = 0
                pc += 1; continue
            if m == 'jmp':
                t = num(o)
                nxt = _index_of(ins, t, lo, hi) if t is not None else None
                if nxt is None: break
                pc = nxt; continue
            if m.startswith('j'):
                t = num(o)
                if t is not None:
                    nxt = _index_of(ins, t, lo, hi)
                    if nxt is not None:
                        work.append((nxt, dsp, reg, stk, 0))
                pc += 1; continue
            if ',' in o:
                d = o.split(',', 1)[0].strip()
                if d in REGS: reg.pop(d, None)
            pc += 1
    return {'slots': slots, 'iatcalls': iatcalls, 'truncated': truncated,
            'steps': steps, 'states': len(seen), 'stk_writes': stk_writes}


def _eval(s, reg, stk, dsp):
    s = s.strip()
    if s in REGS:
        return reg.get(s)
    b, disp = parse_mem(s)
    if b == 'esp':
        return stk.get(dsp + disp)
    if b in REGS:
        if reg.get(b) == ('Q',) and disp == 0:
            return ('VT',)
        return None
    n = num(s)
    return ('IMM', n) if n is not None else None


def _index_of(ins, va, lo, hi):
    for j in range(lo, hi):
        if ins[j][0] == va: return j
        if ins[j][0] > va: return None
    return None
