import struct,pefile
from capstone import *
exe=r'D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe'
pe=pefile.PE(exe);base=pe.OPTIONAL_HEADER.ImageBase;d=pe.__data__
def off(va):return pe.get_offset_from_rva(va-base)
def u8(va):return d[off(va)]
def u32(va):return struct.unpack_from('<I',d,off(va))[0]
print('dropset cur 4..31:',[i+4 for i in range(28) if u8(0x41baec+i)==0])
print('outer table:',[hex(u32(0x41bae4+4*i)) for i in range(4)])
print('inner table at 0x41bb08:',[hex(u32(0x41bb08+4*i)) for i in range(2)])
print('inner idx cur 4..31:',[i+4 for i in range(28) if u8(0x41bb10+i)==0])
for a in [0x41bab2,0x41bad3,0x41bade]:
 print('\n',hex(a),d[off(a):off(a)+48].hex())
 cs=Cs(CS_ARCH_X86,CS_MODE_32);cs.skipdata=True
 for ins in cs.disasm(d[off(a):off(a)+48],a): print('  %08X %-20s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic+' '+ins.op_str))
