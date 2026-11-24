
import pefile, capstone, json
EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pefile.PE(EXE, fast_load=True); IMAGE = pe.OPTIONAL_HEADER.ImageBase
for s in pe.sections:
    if s.Name.rstrip(b'\x00') == b'.text': text = s
TB = text.VirtualAddress + IMAGE; TS = text.Misc_VirtualSize
RAW = open(EXE,'rb').read(); tdata = RAW[text.PointerToRawData:text.PointerToRawData+text.SizeOfRawData]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=True; md.skipdata=True
boundary=set(); e8t=set(); off=0
while off < TS:
    ok=False
    for i in md.disasm(tdata[off:off+16], TB+off):
        boundary.add(i.address)
        if i.bytes[0]==0xE8:
            b = tdata[off:off+5]
            if len(b)==5:
                rel = int.from_bytes(b[1:5],'little',signed=True)
                e8t.add(i.address+5+rel)
        off += i.size; ok=True; break
    if not ok: off += 1
print('boundary', len(boundary), 'e8targets', len(e8t))
out = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\entries.json'
json.dump({'n_boundary':len(boundary),'n_e8':len(e8t),'e8':sorted(e8t)}, open(out,'w'))
