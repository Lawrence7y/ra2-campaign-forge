"""Full VectorClass<PAUTileInsertType> method cluster + all field writes.

Question: at 0x0054A56E `mov [esi+4],0`, esi == ecx == this.
Does the path to 0x0054A56E write [esi+0xC] FIRST (0x0054A506 / 0x0054A526)?
If yes, a read-only .text `esi` is impossible at 0x0054A56E.
"""
import importlib.util, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)
md = pt.make_md()

LO, HI = 0x0054A000, 0x0054A900
ins = pt.disasm_range(pe, md, LO, HI)

# function starts: push ebp/mov ebp,esp  OR  code right after ret/nop-padding
starts = []
prev_ret = True
for i in ins:
    if prev_ret and i.mnemonic not in ('nop', 'db', 'int3'):
        starts.append(i.address)
        prev_ret = False
    if i.mnemonic.startswith('ret'):
        prev_ret = True

print('=== function entry candidates in [%08X,%08X) ===' % (LO, HI))
for s in starts:
    print('  %08X' % s)

print()
print('=== all writes to [esi/ecx/ebx/edi + disp] in cluster (field stores) ===')
for i in ins:
    op = i.op_str
    if i.mnemonic in ('mov', 'movzx', 'movsx', 'add', 'sub', 'and', 'or', 'inc', 'dec'):
        dst = op.split(',')[0].strip()
        if dst.startswith('dword ptr [') or dst.startswith('byte ptr [') or dst.startswith('word ptr ['):
            base = dst.split('[')[1].split(']')[0]
            if any(r in base for r in ('esi', 'ecx', 'edi', 'ebx', 'eax', 'edx')) and '+' in base:
                print('  %08X  %-22s %-8s %s' % (i.address, i.bytes.hex(), i.mnemonic, op))

print()
print('=== the critical window: does anything write [esi+0xc] before 0x0054A56E? ===')
path_ok = False
for i in ins:
    if 0x0054A4F0 <= i.address <= 0x0054A56E:
        if i.mnemonic == 'mov' and i.op_str.startswith('byte ptr [esi + 0xc]'):
            print('  %08X  %-22s %-8s %s   <-- WRITE to this+0xC (before the alleged fault)' % (
                i.address, i.bytes.hex(), i.mnemonic, i.op_str))
            path_ok = True
print('  => such a write exists before 0x0054A56E: %s' % path_ok)

print()
print('=== reads/derefs of [esi+4] before 0x0054A56E ===')
for i in ins:
    if 0x0054A4F0 <= i.address <= 0x0054A56E and '[esi + 4]' in i.op_str:
        print('  %08X  %-22s %-8s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))

print()
print('=== section write/exec permissions (from section chars) ===')
for s in pe.sections:
    ch = s['chars']
    print('  %-9s %08X..%08X  chars=%08X  R=%d W=%d X=%d' % (
        s['name'], s['va'], s['vend'], ch,
        bool(ch & 0x40000000), bool(ch & 0x80000000), bool(ch & 0x20000000)))
