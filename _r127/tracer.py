# -*- coding: utf-8 -*-
"""R127 共用：直线窗口内的简化抽象解释器（只服务本轮定名测量）。

值表示：
  ('obj', name)   持有一个 COM 接口指针
  ('vptr', name)  从接口指针偏移 0 取出的虚表指针
  ('imm', k)      整数常量
  ('iatv', va)    从绝对地址读出的值（导入函数地址）
栈槽键 = 相对窗口起点的 esp 偏移；push/pop/add esp 都记账。
调用约定：对本窗口里的 COM 调用按 stdcall 处理（弹出此前 push 的全部实参）；
遇到调用方显式 add esp,N 则以它为准。这条假设会写进报告的边界说明。
"""
import struct

REGS = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')
MEMPFX = ('dword ptr [', 'byte ptr [', 'word ptr [')


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
    if b in REGS:
        return b, d
    if b.startswith('0x'):
        return ('abs', num(b)), d
    return None, None


class Sim:
    """从 i0（QI 的 call 指令的**下一条**）开始，执行 limit 条。"""

    def __init__(self, ins, i0, esp0=0, limit=90, stdcall_pop=True):
        self.ins = ins
        self.i0 = i0
        self.limit = limit
        self.reg = {}
        self.stk = {}
        self.esp = esp0
        self.npush = 0
        self.events = []
        self.ret_at = None
        self.stdcall_pop = stdcall_pop

    def key(self, disp):
        return self.esp + disp

    def eval(self, s):
        s = s.strip()
        if s in REGS:
            return self.reg.get(s)
        if s == 'esp':
            return ('esp', 0)
        b, disp = parse_mem(s)
        if b == 'esp':
            return self.stk.get(self.key(disp))
        if b in REGS:
            base = self.reg.get(b)
            if base and base[0] == 'obj' and disp == 0:
                return ('vptr', base[1])
            return None
        if b and b[0] == 'abs':
            return ('iatv', b[1])
        n = num(s)
        return ('imm', n) if n is not None else None

    def run(self, obj_name):
        ins = self.ins
        self.reg['eax'] = ('obj', obj_name)
        for j in range(self.i0, min(len(ins), self.i0 + self.limit)):
            a, m, o = ins[j]
            if m == 'ret':
                self.ret_at = a
                break
            if m == 'push':
                self.esp -= 4
                self.npush += 1
                self.events.append((a, 'push', o.strip()))
                continue
            if m == 'pop':
                self.esp += 4
                self.npush = max(0, self.npush - 1)
                if o.strip() in REGS:
                    self.reg.pop(o.strip(), None)
                continue
            if m == 'add' and o.strip().startswith('esp, '):
                self.esp += num(o.split(',', 1)[1]) or 0
                self.npush = 0
                continue
            if m == 'sub' and o.strip().startswith('esp, '):
                self.esp -= num(o.split(',', 1)[1]) or 0
                continue
            if m == 'mov' and ',' in o:
                d, src = [x.strip() for x in o.split(',', 1)]
                v = self.eval(src)
                if d in REGS:
                    if v is None: self.reg.pop(d, None)
                    else: self.reg[d] = v
                else:
                    b, disp = parse_mem(d)
                    if b == 'esp':
                        k = self.key(disp)
                        if v is None: self.stk.pop(k, None)
                        else:
                            self.stk[k] = v
                            self.events.append((a, 'stkslot', k, v))
                    elif b in REGS or (b and b[0] == 'abs'):
                        self.events.append((a, 'store', d))
                continue
            if m == 'lea':
                d = o.split(',', 1)[0].strip()
                if d in REGS: self.reg.pop(d, None)
                continue
            if m == 'xor' and ',' in o:
                d, src = [x.strip() for x in o.split(',', 1)]
                if d == src and d in REGS: self.reg[d] = ('imm', 0)
                continue
            if m == 'call':
                tgt = o.strip()
                vt = None
                iatv = None
                if tgt.startswith('dword ptr ['):
                    inner = tgt[len('dword ptr ['):-1]
                    b, disp = parse_mem('dword ptr [%s]' % inner)
                    if b in REGS:
                        base = self.reg.get(b)
                        if base and base[0] == 'vptr':
                            vt = (disp, base[1])
                    elif b and b[0] == 'abs':
                        iatv = b[1]
                elif num(tgt) is None:
                    r = self.reg.get(tgt)
                    if r and r[0] == 'iatv':
                        iatv = r[1]
                if vt:
                    self.events.append((a, 'vcall', vt[0], vt[1]))
                elif iatv is not None:
                    self.events.append((a, 'iatcall', iatv))
                if self.stdcall_pop:
                    self.esp += 4 * self.npush
                    self.npush = 0
                self.reg.pop('eax', None)
                continue
            if m in ('test', 'cmp', 'jmp', 'nop', 'int3', 'inc', 'dec',
                     'and', 'or', 'shl', 'shr', 'neg', 'not', 'xchg',
                     'setl', 'sete', 'setge', 'setne', 'setg', 'movzx',
                     'movsx', 'imul', 'saHF', 'and_', 'fld', 'fstp'):
                if m.startswith('j'):
                    pass
                continue
            # 其它指令：保守地把写到的寄存器置未知
            if ',' in o:
                d = o.split(',', 1)[0].strip()
                if d in REGS: self.reg.pop(d, None)
        return self


def find_ppv_slot(ins, icall, back=6):
    """QI 形态：lea R,[esp+K] ; push R ; push riid ; push this ; ... call。
    返回 K（相对该 lea 指令处的 esp）；找不到返回 None。"""
    for b in range(2, back + 1):
        p = ins[icall - b]
        if p[1] == 'lea' and '[esp + ' in p[2]:
            tgt = p[2].split(',', 1)[0].strip()
            k = num(p[2].rsplit(' + ', 1)[1].rstrip(']'))
            if k is None:
                return None
            # 该 lea 之后的 push 数（到 call 为止）用来把 K 折算到 call 时的 esp
            npush = sum(1 for j in range(icall - b + 1, icall) if ins[j][1] == 'push')
            pushed = [ins[j] for j in range(icall - b + 1, icall) if ins[j][1] == 'push']
            if not any(pp[2].strip() == tgt for pp in pushed):
                return None
            return k - 4 * npush
    return None
