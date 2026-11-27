import struct,os
ROOT='/home/t628/projects/ra2-campaign-forge'; os.chdir(ROOT)
raw=open('ra2bench/gamemd.exe','rb').read()
def r2o(va):
    if 0x401000<=va<0x7E038D: return 0x1000-0x401000+va
    if 0x7E1000<=va<0x811074: return 0x3E1000-0x7E1000+va
    if 0x812000<=va<0x849BE4: return 0x412000-0x812000+va
    return None
for va in (0x8177E8,0x8177C8,0x816B50,0x822258,0x824550,0x8250F8):
    o=r2o(va)
    ds=[struct.unpack_from('<I',raw,o+4*i)[0] for i in range(6)]
    nm=raw[o+8:o+8+64].split(b'\0')[0]
    print(hex(va),[hex(x) for x in ds],'name8=',nm[:60])
# dump around 0x7fb150
o=r2o(0x7fb140)
print('0x7fb140..:',[hex(struct.unpack_from('<I',raw,o+4*i)[0]) for i in range(20)])
