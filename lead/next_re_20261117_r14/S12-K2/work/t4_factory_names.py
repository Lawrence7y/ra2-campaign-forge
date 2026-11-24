import sys,os,re,struct
sys.path.insert(0,os.path.dirname(__file__))
from re_helper import Bin,EVID
b=Bin();L=[]
pat=re.compile(rb'\.\?AV[A-Za-z0-9_]*Factory[A-Za-z0-9_]*@@')
found={}
for sec in b.sections:
    if sec['name']=='.text': continue
    buf=b.pe.__data__[sec['raw']:sec['raw']+sec['rawsize']]
    for m in pat.finditer(buf):
        nm=m.group().decode('ascii','replace'); td=sec['va']+m.start()-8
        found[(nm,td)]=True
L.append("RTTI names containing Factory: %d"%len(found))
for nm,td in sorted(found):
    tp=td.to_bytes(4,'little'); vts=[]
    for sec in b.sections:
        if sec['name']=='.text': continue
        buf=b.pe.__data__[sec['raw']:sec['raw']+sec['rawsize']]
        for m in re.finditer(re.escape(tp),buf):
            col=sec['va']+m.start()-0xC; cp=col.to_bytes(4,'little')
            for s3 in b.sections:
                if s3['name']=='.text': continue
                b3=b.pe.__data__[s3['raw']:s3['raw']+s3['rawsize']]
                for m3 in re.finditer(re.escape(cp),b3):
                    vt=s3['va']+m3.start()+4
                    try:
                        gs=b.u32(vt+0x30); code=b.read(gs,8)
                        if code[0]==0xB8 and code[5]==0xC3:
                            sz=struct.unpack('<I',code[1:5])[0]
                            vts.append((vt,col,gs,sz))
                    except: pass
    L.append("%s td=%08X vts=%s"%(nm,td," ".join("vt=%08X/gs=%08X/sz=0x%X"%(v[0],v[2],v[3]) for v in vts[:8])))
out=os.path.join(EVID,'t4_factory_names.txt')
open(out,'w',encoding='utf-8').write("\n".join(L)+"\n")
print("wrote",out,"lines",len(L))
