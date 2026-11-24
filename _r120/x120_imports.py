import struct,json
P='ra2bench/gamemd.exe'
d=open(P,'rb').read()
IB=0x400000
SEC=[('text',0x1000,0x3df38d,0x1000,0x3e0000),
     ('rdata',0x3e1000,0x30074,0x3e1000,0x31000),
     ('data',0x412000,0x367be4,0x412000,0x6c000),
     ('rsrc',0x77a000,0x18128,0x47e000,0x19000),
     ('detour',0x793000,0x2718,0x497000,0x3000)]
def va2off(va):
    rva=va-IB
    for n,sv,vs,raw,rs in SEC:
        if sv<=rva<sv+vs:
            if rva-sv<rs: return raw+(rva-sv)
    return None
def sz(va,n): 
    o=va2off(va); return d[o:o+n]
imp_rva,imp_sz=0x7955c0,0x154
o=va2off(IB+imp_rva)
res={}
i=0
while True:
    ilt,ts,fc,name_rva,iat=struct.unpack_from('<IIIII',d,o+20*i)
    if name_rva==0 and iat==0: break
    name=sz(IB+name_rva,64).split(b'\0')[0].decode(errors='replace')
    entries=[]
    # use IAT to get slot VAs directly
    j=0
    if iat:
        while True:
            v=struct.unpack_from('<I',d,va2off(IB+iat)+4*j)[0]
            if v==0: break
            nm=None
            if not (v & 0x80000000):
                nm=sz(IB+v+2,64).split(b'\0')[0].decode(errors='replace')
            entries.append((IB+iat+4*j, v, nm))
            j+=1
    res[name]=entries
    i+=1
for k,v in res.items():
    print(k,len(v))
    for slot,val,nm in v:
        print('   slot=%08x val=%08x %s'%(slot,val,nm))
json.dump({k:[[s,v,n] for s,v,n in vv] for k,vv in res.items()},open('_r120/x120exec_imports.json','w'),indent=1)
