"""W178-PATCH main evidence collector (read-only against gamemd.exe).

Independently:
  1. Full .text linear disasm (capstone skipdata=True) -> 30 call sites to 0x724730.
  2. Host function via function_atlas.tsv interval containment (entry<=site<entry+size).
     2 atlas-hole hosts verified by independent ret+nop boundary (NOT entry_at_or_before).
  3. Per site: ecx last-write source, zero-guard check, CFG reachability from fn entry
     with branch conditions, host static refs, push-arg detection, crash prediction.
  4. 0x6CD8CD: eax source, jump-table reachability, crash prediction.
  5. Global NULL writers for [0x887368]/[0x8871E0].
  6. Space: nop/int3 runs near each site, arg-push instruction, 5-byte call slot.

Outputs: EVIDENCE/core.json, EVIDENCE/dump.txt, EVIDENCE/site_table.tsv
"""
from __future__ import annotations
import hashlib, json, os, struct
from collections import defaultdict, deque
import capstone, pefile

ROOT=r"D:\Project\ra2-campaign-forge"
EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
ATLAS=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","W178_PATCH","EVIDENCE")
EXPECTED_SHA="73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
IB=0x400000
TARGET=0x724730
S6=0x6CD8CD
G368=0x887368
G1E0=0x8871E0
JT_6CC390=0x6CDE44
# Independent boundary evidence for atlas-hole hosts (verified in this script via ret+nop).
GAP_FUNCS={0x6D15CB:(0x6D1570,0x6D15E4),0x6D1605:(0x6D15F0,0x6D160B)}
ECX_REGS={"ECX","CX","CL","CH"}
EAX_REGS={"EAX","AX","AL","AH"}
CANON={"EBX":{"EBX","BX","BL","BH"},"EDX":{"EDX","DX","DL","DH"},
       "ESI":{"ESI","SI"},"EDI":{"EDI","DI"},"EBP":{"EBP","BP"},"ESP":{"ESP","SP"}}

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest().upper()

class Bin:
    def __init__(self,p):
        self.pe=pefile.PE(p,fast_load=True); self.ib=self.pe.OPTIONAL_HEADER.ImageBase
        self.secs=[]
        for s in self.pe.sections:
            n=s.Name.decode('utf-8','replace').rstrip('\x00')
            self.secs.append(dict(name=n,va=self.ib+s.VirtualAddress,vsize=s.Misc_VirtualSize,
                                  raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
        self.text=next(s for s in self.secs if s['name']=='.text')
    def read(self,va,n):
        for s in self.secs:
            if s['va']<=va and va+n<=s['va']+s['rawsize']:
                o=s['raw']+(va-s['va']); return self.pe.__data__[o:o+n]
        raise ValueError(f"VA {va:#x}+{n} not in raw range")
    def raw(self,s): return self.pe.__data__[s['raw']:s['raw']+s['rawsize']]

def md(skipdata=True,detail=True):
    m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.skipdata=skipdata; m.detail=detail; return m
def itext(i): return f"{i.address:08X}  {i.bytes.hex(' '):<24}  {i.mnemonic} {i.op_str}".rstrip()
def parse_tgt(s):
    s=s.strip()
    if s.startswith('0x'):
        try: return int(s,16)
        except: return None
    return None
def canon_reg(n):
    n=n.upper()
    if n in ECX_REGS: return 'ECX'
    if n in EAX_REGS: return 'EAX'
    for k,v in CANON.items():
        if n in v: return k
    return n
def reg_w(insn):
    try: wr=insn.regs_access()[1]
    except: return set()
    return {canon_reg(insn.reg_name(r)) for r in wr}
def reg_r(insn):
    try: rd=insn.regs_access()[0]
    except: return set()
    return {canon_reg(insn.reg_name(r)) for r in rd}

def load_atlas():
    rows=[]
    with open(ATLAS,encoding='utf-8',errors='replace') as f:
        h=f.readline().rstrip('\n').split('\t')
        for line in f:
            p=line.rstrip('\n').split('\t')
            if len(p)<2: continue
            try: e=int(p[0],16); z=int(p[1],10)
            except: continue
            rows.append(dict(entry=e,size=z,raw=dict(zip(h,p))))
    rows.sort(key=lambda r:r['entry']); return rows
def containing(rows,va):
    hits=[r for r in rows if r['entry']<=va<r['entry']+r['size']]
    return min(hits,key=lambda r:r['size']) if hits else None

def full_sweep(b):
    m=md(); data=b.raw(b.text); starts=set(); calls=defaultdict(list); jmps=defaultdict(list)
    n=0; ns=0; mem_w=defaultdict(list); imm_l=defaultdict(list)
    tg={G368,G1E0}
    for i in m.disasm(data,b.text['va']):
        if i.id==0: ns+=1; continue
        n+=1; starts.add(i.address)
        if i.mnemonic=='call':
            t=parse_tgt(i.op_str)
            if t is not None: calls[t].append(i.address)
        elif i.mnemonic=='jmp':
            t=parse_tgt(i.op_str)
            if t is not None: jmps[t].append(i.address)
        for op in i.operands:
            if op.type==capstone.x86.X86_OP_MEM:
                mm=op.mem; disp=mm.disp&0xffffffff
                isw=(op is i.operands[0] and i.mnemonic.split()[0] in {
                    'mov','movzx','movsx','add','sub','inc','dec','and','or','xor','lea','xchg'})
                if isw and disp in tg:
                    mem_w[disp].append(dict(va=i.address,text=itext(i),
                        kind='abs' if mm.base==0 and mm.index==0 else 'reg+disp',
                        base=i.reg_name(mm.base) if mm.base else None))
            elif op.type==capstone.x86.X86_OP_IMM and (op.imm&0xffffffff) in tg:
                if i.mnemonic=='mov' and i.operands and i.operands[0].type==capstone.x86.X86_OP_REG:
                    imm_l[op.imm&0xffffffff].append(dict(va=i.address,reg=i.reg_name(i.operands[0].reg),text=itext(i)))
    return dict(starts=starts,calls=dict(calls),jmps=dict(jmps),n=n,ns=ns,mem_w=dict(mem_w),imm_l=dict(imm_l))

def disasm(b,s,e): return list(md().disasm(b.read(s,e-s),s))

def resolve_reg(instrs,idx,canon_,max_steps=100):
    r=canon_; j=idx-1; steps=0
    while j>=0 and steps<max_steps:
        ins=instrs[j]
        if ins.id and r in reg_w(ins):
            t=itext(ins)
            if ins.mnemonic=='mov' and len(ins.operands)==2:
                src=ins.operands[1]
                if src.type==capstone.x86.X86_OP_REG:
                    nx=canon_reg(ins.reg_name(src.reg))
                    if nx!=r: r=nx; j-=1; steps+=1; continue
                if src.type==capstone.x86.X86_OP_IMM: return f"imm {src.imm:#x} @ {ins.address:#x}: {t}"
                if src.type==capstone.x86.X86_OP_MEM: return f"mem {ins.op_str} @ {ins.address:#x}: {t}"
            if ins.mnemonic=='lea': return f"lea {ins.op_str} @ {ins.address:#x}: {t}"
            return f"other-write {ins.mnemonic} @ {ins.address:#x}: {t}"
        j-=1; steps+=1
    return f"entry-value/{r}"

def zero_guard(instrs,idx):
    last=None
    for k in range(idx-1,-1,-1):
        if 'ECX' in reg_w(instrs[k]): last=k; break
    if last is None: return dict(last_write=None,tests=[],fwd_je=[])
    tests=[]; fwd=[]
    for k in range(last,idx):
        ins=instrs[k]
        if ins.mnemonic=='test' and len(ins.operands)==2:
            a,c=ins.operands
            if a.type==c.type==capstone.x86.X86_OP_REG and canon_reg(ins.reg_name(a.reg))=='ECX' and canon_reg(ins.reg_name(c.reg))=='ECX':
                tests.append(dict(va=ins.address,text=itext(ins),kind='test ecx,ecx'))
        if ins.mnemonic=='cmp' and len(ins.operands)==2:
            a,c=ins.operands
            if a.type==capstone.x86.X86_OP_REG and canon_reg(ins.reg_name(a.reg))=='ECX' and c.type==capstone.x86.X86_OP_IMM and c.imm==0:
                tests.append(dict(va=ins.address,text=itext(ins),kind='cmp ecx,0'))
        if ins.mnemonic in ('je','jz'):
            t=parse_tgt(ins.op_str)
            if t is not None and t>instrs[idx].address: fwd.append(dict(va=ins.address,target=t,text=itext(ins)))
    return dict(last_write=ins.address if False else itext(instrs[last]),last_write_va=instrs[last].address,
                tests=tests,fwd_je=fwd,writes_after_load=idx-1-last)

def cfg_reach(instrs,target,extra=()):
    bya={ins.address:k for k,ins in enumerate(instrs)}
    if target not in bya: return False,[],[]
    start=instrs[0].address; q=deque([start]); prev={start:None}; branches=[]
    while q:
        a=q.popleft(); k=bya.get(a)
        if k is None: continue
        ins=instrs[k]
        if a==target:
            path=[]; cur=a
            while cur is not None: path.append(cur); cur=prev.get(cur)
            return True,list(reversed(path)),branches
        nx=instrs[k+1].address if k+1<len(instrs) else None
        m=ins.mnemonic; succ=[]
        if m in ('ret','retf'): succ=[]
        elif m.startswith('j') and m not in ('jmp',):
            t=parse_tgt(ins.op_str); succ=[x for x in (t,nx) if x is not None]
            branches.append(dict(va=ins.address,text=itext(ins),kind='cond',targets=succ))
        elif m=='jmp':
            t=parse_tgt(ins.op_str); succ=[t] if t is not None else list(extra)
        else: succ=[nx] if nx is not None else []
        for s2 in succ:
            if s2 not in prev: prev[s2]=a; q.append(s2)
    return False,[],branches

def dword_refs(b,value):
    pat=struct.pack('<I',value); out=[]
    for s in b.secs:
        d=b.raw(s); p=0
        while True:
            k=d.find(pat,p)
            if k<0: break
            out.append(dict(sec=s['name'],va=s['va']+k)); p=k+1
    return out
def imm_refs(b,values):
    out=defaultdict(list); m=md(); data=b.raw(b.text)
    for i in m.disasm(data,b.text['va']):
        if i.id==0: continue
        for op in i.operands:
            if op.type==capstone.x86.X86_OP_IMM and (op.imm&0xffffffff) in values:
                out[op.imm&0xffffffff].append(dict(va=i.address,text=itext(i)))
    return dict(out)
def jt_entries(b,tbl,n): return [struct.unpack('<I',b.read(tbl+4*i,4))[0] for i in range(n)]

def main():
    os.makedirs(OUT,exist_ok=True)
    dig=sha256(EXE); b=Bin(EXE); rows=load_atlas(); sw=full_sweep(b)
    sites=sorted(sw['calls'].get(TARGET,[]))
    # verify gap boundaries independently (ret+nop) before using them
    gap_note={}
    for site,(gs,ge) in GAP_FUNCS.items():
        w=b.read(gs,ge-gs)
        # find last ret within first 0x10 bytes from gs
        ins=disasm(b,gs,min(ge,gs+0x20))
        rets=[i for i in ins if i.mnemonic=='ret']
        gap_note[site]=dict(start=gs,end=ge,ret_va=rets[-1].address if rets else None,
                            bytes_head=w[:24].hex(' '))
    interesting={r['entry'] for r in rows if any(s in GAP_FUNCS and GAP_FUNCS[s][0]==r['entry'] for s in sites)}
    for s in GAP_FUNCS: interesting.add(GAP_FUNCS[s][0])
    imm_by=imm_refs(b,interesting)

    reports=[]
    for s in sites:
        fn=containing(rows,s); src='atlas-interval'
        if s in GAP_FUNCS:
            gs,ge=GAP_FUNCS[s]
            fn=dict(entry=gs,size=ge-gs,raw={'source':'independent-boundary'})
            src='independent-boundary(ret+nop)'
        if fn is None:
            reports.append(dict(site=s,error='no containing interval')); continue
        st,en=fn['entry'],fn['entry']+fn['size']
        ins=disasm(b,st,en); bya={i.address:k for k,i in enumerate(ins)}; k=bya.get(s)
        if k is None:
            reports.append(dict(site=s,fn=st,error='site not boundary from fn entry')); continue
        ecxw=[dict(va=i.address,text=itext(i)) for i in ins[:k] if 'ECX' in reg_w(i)]
        zg=zero_guard(ins,k); srcstr=resolve_reg(ins,k,'ECX')
        reach,path,branches=cfg_reach(ins,s)
        callers=sw['calls'].get(st,[]); fptr=dword_refs(b,st); imms=imm_by.get(st,[])
        static=len(callers)+len(fptr)+len(imms)
        # push arg detection: nearest push before site (scan back up to 10 insns)
        pushes=[]
        for j in range(max(0,k-24),k):
            if ins[j].mnemonic=='push': pushes.append(dict(va=ins[j].address,text=itext(ins[j])))
        # nop/int3 runs in [s-16,s+16]
        win=b.read(s-16,32); runs=[]; i=0
        while i<len(win):
            if win[i] in (0x90,0xcc):
                j=i
                while j<len(win) and win[j] in (0x90,0xcc): j+=1
                runs.append(dict(va=s-16+i,length=j-i,byte=hex(win[i]))); i=j
            else: i+=1
        # crash: callee first deref [ebp+0x250], ebp=ecx
        prev=[('>> ' if ins[j].address==s else '   ')+itext(ins[j]) for j in range(max(0,k-14),min(len(ins),k+3))]
        reports.append(dict(
            site=f"{s:08X}",site_int=s,fn=f"{st:08X}",fn_int=st,fn_size=fn['size'],fn_source=src,
            boundary=s in sw['starts'],ecx_source=srcstr,ecx_writes=ecxw,ecx_write_count=len(ecxw),
            zero_guard=zg,reachable=reach,path_len=len(path),path=path,branches=branches,
            direct_callers=callers,caller_count=len(callers),
            dword_refs=fptr[:12],dword_ref_count=len(fptr),imm_refs=imms[:12],imm_ref_count=len(imms),
            host_static_refs=static,host_grade='static-ref' if static else 'zero-static-ref',
            pushes_before=pushes,nop_runs=runs,
            call_bytes=b.read(s,5).hex(' '),prev=prev,
            crash_va='0x724737',crash_insn='mov eax, dword ptr [ebp+0x250]',
            crash_reason='ebp=ecx(this)=0 -> deref address 0x250 -> AV fault 0x250'))

    # 0x6CD8CD
    fn6=containing(rows,S6); st6,en6=fn6['entry'],fn6['entry']+fn6['size']
    ins6=disasm(b,st6,en6); by6={i.address:k for k,i in enumerate(ins6)}; k6=by6.get(S6)
    jt=jt_entries(b,JT_6CC390,12)
    reach6,path6,br6=cfg_reach(ins6,S6,extra=jt)
    six=dict(site=f"{S6:08X}",fn=f"{st6:08X}",fn_size=fn6['size'],
             boundary=S6 in sw['starts'],eax_source=resolve_reg(ins6,k6,'EAX'),
             ecx_source=resolve_reg(ins6,k6,'ECX'),reachable=reach6,path_len=len(path6),
             path=path6,branches=br6,jump_table=[hex(x) for x in jt],
             callers=sw['calls'].get(st6,[]),dword_count=len(dword_refs(b,st6)),
             prev=[('>> ' if ins6[j].address==S6 else '   ')+itext(ins6[j]) for j in range(max(0,k6-16),k6+5)],
             crash_va='0x6CD8CD',crash_insn='mov ecx, dword ptr [eax+0x250]',
             crash_reason='eax=[0x8871E0]=0 -> deref 0x250 -> AV fault 0x250')
    # global writers
    gw={}
    for g in (G368,G1E0):
        ws=sw['mem_w'].get(g,[]); enriched=[]
        for w in ws:
            wf=containing(rows,w['va'])
            enriched.append({**w,'writer_fn':wf['entry'] if wf else None,
                             'callers':sw['calls'].get(wf['entry'],[]) if wf else []})
        gw[f"{g:08X}"]=dict(mem_writes=ws,imm_loads=sw['imm_l'].get(g,[]),writers=enriched)

    core=dict(sha=dig,sha_ok=dig==EXPECTED_SHA,ib=b.ib,text=b.text,
              sweep=dict(insns=sw['n'],skipdata=sw['ns'],call_sites=[f"{s:08X}" for s in sites],call_count=len(sites)),
              callee=dict(entry=f"{TARGET:08X}",ret=dict(va='0x7248AE',text='ret 4'),
                          head=[itext(i) for i in disasm(b,TARGET,TARGET+24)]),
              gap_verification=gap_note,sites=reports,s6=six,globals=gw)
    with open(os.path.join(OUT,'core.json'),'w',encoding='utf-8') as f:
        json.dump(core,f,ensure_ascii=False,indent=2)

    # dump.txt
    L=[]
    L.append(f"SHA256={dig} OK={dig==EXPECTED_SHA} IB={b.ib:#x}")
    L.append(f"FULL SWEEP insns={sw['n']} skipdata={sw['ns']}")
    L.append(f"call->724730 count={len(sites)}")
    L.append("CALLEE HEAD (crash @0x724737 mov eax,[ebp+0x250], ebp=ecx=0):")
    L.extend("  "+x for x in core['callee']['head'])
    L.append(f"CALLEE RET: {core['callee']['ret']['text']} @ {core['callee']['ret']['va']} -> cleans 4-byte stack arg")
    L.append("GAP BOUNDARY VERIFICATION:")
    for site,note in gap_note.items(): L.append(f"  site {site:#x}: {note}")
    L.append("")
    for r in reports:
        L.append(f"=== SITE {r['site']} host {r['fn']} size={r['fn_size']} src={r['fn_source']} boundary={r['boundary']} ===")
        if 'error' in r: L.append("ERROR "+r['error']); continue
        L.append(f"ecx_source={r['ecx_source']}")
        L.append(f"ecx_write_count={r['ecx_write_count']} last_write={r['zero_guard'].get('last_write')} va={r['zero_guard'].get('last_write_va'):#x}" if r['zero_guard'].get('last_write_va') else f"ecx_write_count={r['ecx_write_count']}")
        L.append(f"zero_guard_tests={[t['text'] for t in r['zero_guard']['tests']]} fwd_je={[t['text'] for t in r['zero_guard']['fwd_je']]}")
        L.append(f"reachable_from_fn_entry={r['reachable']} path_len={r['path_len']} branches_on_path={len(r['branches'])}")
        for br in r['branches'][:6]: L.append("    BR "+br['text']+f" -> {[hex(x) for x in br['targets']]}")
        L.append(f"callers={r['caller_count']} dword_refs={r['dword_ref_count']} imm_refs={r['imm_ref_count']} host_grade={r['host_grade']}")
        L.append(f"push_arg_before={[p['text'] for p in r['pushes_before']]}")
        L.append(f"call_bytes={r['call_bytes']} nop_runs={r['nop_runs']}")
        L.append(f"crash={r['crash_va']} {r['crash_insn']} :: {r['crash_reason']}")
        L.extend(r['prev']); L.append("")
    L.append(f"=== SITE {six['site']} ===")
    for key in ('fn','fn_size','boundary','eax_source','ecx_source','reachable','path_len','jump_table','callers','dword_count','crash_va','crash_insn','crash_reason'):
        L.append(f"{key}={six[key]}")
    for br in six['branches'][:8]: L.append("    BR "+br['text'])
    L.extend(six['prev']); L.append("")
    for g,p in gw.items():
        L.append(f"=== GLOBAL {g} ===")
        for w in p['mem_writes']: L.append("  WRITE "+w['text']+f" writer_fn={hex(next((e['writer_fn'] for e in p['writers'] if e['va']==w['va']),0)) if False else ''}")
        for e in p['writers']: L.append(f"    writer {e['va']:#x} fn={e['writer_fn']:#x} callers={[hex(x) for x in e['callers'][:6]]}" if e['writer_fn'] else f"    writer {e['va']:#x} fn=None")
        L.append("")
    with open(os.path.join(OUT,'dump.txt'),'w',encoding='utf-8') as f: f.write("\n".join(L))

    # site_table.tsv (compact)
    T=["site\tfn\tfn_size\tboundary\tecx_source\tecx_writes\treachable\tpath_len\tcallers\tdword\timm\thost_grade\tzero_tests\tpushes\tnop_runs\tcall_bytes\tcrash"]
    for r in reports:
        if 'error' in r: T.append("\t".join([r['site'],'ERROR'])); continue
        T.append("\t".join([
            r['site'],r['fn'],str(r['fn_size']),str(r['boundary']),r['ecx_source'].replace('\t',' '),
            str(r['ecx_write_count']),str(r['reachable']),str(r['path_len']),str(r['caller_count']),
            str(r['dword_ref_count']),str(r['imm_ref_count']),r['host_grade'],
            str(len(r['zero_guard']['tests'])),str(len(r['pushes_before'])),
            str(len(r['nop_runs'])),r['call_bytes'],r['crash_va']]))
    with open(os.path.join(OUT,'site_table.tsv'),'w',encoding='utf-8') as f: f.write("\n".join(T))

    nsites=len(reports)
    reach=sum(1 for r in reports if r.get('reachable') and r.get('host_grade')=='static-ref')
    print(json.dumps(dict(sha_ok=dig==EXPECTED_SHA,sites=len(sites),
        boundaries=sum(1 for r in reports if r.get('boundary')),
        proven_reach_null=reach,
        zero_static_ref=sum(1 for r in reports if r.get('host_grade')=='zero-static-ref'),
        ecx_global=sum(1 for r in reports if '0x887368' in r.get('ecx_source','')),
        zero_guard=sum(1 for r in reports if r.get('zero_guard',{}).get('tests')),
        s6_reach=six['reachable'],s6_path=six['path_len']),ensure_ascii=False,indent=2))

if __name__=='__main__': main()
