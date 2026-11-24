import sys, struct
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S08_KPROVED2\_audit\scripts')
from peutil import PE
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
p = PE(EXE)
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True
ENTRY = 0x45A640

print('=== FULL BODY 0045A640 (0x45A640..0x45A690) ===')
for ins in md.disasm(p.read(ENTRY, 0x50), ENTRY):
    print('%08X (+%03X)  %-20s %-8s %s' % (ins.address, ins.address-ENTRY, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print()
print('=== RTTI chains for both holding tables ===')
for vt in (0x7E44F4, 0x7E4514):
    col = p.u32(vt-4)
    td = p.u32(col+0xC) if col else None
    name = p.cstr(td+8) if td else None
    print('vt=%08X  COL[vt-4]=%08X  TD[COL+0xC]=%08X  TD+8 name=%r' % (vt, col, td, name))
    for slot in range(0, 9):
        sva = vt + 4*slot
        val = p.u32(sva)
        sec = p.sec_of(val) if val else None
        print('   slot%d @%08X = %08X  [%s]' % (slot, sva, val, sec['name'] if sec else '?'))
    print()

print('=== Table boundary proof: value in .text vs .rdata ===')
for base in (0x7E44F4, 0x7E4514):
    print('table base %08X:' % base)
    for i in range(0, 10):
        va = base + 4*i
        v = p.u32(va)
        sec = p.sec_of(v) if v else None
        print('   [%08X]=%08X  %s' % (va, v, sec['name'] if sec else '?'))
