
import pefile,struct,json,sys
p=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(p); img=pe.OPTIONAL_HEADER.ImageBase; raw=open(p,'rb').read()
cfg=json.load(open(sys.argv[1],encoding='utf8'))
vts=set(int(x,16) for x in cfg['vts'])
print("vts:", [hex(v) for v in sorted(vts)])
text=[s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text'][0]
tva=img+text.VirtualAddress; tsz=text.SizeOfRawData
def off(va): return pe.get_offset_from_rva(va-img)
found={}
for i in range(tva,tva+tsz-10):
    o=off(i)
    if raw[o:o+2]==b'\xc7\x05':
        G=struct.unpack_from('<I',raw,o+2)[0]
        VT=struct.unpack_from('<I',raw,o+6)[0]
        if VT in vts: found[G]=VT
print("globals with vptr install:",len(found), [hex(g) for g in list(found)[:10]])
print("0x89c668 installed:",found.get(0x89C668) and hex(found[0x89C668]))
