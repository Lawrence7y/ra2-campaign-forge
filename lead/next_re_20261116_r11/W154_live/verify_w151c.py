import struct, pefile, capstone
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase; data=pe.get_memory_mapped_image()
TGT=0x55B8F0
sec=[s for s in pe.sections if s.Name.startswith(b'.text')][0]
rva,off,size=sec.VirtualAddress,sec.PointerToRawData,sec.Misc_VirtualSize
code=data[off:off+size]; tva=base+rva
res={"e8":0,"e9":0,"eb":0,"0f8x":0}
found=[]
for i in range(len(code)-5):
    b=code[i]
    if b in (0xE8,0xE9):
        d=struct.unpack_from("<i",code,i+1)[0]
        if tva+i+5+d==TGT: found.append((tva+i,hex(b)))
    elif b==0xEB:
        d=struct.unpack_from("<b",code,i+1)[0]
        if tva+i+2+d==TGT: found.append((tva+i,"eb"))
    elif b==0x0F and 0x80<=code[i+1]<=0x8F:
        d=struct.unpack_from("<i",code,i+2)[0]
        if tva+i+6+d==TGT: found.append((tva+i,"0f8x"))
print("byte-level branch targets == 0x%X : %d"%(TGT,len(found)))
for a,k in found[:20]: print("   0x%X (%s)"%(a,k))
# is there a pointer to it anywhere (any section)?
pt=struct.pack("<I",TGT); n=0; pos=0
while True:
    pos=data.find(pt,pos)
    if pos<0: break
    n+=1; pos+=1
print("absolute dword 0x%X anywhere in image: %d"%(TGT,n))
# disassemble the region starting a bit before
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
st=0x55B840
sof=off+(st-base-rva)
print("\n=== linear disasm from 0x%X ==="%st)
for k,ins in enumerate(cs.disasm(code[sof:sof+0x140], st)):
    mark="  <<< TGT" if ins.address==TGT else ""
    print("  0x%X  %-20s %s %s%s"%(ins.address, ins.bytes.hex()[:20], ins.mnemonic, ins.op_str, mark))
    if k>44: break
