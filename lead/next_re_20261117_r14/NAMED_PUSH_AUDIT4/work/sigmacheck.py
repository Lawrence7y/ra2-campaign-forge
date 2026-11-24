"""Structural signature per row: does THIS row's own body contain every claimed element?"""
import sys, json, os, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA
img = Img()
W = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work"

def ins_at(a):
    l = img.dis(a, 15); return l[0] if l else None
def body(entry, limit=0x500):
    seen, work, visited = {}, [entry], set()
    while work:
        a = work.pop()
        while a not in visited and len(visited) < 3000:
            visited.add(a)
            i = ins_at(a)
            if not i: break
            seen[a] = i
            mn = i.mnemonic
            if mn.startswith('ret') or mn == 'hlt': break
            if mn == 'jmp':
                if i.op_str.startswith('0x'):
                    a = int(i.op_str, 16); continue
                break
            if mn.startswith('j') and i.op_str.startswith('0x'):
                work.append(int(i.op_str, 16))
            a = i.address + i.size
            if a - entry > limit: break
    return [seen[k] for k in sorted(seen)]

rows = ['006BF810','006BF990','006BFB10','006BFC90','006BFE10','006BFF90','006C0110',
        '006C0290','006C0410','006C0590','006C0710','006C0890','006C0A10','006C0B90',
        '006C0D10','006C0E90']
seqmask = {}
for r in rows:
    e = int(r, 16)
    b = body(e)
    txt = [i.mnemonic + ' ' + i.op_str for i in b]
    sig = dict(
        ppv_load=None, ppv_test=None, code_invalid=('mov', 'eax, 0x80070057'),
        zero_ppv=None, unk_test=None, code_noagg=('mov', 'eax, 0x80040110'),
        size_push=None, opnew=False, oom_test=None, obj_ctor=None,
        code_oom=('mov', 'eax, 0x8007000e'),
        vt_load=None, arg_push=0, qi_call=None, mov_edi=None, test_edi=None,
        jge=None, rel_vt=None, push1=None, rel_call=None, ret_edi=None, ret=None,
        n_qi_call=0, n_rel_call=0,
    )
    for n, i in enumerate(txt):
        if i.startswith('push') and sig['size_push'] is None and n < 6:
            sig['size_push'] = (b[n].address, i)
    has = {k: False for k in ('c1', 'c2', 'c3')}
    for i in b:
        if i.mnemonic == 'mov' and i.op_str == 'eax, 0x80070057': has['c1'] = True
        if i.mnemonic == 'mov' and i.op_str == 'eax, 0x80040110': has['c2'] = True
        if i.mnemonic == 'mov' and i.op_str == 'eax, 0x8007000e': has['c3'] = True
        if i.mnemonic == 'mov' and i.op_str == 'dword ptr [edi], 0': sig['zero_ppv'] = i.address
        if i.mnemonic == 'call' and i.op_str == 'dword ptr [eax]':
            sig['n_qi_call'] += 1; sig['qi_call'] = (i.address, i.bytes.hex(' '))
        if i.mnemonic == 'call' and i.op_str == 'dword ptr [edx + 0x20]':
            sig['n_rel_call'] += 1; sig['rel_call'] = (i.address, i.bytes.hex(' '))
        if i.mnemonic == 'push' and i.op_str == '1': sig['push1'] = i.address
        if i.mnemonic == 'mov' and i.op_str == 'eax, edi': sig['ret_edi'] = i.address
        if i.mnemonic == 'push' and i.op_str.startswith('0x') and i.op_str not in ('1',):
            v = int(i.op_str, 16)
            if v < 0x2000: sig['size_push'] = (i.address, i.op_str)
        if i.mnemonic == 'call' and i.op_str.startswith('0x') and i.op_str not in ('0x7c8e17',):
            sig['obj_ctor'] = (i.address, i.op_str)
        if i.mnemonic == 'call' and i.op_str == '0x7c8e17':
            sig['opnew'] = True
    s = ' '.join(txt)
    sig['body'] = s
    sig['codes'] = has
    sig['n_insn'] = len(b)
    sig['addr_list'] = [i.address for i in b]
    sig['ret_kind'] = [i.op_str for i in b if i.mnemonic.startswith('ret')]
    seqmask[r] = sig
    print("%s  insn=%-3d codes=%s qi=%d rel=%d zeroPpv=%s push1=%s retE di=%s rets=%s ctor=%s" % (
        r, sig['n_insn'], ''.join('1' if has[k] else '0' for k in ('c1','c2','c3')),
        sig['n_qi_call'], sig['n_rel_call'],
        '%08X' % sig['zero_ppv'] if sig['zero_ppv'] else 'None',
        '%08X' % sig['push1'] if sig['push1'] else 'None',
        '%08X' % sig['ret_edi'] if sig['ret_edi'] else 'None',
        sig['ret_kind'], sig['obj_ctor'][1] if sig['obj_ctor'] else None))

# --- are bodies identical modulo immediates? ---
base = None
print("\n--- template identity: masked-token comparison vs first row ---")
def masked(sig):
    out = []
    for a in sig['addr_list']:
        i = ins_at(a)
        op = re.sub(r'0x[0-9a-f]+', '#', i.op_str)
        out.append(i.mnemonic + ' ' + op)
    return out
base = masked(seqmask[rows[0]])
for r in rows[1:]:
    m = masked(seqmask[r])
    print("%s  identical_masked=%s  len %d vs %d" % (r, m == base, len(m), len(base)))
