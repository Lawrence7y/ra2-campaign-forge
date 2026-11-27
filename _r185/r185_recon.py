import struct,re,sys
EXE='ra2bench/gamemd.exe'
raw=open(EXE,'rb').read()
pe=struct.unpack_from('<I',raw,0x3c)[0]
nsec=struct.unpack_from('<H',raw,pe+6)[0]; optsz=struct.unpack_from('<H',raw,pe+20)[0]
opt=pe+24; IB=struct.unpack_from('<I',raw,opt+28)[0]
secs=[]
for i in range(nsec):
    o=opt+optsz+40*i
    nm=raw[o:o+8].rstrip(b'\0').decode('latin1')
    vs,va,rs,ra=struct.unpack_from('<IIII',raw,o+8)
    secs.append((nm,va,vs,ra,rs))
print('sections',[(s[0],hex(IB+s[1]),s[4]) for s in secs])
def r2o(va):
    rva=va-IB
    for nm,v,vs,ra,rs in secs:
        if v<=rva<v+rs: return ra+(rva-v)
    return None
VT=0x7E1F50
o=r2o(VT); print('file off of vt',hex(o) if o else None)
if o:
    d=struct.unpack_from('<20I',raw,o)
    print('20 dwords:',[hex(x) for x in d])
    # how many dwords until 0
    n=0
    while True:
        v=struct.unpack_from('<I',raw,o+4*n)[0]
        if v==0: break
        n+=1
    print('nonzero run len',n,'next dword',hex(struct.unpack_from('<I',raw,o+4*n)[0]))
# install site byte pattern mov dword ptr [reg], 0x7E1F50 : c7 06/07/00/01/02/03/05 50 1f 7e 00
pat=re.compile(rb'\xc7[\x00-\x07]\x50\x1f\x7e\x00')
hits=[m.start() for m in pat.finditer(raw)]
print('mov [reg],0x7E1F50 raw byte hits',len(hits),[hex(h) for h in hits[:10]])
# call [reg+0x48]
pat2=re.compile(rb'\xff[\x50-\x57]\x48')
print('call [reg+0x48] hits',len(pat2.findall(raw)))
