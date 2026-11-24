# R120 final: Q1..Q4. Self-written PE parse; chunked/linear-sweep facts from stageA2;
# boundary criteria compared against recursive-descent ground truth.
import struct, json, bisect, re, array as _ar, math
P='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r120/'
d=open(P,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]
nsec=struct.unpack_from('<H',d,e+6)[0]; optsz=struct.unpack_from('<H',d,e+20)[0]
IB=struct.unpack_from('<I',d,e+24+28)[0]
SOI=struct.unpack_from('<I',d,e+24+56)[0]
DIRS={}
for i in range(16):
    r,s=struct.unpack_from('<II',d,e+24+96+8*i); DIRS[i]=(r,s)
sec=e+24+optsz; SEC={}
for i in range(nsec):
    nm=d[sec+40*i:sec+40*i+8].rstrip(b'\0').decode('latin1')
    vs,va,rs,ra=struct.unpack_from('<IIII',d,sec+40*i+8)
    SEC[nm]=dict(va=va,vs=vs,raw=ra,rawsz=rs)
tv=SEC['.text']; text=d[tv['raw']:tv['raw']+tv['vs']]
base=IB+tv['va']; tend=base+len(text)

def ld(nm,ty): 
    a=_ar.array(ty); a.frombytes(open(OUT+nm+'.bin','rb').read()); return a
starts=ld('a2_starts','I'); kinds=ld('a2_kinds','B'); sizes=ld('a2_sizes','B')
pushes=ld('a2_pushes','I'); pushv=ld('a2_pushv','I')
calls=ld('a2_calls','I'); callk=ld('a2_callk','B'); callt=ld('a2_callt','I')
iatref=ld('a2_iatref','I'); iatslot=ld('a2_iatslot','I')
meta=json.load(open(OUT+'x120exec_sweep_meta.json'))
pushset={a:v for a,v in zip(pushes,pushv)}
startset=set(starts)
IATNAME={0x7e15f8:'OleLoadFromStream',0x7e15f4:'OleSaveToStream',0x7e15e4:'StgOpenStorage',
         0x7e15c8:'StgCreateDocfile',0x7e15fc:'CoCreateInstance',0x7e1600:'OleRun'}
IAT_LOAD=0x7e15f8; IAT_SAVE=0x7e15f4
iat_by_slot={}
for a,s in zip(iatref,iatslot): iat_by_slot.setdefault(s,[]).append(a)
for k in iat_by_slot: iat_by_slot[k].sort()

HEAD=dict(target_file=P,ImageBase=hex(IB),SizeOfImage=hex(SOI),
   sections={k:dict(va=hex(IB+v['va']),vs=hex(v['vs']),raw=hex(v['raw']),
                    rawsz=hex(v['rawsz']),file_backed_va_end=hex(IB+v['va']+min(v['vs'],v['rawsz']))) for k,v in SEC.items()},
   dirs={'import':[hex(v) for v in DIRS[1]],'resource':[hex(v) for v in DIRS[2]]},
   sweep=dict(insn_decoded=meta['n_insn'],chunk_bytes=65536,resync_points=meta['resync'],
              push_imm_insns=meta['n_push_imm'],call_insns=meta['n_calls'],
              iat_operand_refs=meta['n_iatref'],
              mode='capstone CS_MODE_32, disasm_lite, 64KB chunks, no detail=True, no full-text object retention'),
   rd=json.load(open(OUT+'rd2_meta.json')))

# ---------------- IID census ----------------
def guid_ok(b,drop_d2=False,d4=0x46000000,d3low=0x00C0):
    d1,d2,d3,d4_=struct.unpack('<4I',b)
    if d4_!=d4: return False
    if not drop_d2 and d2!=0: return False
    if d3low is not None and (d3&0xFFFF)!=d3low: return False
    return True
def scan(drop_d2=False,d4=0x46000000,d3low=0x00C0,sections=('.rdata','.data')):
    hits={}
    for nm in sections:
        s=SEC[nm]; blob=d[s['raw']:s['raw']+min(s['vs'],s['rawsz'])]
        for off in range(0,len(blob)-16,4):
            if guid_ok(blob[off:off+16],drop_d2,d4,d3low): hits[IB+s['va']+off]=nm
    return hits
iid=scan()
iid_addrs=sorted(iid)

# ---------------- boundary criteria ----------------
B1=[]  # after int3 padding (>=1 CC byte)
for i,a in enumerate(starts):
    o=a-base
    if o==0: continue
    if text[o-1]==0xCC: B1.append(a)
B1.sort()
B2=sorted({int(starts[i]) for i in range(1,len(starts)) if kinds[i-1] in (1,2)})
B3=sorted({int(callt[i]) for i in range(len(calls)) if callk[i]==3
           and base<=int(callt[i])<tend and int(callt[i]) in startset})
BALL=sorted(set(B1)|set(B2)|set(B3))   # union, used for minimal extents
rd_addr=ld('rd2_addr','I'); rd_tgt=ld('rd2_tgt','I'); rd_kind=ld('rd2_kind','B')
RDFN=sorted({int(t) for t,k in zip(rd_tgt,rd_kind) if k==3 and base<=int(t)<tend and int(t) in startset})
CRIT=dict(B1_after_int3_padding=B1,B2_after_ret_or_jmp=B2,B3_direct_call_target=B3,
          RD_direct_call_target=RDFN)
def nearest(arr,a):
    i=bisect.bisect_right(arr,a)-1
    return arr[i] if i>=0 else None
def nextb(arr,fs):
    i=bisect.bisect_right(arr,fs)
    return arr[i] if i<len(arr) else tend

# ---------------- helper: IID-push census per function ----------------
def iid_pushes():
    return [(a,v) for a,v in zip(pushes,pushv) if v in iid]
IP=iid_pushes()
def group(carr, extent_arr, items):
    g={}
    for a,v in items:
        fs=nearest(carr,a)
        if fs is None: fs=base
        g.setdefault(fs,[]).append((a,v))
    out=[]
    for fs,I in sorted(g.items()):
        fe=nextb(extent_arr,fs)
        i=bisect.bisect_left(starts,fs); j=bisect.bisect_left(starts,fe)
        vals=[pushset[int(starts[k])] for k in range(i,j) if int(starts[k]) in pushset]
        allv=sorted({v for v in vals if v in iid})
        out.append(dict(func_start=hex(fs),func_end_exclusive=hex(fe),
            site_count=len(I),sites=sorted({hex(a) for a,_ in I}),
            distinct_iids_all_in_extent=[hex(x) for x in allv],n_distinct=len(allv)))
    return out
def summarize(gs):
    return dict(funcs=len(gs),exactly1=sum(1 for x in gs if x['n_distinct']==1),
                ge2=sum(1 for x in gs if x['n_distinct']>=2),
                ge3=sum(1 for x in gs if x['n_distinct']>=3),
                zero=sum(1 for x in gs if x['n_distinct']==0))

# ---------------- Q1 ----------------
T1=0x7f7c80
raw1=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T1.to_bytes(4,'little')),text)]
sites1=[a for a in raw1 if a in pushset and pushset[a]==T1]
Q1=dict(target=hex(T1),
  raw_5byte_pattern_hits=len(raw1),
  decoded_push_imm_sites=len(sites1),
  sites=[hex(a) for a in sites1],
  rejected=[hex(a) for a in raw1 if a not in sites1],
  detection_method='search .text for bytes 68 + LE32(0x7f7c80); accept a hit only if its address is an instruction start produced by the 64KB-chunked capstone linear sweep AND capstone decodes that instruction as push with immediate exactly 0x7f7c80; instruction length must be 5 and the imm32 must occupy bytes 1..4 (i.e. it is the operand, not incidental data)',
  immediate_operand_check='bytes[1:5]==LE32(0x7f7c80) and decoded mnemonic==push and op_str==0x7f7c80',
  boundary_candidate_counts={k:len(v) for k,v in CRIT.items()},
  grouping=[], candidate_start_vectors=[])
amb=[]
for cname,arr in CRIT.items():
    g=group(arr,BALL,[(a,pushset[a]) for a in sites1])
    Q1['grouping'].append(dict(criterion=cname,n_functions=len(g),
        functions=[dict(f) for f in g],summary=summarize(g)))
for a in sites1:
    v={c:(hex(nearest(arr,a)) if nearest(arr,a) is not None else None) for c,arr in CRIT.items()}
    amb.append(dict(site=hex(a),candidates=v))
vecs=sorted({tuple(sorted(x['candidates'].items())) for x in amb})
Q1['candidate_start_vectors']=[dict(v) for v in vecs]
Q1['per_site_candidates']=amb
Q1['ambiguity_note']='a site yields different function starts depending on criterion; all vectors are listed in candidate_start_vectors, none was silently picked'
json.dump(dict(header=HEAD,q1=Q1),open(OUT+'x120exec_q1.json','w'),indent=1)
print('Q1 sites',len(sites1),'raw',len(raw1))
for g in Q1['grouping']: print(' ',g['criterion'],g['n_functions'],g['summary'])
print('IID census',len(iid),[hex(a) for a in iid_addrs])
