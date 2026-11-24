# -*- coding: utf-8 -*-
import recore as R
print('TEXT_VA',hex(R.TEXT_VA),'TEXT_SIZE',hex(R.TEXT_SIZE),'end',hex(R.TEXT_VA+R.TEXT_SIZE))
for va in [0x7DD0F8,0x7C990E,0x7C9A31,0x7C8E17,0x7C978A,0x7BD130,0x4114B0,0x410260]:
    b=R.read_va(va,16)
    secs=[s.Name.rstrip(b'\x00').decode('latin1') for s in R._pe.sections if R.IB+s.VirtualAddress<=va<R.IB+s.VirtualAddress+s.Misc_VirtualSize]
    print('%08X' % va, 'in_text=',R.in_text(va), 'sec=', secs, 'bytes=',b.hex())
    ins=R.disasm(va,b)
    for i in ins[:4]: print('     ',i.mnemonic,i.op_str)
