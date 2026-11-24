import io,re,array,bisect
FULL=re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\t(.*)$')
WRAP=re.compile(r'^  ([0-9a-f]+):\t([0-9a-f ]+)\s*$')
starts=array.array('I'); LENS=array.array('B'); wraps=array.array('I'); wl=array.array('B')
for ln in io.open('/tmp/r93_disasm.txt',encoding='utf-8',errors='replace'):
    m=FULL.match(ln)
    if m:
        starts.append(int(m.group(1),16)); LENS.append(len(m.group(2).split())); continue
    w=WRAP.match(ln)
    if w:
        wraps.append(int(w.group(1),16)); wl.append(len(w.group(2).split()))
N=len(starts)
TL=array.array('B',LENS)
for a,n in zip(wraps,wl):
    j=bisect.bisect_left(starts,a)-1
    TL[j]+=n
print("N",N,"wraps",len(wraps),"sumLENS",sum(LENS),"sumTL",sum(TL),"maxTL",max(TL))
# contiguity
bad=[]
for i in range(N-1):
    if starts[i]+TL[i]!=starts[i+1]: bad.append(i)
print("TL contiguity violations",len(bad),"first",[ (hex(starts[i]),TL[i],hex(starts[i+1])) for i in bad[:5]])
badl=sum(1 for i in range(N-1) if starts[i]+LENS[i]!=starts[i+1])
print("LENS contiguity violations",badl)
print("first start",hex(starts[0]),"last start",hex(starts[-1]),"last end",hex(starts[-1]+TL[-1]))
print("span 401000..7e038d =",0x7e038d-0x401000,"sumTL-span",sum(TL)-(0x7e038d-0x401000))
over=[i for i in range(N) if starts[i]+TL[i]>0x7e038d]
print("insns ending beyond 0x7e038d:",len(over),[(hex(starts[i]),TL[i]) for i in over[:8]])
