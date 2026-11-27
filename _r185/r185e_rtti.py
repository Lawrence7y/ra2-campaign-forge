import struct,os,re
ROOT='/home/t628/projects/ra2-campaign-forge'; os.chdir(ROOT)
raw=open('ra2bench/gamemd.exe','rb').read()
def r2o(va):
    if 0x401000<=va<0x7E038D: return 0x1000-0x401000+va
    if 0x7E1000<=va<0x811074: return 0x3E1000-0x7E1000+va
    if 0x812000<=va<0x849BE4: return 0x412000-0x812000+va
    return None
def cstr(va,maxlen=200):
    o=r2o(va)
    if o is None: return None
    e=raw.find(b'\0',o,o+maxlen)
    return raw[o:e]
for vt in (0x7E1F50,0x7E1F34,0x7F5C70,0x7E22A4,0x7E4A28):
    o=r2o(vt)
    ds=[struct.unpack_from('<I',raw,o+4*i)[0] for i in range(60)]
    # find first non-text index
    k=next((i for i,v in enumerate(ds) if not (0x401000<=v<0x7E038D)), None)
    print(hex(vt),'first nontext idx',k,'ds[%s]='%k,hex(ds[k]) if k is not None else '-')
    # assume slot k is ptr to COL? check locator signature at that pointer
    p=ds[k]
    lo=r2o(p)
    if lo:
        sig=struct.unpack_from('<I',raw,lo)[0]
        print('   ptr target',hex(p),'sig',hex(sig))
    # scan backwards from vt for a plausible COL: signature 0 or 1 with pTypeDescriptor plausible
    lo2=r2o(vt)
    for back in range(0, 0x40, 4):
        cand=vt-back
        co=r2o(cand)
        if co is None: break
        sig,off,cd,ptd,pcd=struct.unpack_from('<5I',raw,co)
        if sig in (0,1) and 0x812000<=ptd<0x849BE4 and 0x7E1000<=pcd<0x811074:
            name=cstr(ptd+8)
            print('   COL?',hex(cand),'back',back,'sig',sig,'ptd',hex(ptd),'pcd',hex(pcd),'name',name)
