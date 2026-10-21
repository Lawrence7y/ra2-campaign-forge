"""Two decisive checks.

A) Are there any xrefs (call/jmp/jcc) INTO the body of 0x0054A4F0..0x0054A58E
   (i.e. a path that reaches 0x0054A56E while skipping the [esi+0xC] writes
   at 0x0054A506 / 0x0054A526)?

B) Who can write a .text/.rdata address into [obj+4]?  Two shapes:
   B1) vptr stores `mov dword [reg+disp], <vtable VA>`  with disp != 0
   B2) `mov [reg], <vtable VA>` where reg itself is obj+4
"""
import importlib.util, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)
md = pt.make_md()

FN_LO, FN_HI = 0x0054A4F0, 0x0054A58E

print('=== A) raw E8/E9/0F8x rel32 targets landing inside [%08X,%08X) ===' % (FN_LO, FN_HI))
text_lo, text_hi = pe.text_lo, pe.text_hi
hits = []
# scan whole .text for rel32 branches; decode with capstone to get true branch insns
ins = pt.disasm_range(pe, md, text_lo, min(text_hi, 0x007E1000))
for i in ins:
    m = i.mnemonic
    if not (m.startswith('j') or m in ('call', 'loop', 'loope', 'loopne')):
        continue
    op = i.op_str.strip()
    if not op.startswith('0x'):
        continue
    try:
        tgt = int(op, 16)
    except ValueError:
        continue
    if FN_LO <= tgt < FN_HI:
        hits.append((i.address, m, tgt))
print('  branch instructions targeting the function body: %d' % len(hits))
for a, m, t in hits:
    kind = 'ENTRY' if t == FN_LO else 'INTO-MIDDLE'
    print('    %08X %-8s -> %08X   %s' % (a, m, t, kind))

print()
print('=== A2) internal control flow of the function (jcc/jmp targets) ===')
for i in ins:
    pass
body = pt.disasm_range(pe, md, FN_LO, FN_HI)
tg = set()
for i in body:
    m = i.mnemonic
    if m.startswith('j') or m == 'call':
        op = i.op_str.strip()
        if op.startswith('0x'):
            tg.add(int(op, 16))
for t in sorted(tg):
    print('    target %08X  %s' % (t, 'IN BODY' if FN_LO <= t < FN_HI else 'outside'))

print()
print('=== A3) any store to esi between 0x0054A4FA and 0x0054A56E? ===')
for i in body:
    if 0x0054A4FA <= i.address <= 0x0054A56E:
        if i.mnemonic == 'mov' and i.op_str.split(',')[0].strip() == 'esi':
            print('    %08X %s' % (i.address, i.op_str))
        if i.mnemonic in ('pop', 'xchg') and 'esi' in i.op_str:
            print('    %08X %s %s' % (i.address, i.mnemonic, i.op_str))
print('    (none printed => esi is never reloaded before the faulting store)')

print()
print('=== B1) vptr-style stores `mov dword ptr [reg+disp], <code/rdata VA>` ===')
cnt = 0
for i in ins:
    if i.mnemonic != 'mov':
        continue
    parts = i.op_str.split(',')
    if len(parts) != 2:
        continue
    dst, src = parts[0].strip(), parts[1].strip()
    if not (dst.startswith('dword ptr [') and src.startswith('0x')):
        continue
    try:
        val = int(src, 16)
    except ValueError:
        continue
    if not (pe.is_text(val) or 0x007E1000 <= val < 0x00812000):
        continue
    # only stores of code/vtable addresses -- these are vptr or fnptr stores
    disp = None
    if '[' in dst and '+' in dst:
        try:
            disp = int(dst.split('+')[1].split(']')[0].strip(), 16)
        except ValueError:
            disp = None
    if disp is not None and disp != 0:
        cnt += 1
        if cnt <= 40:
            print('    %08X  %-26s -> [%s+0x%X] = %08X (%s)' % (
                i.address, i.op_str, dst.split('[')[1].split('+')[0], disp, val,
                'text' if pe.is_text(val) else 'rdata'))
print('    total non-zero-offset vptr/fnptr stores: %d' % cnt)

print()
print('=== B2) does anything store a vtable VA at exactly +4 ? ===')
for i in ins:
    if i.mnemonic != 'mov':
        continue
    parts = i.op_str.split(',')
    if len(parts) != 2:
        continue
    dst, src = parts[0].strip(), parts[1].strip()
    if dst in ('dword ptr [eax + 4]', 'dword ptr [ecx + 4]', 'dword ptr [edx + 4]',
               'dword ptr [esi + 4]', 'dword ptr [edi + 4]', 'dword ptr [ebx + 4]'):
        try:
            val = int(src, 16)
        except ValueError:
            continue
        if pe.is_text(val) or 0x007E1000 <= val < 0x00812000:
            print('    %08X  %-30s = %08X' % (i.address, dst, val))
