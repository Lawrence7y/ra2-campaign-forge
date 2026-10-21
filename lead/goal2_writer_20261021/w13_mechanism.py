"""Mechanism hunt: can a CODE address (vptr / virtual fn ptr) reach a +4 field?

Patterns that could put a vtable pointer (0x007Exxxx, in the task's ".text"
band 00401000-007EFFFF) into obj+4:

  P1  mov reg, [obj]            ; load vptr
      ... within N insns ...
      mov [X+4], reg            ; store vptr into a +4 field

  P2  mov reg, [obj+disp]       ; load a virtual fn pointer from a vtable slot
      mov [X+4], reg            ; store it into a +4 field

  P3  bulk copy: rep movs / memcpy whose destination is obj+4

Report every P1/P2 hit with the surrounding window so the shape can be judged.
"""
import importlib.util, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\goal2_writer_20261021'.replace(
    'goal2_writer_20261021', 'goal2_writer_20261021')
EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)
md = pt.make_md()

ins = pt.disasm_range(pe, md, pe.text_lo, 0x007E1000)
by_addr = {i.address: n for n, i in enumerate(ins)}


def is_store_to_plus4(op):
    if not op.startswith('dword ptr ['):
        return False
    return op.rstrip().endswith('+ 4]')


print('=== P1: load vptr from [reg] then store reg into a +4 field within 8 insns ===')
hits = 0
for n, i in enumerate(ins):
    if i.mnemonic != 'mov':
        continue
    p = i.op_str.split(',')
    if len(p) != 2:
        continue
    dst, src = p[0].strip(), p[1].strip()
    # `mov reg, dword ptr [reg2]`  (plain vptr load, disp 0)
    if not (dst.startswith(('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')) and src.startswith('dword ptr [')):
        continue
    if '+' in src or '*' in src:
        continue
    reg = dst
    for m in range(n + 1, min(n + 9, len(ins))):
        j = ins[m]
        if j.mnemonic != 'mov':
            continue
        q = j.op_str.split(',')
        if len(q) != 2:
            continue
        d2, s2 = q[0].strip(), q[1].strip()
        if is_store_to_plus4(d2) and s2 == reg:
            hits += 1
            print('  --- hit %d ---' % hits)
            for k in range(max(0, n - 2), min(n + 10, len(ins))):
                ins_k = ins[k]
                tag = ' <<<' if k in (n, m) else ''
                print('     %08X  %-22s %-8s %s%s' % (ins_k.address, ins_k.bytes.hex(), ins_k.mnemonic, ins_k.op_str, tag))
            print()
            break
print('  P1 hits: %d' % hits)

print()
print('=== P2: load from [reg2+disp] (vtable slot) then store into a +4 field ===')
hits2 = 0
for n, i in enumerate(ins):
    if i.mnemonic != 'mov':
        continue
    p = i.op_str.split(',')
    if len(p) != 2:
        continue
    dst, src = p[0].strip(), p[1].strip()
    if not (dst in ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp') and src.startswith('dword ptr [') and '+' in src):
        continue
    reg = dst
    for m in range(n + 1, min(n + 5, len(ins))):
        j = ins[m]
        if j.mnemonic != 'mov':
            continue
        q = j.op_str.split(',')
        if len(q) != 2:
            continue
        d2, s2 = q[0].strip(), q[1].strip()
        if is_store_to_plus4(d2) and s2 == reg:
            hits2 += 1
            if hits2 <= 15:
                print('  --- hit %d ---' % hits2)
                for k in range(max(0, n - 2), min(n + 6, len(ins))):
                    ins_k = ins[k]
                    tag = ' <<<' if k in (n, m) else ''
                    print('     %08X  %-22s %-8s %s%s' % (ins_k.address, ins_k.bytes.hex(), ins_k.mnemonic, ins_k.op_str, tag))
            break
print('  P2 hits: %d' % hits2)

print()
print('=== P3: every store to [REG + 4] whose SOURCE is a register (not imm) ===')
from collections import Counter
c = Counter()
for i in ins:
    if i.mnemonic != 'mov':
        continue
    p = i.op_str.split(',')
    if len(p) != 2:
        continue
    d2, s2 = p[0].strip(), p[1].strip()
    if is_store_to_plus4(d2) and not s2.startswith(('0x', 'byte', 'word', 'dword')):
        c[d2] += 1
print('  total: %d' % sum(c.values()))
for d, n in c.most_common(12):
    print('    %-24s %d' % (d, n))
