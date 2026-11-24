# Indirect-entry evidence: are the 7 Q3 site functions referenced as data pointers?
import struct,json,array as _ar,re
P='ra2bench/gamemd.exe'; d=open(P,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]; IB=0x400000
nsec=struct.unpack_from('<H',d,e+6)[0]; optsz=struct.unpack_from('<H',d,e+20)[0]
sec=e+24+optsz; SEC={}
for i in range(nsec):
    nm=d[sec+40*i:sec+40*i+8].rstrip(b'\0').decode('latin1')
    vs,va,rs,ra=struct.unpack_from('<IIII',d,sec+40*i+8); SEC[nm]=dict(va=va,vs=vs,raw=ra,rawsz=rs)
tv=SEC['.text']; text=d[tv['raw']:tv['raw']+tv['vs']]; base=IB+tv['va']; tend=base+len(text); TL=len(text)
def ld(n,t):
    a=_ar.array(t); a.frombytes(open('_r120/'+n+'.bin','rb').read()); return a
starts=ld('a2_starts','I'); kinds=ld('a2_kinds','B'); sizes=ld('a2_sizes','B')
SL=[int(x) for x in starts]
kd_at=bytearray(TL); sz_at=bytearray(TL)
for i,a in enumerate(SL):
    kd_at[a-base]=int(kinds[i]); sz_at[a-base]=int(sizes[i])
sites3=[0x4af7df,0x4b629f,0x4db560,0x54b7b8,0x69eeef,0x719d1b,0x75c6df]
# search all sections for dword pointers to candidate function starts
def find_ptrs(vals):
    out={}
    for nm in ('.rdata','.data','.text'):
        s=SEC[nm]; blob=d[s['raw']:s['raw']+min(s['vs'],s['rawsz'])]
        for v in vals:
            pat=v.to_bytes(4,'little')
            hits=[m.start() for m in re.finditer(re.escape(pat),blob)]
            for h in hits:
                out.setdefault(v,[]).append((nm,hex(IB+s['va']+h)))
    return out
# nearest B2 boundary before each site
B2=[int(starts[i]) for i in range(1,len(SL)) if kinds[i-1] in (1,2)]
import bisect
res=[]
for a in sites3:
    i=bisect.bisect_right(B2,a)-1
    fs=B2[i]
    # first real insn after padding nops
    cand=[]
    for k in range(0,8):
        x=fs+k
        if x in set(SL): cand.append(x)
    ptrs=find_ptrs([fs]+cand)
    res.append(dict(site=hex(a),nearest_B2=hex(fs),first_insn_candidates=[hex(x) for x in cand],
                    pointer_refs={hex(k):v for k,v in ptrs.items()}))
for r in res: print(r['site'],r['nearest_B2'],r['first_insn_candidates'],r['pointer_refs'])
json.dump(res,open('_r120/x120exec_ptr.json','w'),indent=1)
