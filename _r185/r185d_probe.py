import struct,os,re
ROOT='/home/t628/projects/ra2-campaign-forge'; os.chdir(ROOT)
raw=open('ra2bench/gamemd.exe','rb').read()
def r2o(va):
    if 0x401000<=va<0x7E038D: return 0x1000-0x401000+va
    if 0x7E1000<=va<0x811074: return 0x3E1000-0x7E1000+va
    if 0x812000<=va<0x849BE4: return 0x412000-0x812000+va
    return None
T=(0x401000,0x7E038D); R=(0x7E1000,0x811074); D=(0x812000,0x849BE4)
def where(v):
    if T[0]<=v<T[1]: return 'text'
    if R[0]<=v<R[1]: return 'rdata'
    if D[0]<=v<D[1]: return 'data'
    return 'other'
# 1. full 28 slots of 0x7E1F50
for name,vt in [('AbstractClass',0x7E1F50),('AbstractTypeClass',0x7E1F34)]:
    o=r2o(vt); ds=[]
    for i in range(48):
        v=struct.unpack_from('<I',raw,o+4*i)[0]
        ds.append(v)
        if v==0: break
    print(name,hex(vt),'n=',len(ds))
    print('  ',[(i,hex(v),where(v)) for i,v in enumerate(ds) if where(v)!='text'])
# 2. pattern at rdata slot targets
for a in (0x7FB118,0x7FB160,0x7FAFC0,0x800540,0x802A90,0x802F20):
    o=r2o(a); ds=[struct.unpack_from('<I',raw,o+4*i)[0] for i in range(6)]
    print('rec',hex(a),[hex(x) for x in ds],'self-4?',hex(ds[4]) if ds[4]!=0 else '-')
# 3. terminator after 40 for 0x7f5c70
o=r2o(0x7f5c70)
ds=[struct.unpack_from('<I',raw,o+4*i)[0] for i in range(60)]
print('Unit 0x7f5c70 first nontext idx', next((i for i,v in enumerate(ds) if where(v)!='text'), None))
print(' sample 38..46',[(i,hex(ds[i]),where(ds[i])) for i in range(38,47)])
