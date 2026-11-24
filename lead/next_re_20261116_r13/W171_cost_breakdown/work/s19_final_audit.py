"""S19: independent re-verification of the LEAD_AUDIT claims using raw hex + capstone only
(no use of w171_lib helpers), so the audit does not depend on this card's abstractions.
"""
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
D = pe.__data__
SEC = [(IB + s.VirtualAddress, s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]


def off(va):
    for va0, pr, rs in SEC:
        if va0 <= va < va0 + rs:
            return pr + (va - va0)
    raise ValueError(hex(va))


def rb(va, n):
    return D[off(va):off(va) + n]


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

print('imagebase %08X' % IB)
print()
print('--- 1. Drive wrapper gates: opcode + resolved target ---')
for va in (0x4B0564, 0x4B056D, 0x4B0A79, 0x4B0647, 0x4B07AC):
    raw = rb(va, 6)
    ins = next(md.disasm(raw, va))
    tgt = ''
    if ins.mnemonic.startswith('j') and ins.op_str.startswith('0x'):
        tgt = '  -> ' + ins.op_str
    if ins.mnemonic == 'call':
        t = va + ins.size + struct.unpack('<i', raw[1:5])[0]
        tgt = '  -> %08X' % t
    print('  %08X  %-14s %-8s %s%s' % (va, raw.hex(), ins.mnemonic, ins.op_str, tgt))

print()
print('--- 2. FootClass::AI: throttle target vs locomotion dispatch address ---')
thr_raw = rb(0x4DA568, 6)
thr = next(md.disasm(thr_raw, 0x4DA568))
jne_tgt = int(thr.op_str, 16)
disp_raw = rb(0x4DA877, 3)
disp = next(md.disasm(disp_raw, 0x4DA877))
print('  0x4DA568  %-14s %s %s   (jump target %08X)' % (thr_raw.hex(), thr.mnemonic, thr.op_str, jne_tgt))
print('  0x4DA877  %-14s %s %s' % (disp_raw.hex(), disp.mnemonic, disp.op_str))
print('  dispatch(0x4DA877) > throttle-target(0x%08X)?  %s'
      % (jne_tgt, 0x4DA877 > jne_tgt))
print('  loaded loco pointer just before:')
for va in (0x4DA85C, 0x4DA86E, 0x4DA874, 0x4DA875):
    raw = rb(va, 7)
    ins = next(md.disasm(raw, va))
    print('    %08X  %-14s %s %s' % (va, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print()
print('--- 3. instruction counts, re-derived by walking from each entry (no atlas) ---')


def count(entry, limit=0x9000):
    seen = set()
    work = [entry]
    n = 0
    while work:
        a = work.pop()
        if a in seen or not (entry <= a < entry + limit):
            continue
        try:
            ins = next(md.disasm(rb(a, 15), a))
        except Exception:
            continue
        seen.add(a)
        n += 1
        mn = ins.mnemonic
        nxt = a + ins.size
        # NOTE: call targets are NOT followed (per-function body only).
        if mn == 'call':
            work.append(nxt)
        elif mn == 'jmp':
            if ins.operands and ins.op_str.startswith('0x'):
                work.append(int(ins.op_str, 16))
            # indirect jmp: stop this block (documented limitation)
        elif mn.startswith('j'):
            if ins.operands and ins.op_str.startswith('0x'):
                work.append(int(ins.op_str, 16))
            work.append(nxt)
        elif mn in ('ret', 'retf', 'hlt', 'iret'):
            continue
        else:
            work.append(nxt)
    return n


for va, nm in ((0x4B0500, 'Drive wrapper'), (0x4B2630, 'Drive::Process'),
               (0x4D3920, 'UpdatePathfinding'), (0x4CBBA0, 'CallFindPath'),
               (0x42C900, 'FindPath'), (0x429A90, 'A* container'),
               (0x4DA530, 'FootClass::AI')):
    print('  %08X %-22s %d' % (va, nm, count(va)))

print()
print('--- 4. A* loop latch / header / 0x2710 / 0xFFF7 ---')
for va, exp in ((0x42A3D8, 'jne 0x429D6D'), (0x429D6D, 'loop header'),
                (0x429D59, 'mov [esp+70],0xFFF7'), (0x42A3E2, 'cmp ecx,0x2710'),
                (0x429D57, 'jge (default only when <0)')):
    raw = rb(va, 8)
    ins = next(md.disasm(raw, va))
    print('  %08X  %-20s %-8s %-22s  # %s' % (va, raw.hex(), ins.mnemonic, ins.op_str, exp))

print()
print('--- 5. the throttled block: address span + count (start at the INSTRUCTION BOUNDARY) ---')
# 0x4DA568 is `jne` (6 bytes) -> the block starts at 0x4DA56E, NOT 0x4DA569.
a, b = 0x4DA56E, 0x4DA63B
n = 0
va = a
while va < b:
    ins = next(md.disasm(rb(va, 15), va))
    n += 1
    va += ins.size
print('  linear walk from 0x%08X (boundary) to 0x%08X -> %d instructions ; lands exactly on 0x%08X: %s'
      % (a, b, n, va, va == b))
print('  control: walk from the NON-boundary 0x4DA569 ->')
va = 0x4DA569
m = 0
while va < b and m < 5:
    ins = next(md.disasm(rb(va, 15), va))
    print('      %08X  %-22s %s %s' % (va, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    va += ins.size
    m += 1
print('  => 0x4DA569 is mid-instruction; any count started there is invalid (R12 discipline).')

print()
print('--- 6. slot 73 resolution for Unit/Infantry/Aircraft main tables ---')
for vt, nm in ((0x7F5C70, 'Unit'), (0x7EB058, 'Infantry'), (0x7E22A4, 'Aircraft')):
    v = struct.unpack('<I', rb(vt + 0x124, 4))[0]
    print('  %-9s vt=%08X  [+0x124] = %08X' % (nm, vt, v))
print('  Drive off4 vt 0x7E7EB0 [+0x40] = %08X' % struct.unpack('<I', rb(0x7E7EB0 + 0x40, 4))[0])

print()
print('--- 7. UpdatePathfinding: unique FindPath call site, and the [vptr+0x2CC] gate ---')
for va in (0x4D397F, 0x4D3985, 0x4D3987, 0x4D3989, 0x4D3E4B, 0x4D3EAC, 0x4D3E11):
    raw = rb(va, 8)
    ins = next(md.disasm(raw, va))
    print('  %08X  %-20s %-8s %s' % (va, raw.hex(), ins.mnemonic, ins.op_str))
