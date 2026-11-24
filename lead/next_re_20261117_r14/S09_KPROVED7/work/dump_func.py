"""Dump a specific address range and compact disasm for selected remaining candidates."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED7\work')
import s09lib as L
# dump 0x69de70
print('='*80)
print('0x69de70 disasm:')
o = L.va_off(0x69de70)
ins = list(L.MD.disasm(L.DATA[o:o+400], 0x69de70))
for i in ins[:60]:
    print('  %08X: %-10s %s' % (i.address, i.bytes.hex(), ('%s %s'%(i.mnemonic,i.op_str)).strip()))
