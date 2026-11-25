import struct
import pefile
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
TX=S['.text']; T_LO=TX.VirtualAddress+IB
raw=pe.get_data(TX.VirtualAddress,TX.Misc_VirtualSize)
for iid in (0x7e36c0,0x7e9b20):
    pat=b'\xbf'+struct.pack('<I',iid)
    st=0; hits=[]
    while True:
        k=raw.find(pat,st)
        if k<0: break
        hits.append(T_LO+k); st=k+1
    print(hex(iid),'bf-pattern hits:',[hex(x) for x in hits])
    # also check the actual bytes at 0x4292ab
print('bytes at 0x4292ab:', raw[0x4292ab-T_LO:0x4292ab-T_LO+8].hex())
print('bytes at 0x6cf44e:', raw[0x6cf44e-T_LO:0x6cf44e-T_LO+8].hex())
