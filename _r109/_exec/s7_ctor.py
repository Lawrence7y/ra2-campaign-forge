import sys,struct,json,collections,array
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img
TL,TH=0x401000,0x7e1000
raw=open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_insn.bin','rb').read()
n=len(raw)//5
STARTS=array.array('I'); STARTS.frombytes(raw[:4*n]); SIZES=array.array('B'); SIZES.frombytes(raw[4*n:])
SET=set(STARTS)
R=json.load(open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_vt_raw.json'))
VT={int(k,16):v for k,v in R['vtables'].items()}
tlo=foff(TL); tlen=TH-TL; seg=_img[tlo:tlo+tlen]

# mov dword ptr [mem], imm32 => C7 /0
hits=[]
i=0
while True:
    i=seg.find(b'\xc7',i)
    if i<0: break
    if i+6>tlen: break
    modrm=seg[i+1]
    if ((modrm>>3)&7)!=0: i+=1; continue
    mod=(modrm>>6)&3; rm=modrm&7
    length=None; disp=None; based=None; idx=None; scale=None
    if mod==0 and rm==5:
        length=10; disp=struct.unpack('<I',seg[i+2:i+6])[0]
    elif mod==0 and rm==4:
        if i+11>tlen: i+=1; continue
        sib=seg[i+2]; scale=1<<(sib>>6); idx=(sib>>3)&7; b=sib&7
        if b==5: length=11; disp=struct.unpack('<I',seg[i+3:i+7])[0]
        else: length=10; disp=0; based=b
        if idx==4: idx=None
    elif mod==0 and rm!=4:
        length=6; disp=0; based=rm
    elif mod==1:
        length=7 if rm!=4 else 8; disp=struct.unpack('<b',seg[i+2:i+3])[0]
        if rm!=4: based=rm
        else:
            sib=seg[i+2]; idx=(sib>>3)&7; scale=1<<(sib>>6); b=sib&7
            if idx==4: idx=None
            based=b if b!=5 else None
    elif mod==2:
        length=10 if rm!=4 else 11; disp=struct.unpack('<I',seg[i+2:i+6])[0]
        if rm!=4: based=rm
        else:
            sib=seg[i+2]; idx=(sib>>3)&7; scale=1<<(sib>>6); b=sib&7
            if idx==4: idx=None
            based=b if b!=5 else None
    if length is None or i+length>tlen: i+=1; continue
    va=TL+i
    if va not in SET: i+=1; continue
    imm=struct.unpack('<I',seg[i+length-4:i+length])[0]
    if imm in VT:
        hits.append(dict(va=va,disp=disp,imm=imm,bytes=seg[i:i+length].hex(),
                         vt_cls=VT[imm]['cls'],vt_offset=VT[imm]['offset']))
    i+=1
print('assembler sites (imm in vtable set):',len(hits))
print('distinct imm vtables:',len({h['imm'] for h in hits}))
print('distinct classes:',len({h['vt_cls'] for h in hits}))
print('disp==0:',sum(1 for h in hits if h['disp']==0))
json.dump(dict(sites=hits,vtables={hex(k):v for k,v in VT.items()}),
          open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_ctor.json','w'))
for h in hits[:8]: print(hex(h['va']),'disp',h['disp'],hex(h['imm']),h['vt_cls'],h['bytes'])
