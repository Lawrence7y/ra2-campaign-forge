# Channel B: INDEPENDENT raw PE byte-pattern scan (no capstone, no atlas)
# Pattern 1: 8B 15 <G>   ...  B9 <G>  ...  FF 52 <disp>   (mov edx,[G]; mov ecx,G; call [edx+disp])
# Pattern 2: B9 <G> ... 8B 15 <G> ... FF 52 <disp>
# also A1 <G> (mov eax,[G]) + FF 50 <disp>; 8B 0D <G> (mov ecx,[G]) variants
# Then: check that some C7 05 [G],<vt> writes a vtable whose slot[disp/4] is one of our 14 entries.
import sys,struct,re,json
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
ENTRIES={0x40b880:'slot2/F1',0x40b930:'slot4/F1',0x40f7c0:'slot2/F2',0x40fd90:'slot2/F3',0x40fe40:'slot4/F3',0x46b7e0:'slot2/F4',0x46b890:'slot4/F4',0x62b250:'slot2/F5',0x62b300:'slot4/F5',0x65c0d0:'slot2/F6',0x65c180:'slot4/F6',0x48ad60:'slot6/F7',0x54e8e0:'slot6/F8',0x48ad70:'slot1/F7'}
T0,T1=text_range()
# raw .text bytes
o=va2off(T0); text=DATA[o:o+(T1-T0)]
def va(off): return T0+off
# collect all C7 05 writes: global -> set of vt
GVT={}
for m in re.finditer(b'\xc7\x05',text):
    p=m.start()
    if p+10>len(text):continue
    g,vt=struct.unpack_from('<II',text,p+2)
    if 0x7e1000<=vt<0x810000:
        GVT.setdefault(g,set()).add(vt)
# vtable slot -> entry of interest
def slot_entry(vt,slotb):
    e=u32(vt+slotb)
    return e if e in ENTRIES else None

# Byte-pattern scan: for each global G in GVT, find B9 <G> (mov ecx,G) and 8B 15 <G>(mov edx,[G]) / A1<G> / 8B0D<G>
res=[]
for G,vts in GVT.items():
    gp=struct.pack('<I',G)
    for mseq,regcall in [(b'\x8b\x15'+gp,'edx/FF52'),(b'\xa1'+gp,'eax/FF50'),(b'\x8b\x0d'+gp,'ecx/FF51')]:
        for m in re.finditer(re.escape(mseq),text):
            p=m.start(); loadva=va(p)
            # find call [reg+disp] within next 24 bytes
            chunk=text[p:p+24]
            if regcall=='edx/FF52': callpat=b'\xff\x52'
            elif regcall=='eax/FF50': callpat=b'\xff\x50'
            else: callpat=b'\xff\x51'
            for cm in re.finditer(re.escape(callpat),chunk):
                disp=chunk[cm.start()+2]
                cs=va(p+cm.start())
                # find 'mov ecx,G' (B9 gp) within 16 bytes before or after load
                near=text[max(0,p-16):min(len(text),p+24)]
                ecxpat=b'\xb9'+gp
                if ecxpat not in near and b'\x8d\x0d'+gp not in near:  # lea ecx,[G]
                    continue
                for vt in vts:
                    e=slot_entry(vt,disp)
                    if e:
                        d=dict(entry=hex(e),name=ENTRIES[e],call_site=hex(cs),disp=disp,slot=disp//4,g=hex(G),vt=hex(vt),load=hex(loadva),pattern=regcall)
                        res.append(d)
# dedupe
un={}
for r in res: un[(r['entry'],r['call_site'],r['g'],r['vt'])]=r
res=list(un.values())
res.sort(key=lambda x:(x['entry'],x['call_site']))
print('Channel B raw-byte exact hits:',len(res))
for r in res: print(r)
json.dump(res,open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\EVIDENCE\channelB_raw_byte.json','w'),indent=1)
