import sys,struct,json,collections,array
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img
TL,TH=0x401000,0x7e1000
raw=open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_insn.bin','rb').read()
n=len(raw)//5
STARTS=array.array('I'); STARTS.frombytes(raw[:4*n])
SIZES=array.array('B'); SIZES.frombytes(raw[4*n:])
SZ=dict(zip(STARTS,SIZES))
SET=set(STARTS)
tlo=foff(TL); tlen=TH-TL; seg=_img[tlo:tlo+tlen]

disp=[]
i=0
while True:
    i=seg.find(b'\xff',i)
    if i<0: break
    if i+6>tlen: break
    modrm=seg[i+1]
    if modrm==0x24:   # FF /4, mod=00 rm=100 -> SIB
        sib=seg[i+2]
        if (sib>>3)&7!=4 and i+7<=tlen:  # index !=esp
            table=struct.unpack('<I',seg[i+3:i+7])[0]
            va=TL+i
            if va in SET and SIZES[STARTS.index(va) if False else 0] if False else True:
                if va in SET:
                    disp.append(dict(va=va,table=table,scale=1<<(sib>>6),idx=(sib>>3)&7,
                                     bytes=seg[i:i+7].hex()))
    elif modrm==0x64 and i+8<=tlen:  # FF /4 mod=01 rm=100
        sib=seg[i+2]; d8=seg[i+3]
        if (sib>>3)&7!=4:
            table=struct.unpack('<I',seg[i+4:i+8])[0]
            va=TL+i
            if va in SET:
                disp.append(dict(va=va,table=table,scale=1<<(sib>>6),idx=(sib>>3)&7,
                                 disp8=d8,bytes=seg[i:i+8].hex()))
    elif modrm==0xa4 and i+11<=tlen: # FF /4 mod=10 rm=100
        sib=seg[i+2]
        if (sib>>3)&7!=4:
            table=struct.unpack('<I',seg[i+3:i+7])[0]
            va=TL+i
            if va in SET:
                disp.append(dict(va=va,table=table,scale=1<<(sib>>6),idx=(sib>>3)&7,bytes=seg[i:i+11].hex()))
    i+=1
print('dispatch sites:',len(disp),'distinct tables:',len({d['table'] for d in disp}))
json.dump(disp,open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_dispatch.json','w'))
for d in disp[:6]: print(hex(d['va']),hex(d['table']),d['bytes'])
