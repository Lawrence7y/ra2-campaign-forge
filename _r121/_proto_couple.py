import sys, json, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r119')
from _pe119 import PE_, BUF
import capstone

T = PE_.sec_by_name('.text')
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = False
MD.skipdata = True
IAT = json.load(open('/home/t628/projects/ra2-campaign-forge/_r119/iat_names.json'))
IATV = {int(k, 16): v[1] for k, v in IAT.items()}

def sites(t):
    out = []
    for off in range(0, T['vsize'], 65536):
        blob = BUF[T['raw'] + off: T['raw'] + min(off + 65536, T['vsize'])]
        for (a, sz, mn, ops) in MD.disasm_lite(blob, T['va'] + off):
            if mn == 'push' and ops.startswith('0x'):
                try:
                    if int(ops, 16) == t: out.append(a)
                except ValueError: pass
    return out

def func_start(va, back=0x1000):
    """nearest preceding 0xCC run boundary"""
    lo = max(T['va'], va - back)
    o = PE_.va2off(lo)
    blob = BUF[o:PE_.va2off(va) + 1]
    # find last int3 run
    idx = blob.rfind(b'\xcc\xcc')
    if idx >= 0:
        return lo + idx + 2
    return lo

def trace_reg(va_site, reg):
    st = func_start(va_site)
    o = PE_.va2off(st)
    end = PE_.va2off(va_site)
    last = None
    for ins in MD.disasm(BUF[o:end], st):
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_REG and op.access & capstone.CS_AC_WRITE and ins.reg_name(op.reg) == reg:
                last = ins
    if last is None: return None
    ops = last.op_str
    if ops.startswith(reg + ', dword ptr [0x'):
        imm = int(ops[len(reg + ', dword ptr ['):-1], 16)
        return ('iat', imm, IATV.get(imm, '?'), hex(last.address))
    return ('write', 0, last.mnemonic + ' ' + ops, hex(last.address))

for target in (0x7f7c80, 0x7f7c90, 0x817bc0, 0x818858, 0x820270, 0x87da00):
    S = sites(target)
    cnt = collections.Counter()
    for s in S:
        o = PE_.va2off(s)
        seq = list(MD.disasm_lite(BUF[o:o + 64], s))
        callee = None
        for (a, sz, mn, ops) in seq[1:9]:
            if mn == 'call':
                if ops.startswith('dword ptr [0x'):
                    callee = ('IAT', IATV.get(int(ops[len('dword ptr ['):-1], 16), '?'), hex(a))
                elif ops.startswith('dword ptr ['):
                    inner = ops[len('dword ptr ['):-1]
                    reg = inner.split('+')[0].strip()
                    callee = ('IND', reg, hex(a))
                else:
                    callee = ('REL', ops, hex(a))
                break
        if callee is None:
            cnt['no-call'] += 1; continue
        if callee[0] == 'IAT':
            cnt['IAT:' + callee[1]] += 1
        elif callee[0] == 'REL':
            cnt['REL:' + callee[1]] += 1
        else:
            tr = trace_reg(s, callee[1])
            if tr is None: cnt['IND:%s<-UNRESOLVED' % callee[1]] += 1
            elif tr[0] == 'iat': cnt['IND:%s->IAT:%s' % (callee[1], tr[2])] += 1
            else: cnt['IND:%s->%s' % (callee[1], tr[2])] += 1
    print('===', hex(target), 'sites', len(S))
    for k, v in cnt.most_common(): print('   %-40s %d' % (k, v))
