
import sys, json, re
import pefile
from capstone import *
p=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(p); img=pe.OPTIONAL_HEADER.ImageBase; raw=open(p,'rb').read()
def off(va): return pe.get_offset_from_rva(va-img)
# text section
text=None
for s in pe.sections:
    if s.Name.rstrip(b'\0')==b'.text': text=s
tva=img+text.VirtualAddress; tsz=text.SizeOfRawData
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True; md.detail=False
# scan for C7 05 [G],VT (vptr installs) with VT in candidate vtable set from K8 registry
# read candidate vt bases from argv[1] json
cfg=json.load(open(sys.argv[1],encoding='utf8'))
vts=set(int(x,16) for x in cfg['vts'])
entries=set(int(x,16) for x in cfg['entries'])
# build vt -> slot -> entry from K8 entry_vt_slots.tsv
vt_slot_entry={}
for line in open(cfg['map'],encoding='utf8'):
    m=re.match(r'([0-9A-F]{8}) ([0-9A-F]{8}) .* VT=([0-9A-F]{8}) SLOT=(\d+)',line.strip())
    if m:
        sa,ea,vt,sl=m.groups()
        if int(ea,16) in entries: vt_slot_entry[(int(vt,16),int(sl))]=int(ea,16)
# find globals G such that C7 05 <G>,<vt> and vt in vts
import struct
globals_vt={}
for i in range(tva,tva+tsz-10):
    if raw[off(i):off(i)+1]==b'\xC7' and raw[off(i)+1:off(i)+2]==b'\x05':
        G=struct.unpack_from('<I',raw,off(i)+2)[0]
        VT=struct.unpack_from('<I',raw,off(i)+6)[0]
        if VT in vts: globals_vt[G]=VT
# scan instructions for mov reg,[G] then call [reg+disp] within window, map to entry
res={ea:[] for ea in entries}
buf=raw[off(tva):off(tva)+tsz]
prev=[]
for ins in md.disasm(buf,tva):
    # check call [reg+disp]
    m=re.match(r'dword ptr \[(\w+) \+ (0x[0-9a-f]+)\]',ins.op_str)
    if m and ins.mnemonic=='call':
        reg,disp=m.group(1),int(m.group(2),16)
        vt=None;G=None
        for j,(r,g,v) in enumerate(reversed(prev[-12:])):
            if r==reg and g is not None:
                G=g; vt=v; break
        if vt and vt in vts:
            ea=vt_slot_entry.get((vt,disp//4))
            if ea in res:
                res[ea].append([ins.address, G])
    # track mov reg,[G]
    m2=re.match(r'mov (\w+), dword ptr \[(0x[0-9a-f]+)\]',ins.op_str)
    if ins.mnemonic=='mov' and m2:
        r,g=m2.group(1),int(m2.group(2),16)
        prev.append((r,g,globals_vt.get(g)))
    else:
        prev.append((None,None,None))
    if len(prev)>20: prev.pop(0)
print(json.dumps({f'{k:08X}':v for k,v in res.items()},indent=1))
