import struct, pefile
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase; data=pe.get_memory_mapped_image()
sec=[s for s in pe.sections if s.Name.startswith(b'.text')][0]
rva,off,size=sec.VirtualAddress,sec.PointerToRawData,sec.Misc_VirtualSize
code=data[off:off+size]; tva=base+rva
# FF /2 mod=00 rm=reg  disp8=0x5C  => FF 50 5C (eax) .. FF 57 5C (edi)
pats={("eax",0x50),("ecx",0x51),("edx",0x52),("ebx",0x53),("esp",0x54),("ebp",0x55),("esi",0x56),("edi",0x57)}
hits=[]
for i in range(len(code)-3):
    if code[i]==0xFF and code[i+1] in {p[1] for p in pats} and code[i+2]==0x5C:
        hits.append(tva+i)
print("total `call [reg+0x5C]` (FF 5x 5C) in .text: %d"%len(hits))
near=[h for h in hits if 0x55A000<=h<=0x55C000]
print("of which inside 0x55A000..0x55C000: %d -> %s"%(len(near),[hex(h) for h in near]))
print("\nfirst 40 globally:"); print("  "+", ".join(hex(h) for h in hits[:40]))
