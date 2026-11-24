import pefile, struct, os
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21_C3\EVIDENCE\rtti_scan.txt'
pe=pefile.PE(EXE, fast_load=False)
blob=open(EXE,'rb').read()
ib=pe.OPTIONAL_HEADER.ImageBase
sections=[]
for s in pe.sections:
    name=s.Name.rstrip(b'\0').decode('ascii','replace')
    va=ib+s.VirtualAddress; size=s.Misc_VirtualSize or s.SizeOfRawData
    sections.append((name,va,size,s.SizeOfRawData))
def off(va): return pe.get_offset_from_rva(va-ib)
def rd(va,n):
    o=off(va); return blob[o:o+n]
def dword(va):
    b=rd(va,4)
    return struct.unpack('<I',b)[0] if len(b)==4 else None
def cstr(va,maxn=128):
    b=rd(va,maxn)
    z=b.find(b'\0')
    return b[:z if z>=0 else len(b)].decode('ascii','replace')
def in_text(va):
    return any(n=='.text' and a<=va<a+s for n,a,s,_ in sections)
def valid_col(col):
    if col is None or not (0x400000 <= col < 0x900000): return None
    td=dword(col+0xC)
    if td is None or not (0x400000 <= td < 0x900000): return None
    nm=cstr(td+8,96)
    if nm.startswith(('.?AV','.?AU')):
        return td,nm
    return None
TARGETS=['00539760','0053AB50','0053AF40','00595740','00599650','0053AD00','0053C280','0053B080','00595680','0068BCC0','005657A0','00477DB0','00477BE0','005AC900','005105A0']
EXTRA=['007E4DD8','007ED90C']
rs=[]
for hx in TARGETS+EXTRA:
    hxva=int(hx,16); needle=struct.pack('<I',hxva)
    occs=[]
    for name,sva,ssize,raw in sections:
        if name not in ('.rdata','.data'): continue
        data=rd(sva,ssize)
        start=0
        while True:
            i=data.find(needle,start)
            if i<0: break
            occs.append((name,sva+i,i))
            start=i+1
    found=[]
    for sec,ova,_ in occs:
        # try slot0 and earlier slots in a run of text pointers
        cands=[]
        vts=[ova]
        p=ova-4
        while len(vts)<80 and in_text(dword(p) or 0):
            vts.append(p); p-=4
        for vt in vts:
            col=dword(vt-4)
            vc=valid_col(col)
            if vc:
                found.append({'occurrence':f'{ova:08X}','vtable':f'{vt:08X}','slot':(ova-vt)//4,'col':f'{col:08X}','td':f'{vc[0]:08X}','name':vc[1],'section':sec})
                break
    rs.append({'target':hx,'occurrences':len(occs),'rtti':found[:6]})
os.makedirs(os.path.dirname(OUT),exist_ok=True)
open(OUT,'w',encoding='utf-8').write('\n'.join(f"{r['target']} occ={r['occurrences']} rtti={r['rtti']}" for r in rs)+'\n')
for r in rs:
    print(r['target'],'occ=',r['occurrences'])
    for f in r['rtti'][:3]: print('  ',f)
