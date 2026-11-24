import sys,struct,json,collections,array
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
TL,TH=0x401000,0x7e1000
# load instruction-start set
raw=open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_insn.bin','rb').read()
n=len(raw)//5
STARTS=array.array('I'); STARTS.frombytes(raw[:4*n]); SIZES=array.array('B'); SIZES.frombytes(raw[4*n:])
START_SET=set(STARTS)
print('starts',len(STARTS),'set',len(START_SET))

def va_of(fo):
    for s in SECS:
        if s['raw']<=fo<s['raw']+s['rsize']: return fo+s['rdelta']
    return None
def textfo(va):
    o=foff(va)
    return o

# --- dispatch: jmp dword ptr [reg*4 + disp32] = FF 24 <modrm> disp32, modrm reg=4 ---
disp_hits=[]
tlo,tlen=textfo(TL),TH-TL
seg=_img[tlo:tlo+tlen]
i=0
while True:
    i=seg.find(b'\xff\x24',i)
    if i<0: break
    modrm=seg[i+2]
    # mod=00, rm=100 (SIB) -> (modrm & 0xC7)==0x04 ; reg field /4 = (modrm>>3)&7 ==4
    if (modrm & 0xC7)==0x04 and ((modrm>>3)&7)==4:
        if i+7<=tlen:
            sib=seg[i+3]; disp=struct.unpack('<I',seg[i+4:i+8])[0]
            scale=1<<(sib>>6); idx=(sib>>3)&7; base=sib&7
            va=TL+i
            disp_hits.append(dict(va=va,bytes=seg[i:i+8].hex(),idx=idx,scale=scale,base=base,table=disp,instr_start=(va in START_SET)))
    i+=1
print('raw FF24 pattern hits',len(disp_hits),'at instr starts',sum(1 for d in disp_hits if d['instr_start']))
# --- assembler: mov dword ptr [mem], imm32 ---
asm_hits=[]
i=0
while True:
    i=seg.find(b'\xc7',i)
    if i<0: break
    modrm=seg[i+1]
    mod=(modrm>>6)&3; reg=(modrm>>3)&7; rm=modrm&7
    if reg==0:
        length=None; mem=None; disp=None; base=None; idx=None; scale=None
        if mod==0 and rm==5:
            length=10; disp=struct.unpack('<I',seg[i+2:i+6])[0]
        elif mod==0 and rm==4:
            sib=seg[i+2]; scale=1<<(sib>>6); idx=(sib>>3)&7; b=sib&7
            if b==5: length=11; disp=struct.unpack('<I',seg[i+3:i+7])[0]
            else: length=10; disp=0; base=b
            if idx==4: idx=None
        elif mod==1:
            length=7; disp=struct.unpack('<b',seg[i+2:i+3])[0]
            if rm==4: length=8
        elif mod==2:
            length=10; disp=struct.unpack('<I',seg[i+2:i+6])[0]
            if rm==4: length=11
        elif mod==0:
            length=6
        elif mod==3: length=None
        if length and i+length<=tlen:
            imm_off=i+length-4
            imm=struct.unpack('<I',seg[imm_off:imm_off+4])[0]
            va=TL+i
            asm_hits.append(dict(va=va,disp=disp,imm=imm,bytes=seg[i:i+length].hex(),
                                 instr_start=(va in START_SET),modrm=modrm))
    i+=1
print('raw C7 hits',len(asm_hits),'at starts',sum(1 for a in asm_hits if a['instr_start']))
json.dump(dict(disp=disp_hits,asm=asm_hits),open('/home/t628/projects/ra2-campaign-forge/_r109/_exec/_bytes.json','w'))
