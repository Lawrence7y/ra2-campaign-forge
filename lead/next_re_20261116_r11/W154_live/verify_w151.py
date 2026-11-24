import struct, subprocess, sys
# Lead's own check: is 0x55B8F0 reached? (a) Ghidra function table, (b) raw call/reference scan by capstone
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
import pefile, capstone
pe=pefile.PE(EXE, fast_load=True)
base=pe.OPTIONAL_HEADER.ImageBase
data=pe.get_memory_mapped_image()
def va2off(va):
    rva=va-base
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(rva-s.VirtualAddress)
    return None
TGT=0x55B8F0
print("=== A. raw reference scan for 0x55B8F0 ===")
tgt_le=struct.pack("<I",TGT)
hits=[]
i=0
while True:
    i=data.find(tgt_le,i)
    if i<0: break
    hits.append(i)
    i+=1
print("absolute little-endian dword occurrences of 0x%X: %d"%(TGT,len(hits)))
for h in hits[:10]:
    # map file offset -> va
    va=None
    for s in pe.sections:
        if s.PointerToRawData<=h<s.PointerToRawData+s.SizeOfRawData:
            va=base+ (h-s.PointerToRawData) + s.VirtualAddress
            print("   file off 0x%X -> VA 0x%X  (%s)"%(h,va,s.Name.decode().strip('\x00')))
print()
print("=== B. call/jmp displacement scan (E8/E9 rel32) ===")
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
text=None
for s in pe.sections:
    if s.Name.startswith(b'.text'):
        text=(s.VirtualAddress, s.PointerToRawData, s.Misc_VirtualSize)
print("text rva=0x%X off=0x%X size=0x%X"%text)
rva,off,size=text
code=data[off:off+size]
found=[]
for ins in cs.disasm(code, base+rva):
    if ins.mnemonic in ("call","jmp") and ins.op_str.startswith("0x"):
        try: t=int(ins.op_str,16)
        except: continue
        if t==TGT: found.append((ins.address,ins.mnemonic))
print("direct calls/jmps to 0x%X: %d"%(TGT,len(found)))
for a,m in found[:10]: print("   0x%X %s"%(a,m))
