"""Score all candidates for ③b signals: jump table (scaled-index indirect jmp),
loop-with-write (backedge + explicit mem write in body), error sentinel, guard chain."""
import json
from pathlib import Path
import pefile, capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

ROOT = Path(r'D:\Project\ra2-campaign-forge')
raw = (ROOT/'ra2youli'/'gamemd.exe').read_bytes()
pe = pefile.PE(data=raw, fast_load=True); ib = pe.OPTIONAL_HEADER.ImageBase
secs = [dict(name=s.Name.rstrip(b'\0').decode('latin1'), va=ib+s.VirtualAddress,
             vs=s.Misc_VirtualSize, rs=s.SizeOfRawData, ptr=s.PointerToRawData) for s in pe.sections]
by = {s['name']:s for s in secs}
def va2off(va):
    for s in secs:
        if s['va'] <= va < s['va']+s['rs']:
            o=s['ptr']+va-s['va']
            if o+4<=len(raw): return o
    return None
def u32(va):
    o=va2off(va); return int.from_bytes(raw[o:o+4],'little') if o is not None else None
text=by['.text']; tva=text['va']; tlen=text['vs']; code=raw[text['ptr']:text['ptr']+tlen]
def in_text(v): return v is not None and tva<=v<tva+tlen
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
JCCS={'je','jne','jz','jnz','jg','jge','jl','jle','ja','jae','jb','jbe','js','jns','jo','jno','jp','jnp','jecxz','jcxz'}
sz=bytearray(tlen+16); kind=bytearray(tlen+16); tgt={}; insmap={}
RET=1;JMP=2;JCC=3;CALL=4
for ins in md.disasm(code,tva):
    o=ins.address-tva
    if o>=len(sz): break
    sz[o]=ins.size; insmap[o]=ins; mn=ins.mnemonic
    if mn=='ret' or mn.startswith('ret'): kind[o]=RET
    elif mn=='jmp':
        kind[o]=JMP
        if ins.operands and ins.operands[0].type==X86_OP_IMM: tgt[o]=int(ins.operands[0].imm)&0xffffffff
    elif mn in JCCS:
        kind[o]=JCC
        if ins.operands and ins.operands[0].type==X86_OP_IMM: tgt[o]=int(ins.operands[0].imm)&0xffffffff
    elif mn=='call': kind[o]=CALL

def extent(entry,cap=8000):
    seen=set(); stack=[entry]; addrs=[]; lo=hi=entry; n=0
    while stack:
        a=stack.pop()
        while True:
            if not in_text(a) or a in seen: break
            o=a-tva; s=sz[o]
            if s==0: break
            seen.add(a); addrs.append(a); n+=1
            if n>cap: stack=[]; break
            if a<lo: lo=a
            if a+s>hi: hi=a+s
            k=kind[o]
            if k==RET: break
            if k==JMP:
                t=tgt.get(o)
                if t: stack.append(t)
                break
            if k==JCC:
                t=tgt.get(o)
                if t: stack.append(t)
                a=a+s; continue
            a=a+s
    return lo,hi,sorted(addrs)

tri=json.load(open(ROOT/'lead/next_re_20261117_r14/S09_KPROVED6/work/triage.json'))
for rec in tri:
    e=rec['entry']; lo,hi,addrs=extent(e)
    rset=set(addrs)
    jt=[]; loops=[]; sentinel=[]; jcc_targets=[]; calls=[]; writes=[]
    for a in addrs:
        o=a-tva; ins=insmap.get(o)
        if ins is None: continue
        rel=a-e; mn=ins.mnemonic; ops=ins.operands
        # jump table: jmp with mem operand having a scaled index (index!=0 and scale in 2/4/8)
        if mn=='jmp' and ops and ops[0].type==X86_OP_MEM:
            m=ops[0].mem
            if m.index!=0 and m.scale in (2,4,8): jt.append((rel,'jmp[%s*%d%+d]'%(m.index,m.scale,m.disp)))
        # sentinel -1
        if mn in ('cmp','test') and ops and ops[0].type==X86_OP_IMM and int(ops[0].imm)&0xffffffff==0xffffffff: sentinel.append(rel)
        if mn=='cmp' and len(ops)>1 and ops[1].type==X86_OP_IMM and int(ops[1].imm)&0xffffffff==0xffffffff: sentinel.append(rel)
        # jcc targets distinct
        if mn in JCCS and ops and ops[0].type==X86_OP_IMM:
            t=int(ops[0].imm)&0xffffffff
            if t in rset: jcc_targets.append((rel,t-e))
        if mn=='call' and ops and ops[0].type==X86_OP_IMM: calls.append((rel,int(ops[0].imm)&0xffffffff))
        # explicit write to non-stack mem (disp>=0x8; global abs; [reg+disp])
        if ops and ops[0].type==X86_OP_MEM and (mn in ('mov','add','sub','inc','dec','and','or','xor','movzx','movsx') or mn.startswith('mov')):
            m=ops[0].mem
            base = m.base
            isstack = (base==capstone.x86.X86_REG_ESP or base==capstone.x86.X86_REG_EBP)
            if (not isstack) or (m.disp>=0x8):
                writes.append(rel)
        # backedge
        if o in tgt and kind[o] in (JMP,JCC):
            t=tgt[o]
            if lo<=t<=a: loops.append((rel,t-e))
    distinct_targets=len(set(t for r,t in jcc_targets))
    distinct_calls=len(set(c for r,c in calls))
    score = (4 if jt else 0)+(3 if loops else 0)+(2 if len(sentinel)>=1 else 0)+(1 if distinct_targets>=3 else 0)+(1 if len(writes)>=2 else 0)
    rec['_det']=dict(jt=jt,loops=loops,sentinel=sentinel,jcc_distinct=distinct_targets,
                     call_distinct=distinct_calls,writes=len(writes),size=hi-lo,nins=len(addrs),score=score)
json.dump(tri,open(ROOT/'lead/next_re_20261117_r14/S09_KPROVED6/work/triage2.json','w'),ensure_ascii=False,indent=1)
for r in sorted(tri,key=lambda x:-x['_det']['score']):
    d=r['_det']
    print('%s %-26s score=%d sz=%4d ins=%3d jt=%d loop=%d sen=%d jccT=%d call=%d W=%d | %s'%(
        r['k'],r['name'][:26],d['score'],d['size'],d['nins'],len(d['jt']),len(d['loops']),
        len(d['sentinel']),d['jcc_distinct'],d['call_distinct'],d['writes'],
        ('JT'+str(d['jt'][:2]) if d['jt'] else '')+(' L'+str(d['loops'][:2]) if d['loops'] else '')+(' S'+str(d['sentinel'][:3]) if d['sentinel'] else '')))
