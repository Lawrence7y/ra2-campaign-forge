import struct,json,re
P='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
d=open(P,'rb').read()
TVA,TRAW,TVS,TRAW_SZ=0x1000,0x1000,0x3df38d,0x3e0000
text=d[TRAW:TRAW+TVS]
runs={}
for m in re.finditer(rb'\xcc+',text):
    n=m.end()-m.start()
    runs[n]=runs.get(n,0)+1
print('cc run length histogram (top):',sorted(runs.items())[:20])
tot=sum(runs.values()); print('total cc runs',tot)
print('runs >=1',tot,'runs>=2',sum(v for k,v in runs.items() if k>=2),'runs>=3',sum(v for k,v in runs.items() if k>=3))
# also 0x90 nop runs
runs2={}
for m in re.finditer(rb'\x90+',text):
    n=m.end()-m.start(); runs2[n]=runs2.get(n,0)+1
print('nop run hist',sorted(runs2.items())[:15])
# bytes at 0x7f7c80 and 0x7ed358
def rd(va,n=16):
    off=va-0x400000
    return d[off:off+n].hex()
print('0x7f7c80',rd(0x7f7c80),struct.unpack_from('<4I',d,0x3f7c80))
print('0x7ed358',rd(0x7ed358),struct.unpack_from('<4I',d,0x3ed358))
print('0x7f7c94',rd(0x7f7c94),struct.unpack_from('<4I',d,0x3f7c94))
