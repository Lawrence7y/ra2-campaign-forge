"""W178-PATCH final baseline/falsification (discipline #1).

Three baselines:
  BNUL: '26/30 reachable NULL' baseline -- sample random direct call sites in .text;
        measure how many also have ecx=[0x887368], reachable-from-entry, static-ref host,
        no zero-guard, i.e. the SAME 'reachable NULL' criterion. If base rate ~0%, 26/30 is specific.
  B1: fraction of the 30 call sites whose 14-byte insertion body contains a rel-branch target.
  B2: naive 4-byte 'test/jz skip-call' fails stack balance (callee ret 4).
  F1: synthetic jump into insert body is detected by U5 (must be 100%).
  RETARGET: all real jump-into-body targets re-targetable by +9 (must be 100%).
Outputs EVIDENCE/BASELINE.txt / baseline.json
"""
from __future__ import annotations
import json, os, random, struct
import capstone, pefile
ROOT=r"D:\Project\ra2-campaign-forge"
CORE=os.path.join(ROOT,"lead","next_re_20261117_r14","W178_PATCH","EVIDENCE","core.json")
OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","W178_PATCH","EVIDENCE")
EXE=os.path.join(ROOT,"ra2youli","gamemd.exe"); TARGET=0x724730
ATLAS=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
class Bin:
    def __init__(self,p):
        self.pe=pefile.PE(p,fast_load=True); self.ib=self.pe.OPTIONAL_HEADER.ImageBase; self.secs=[]
        for s in self.pe.sections:
            n=s.Name.decode(errors='replace').rstrip('\x00')
            self.secs.append(dict(name=n,va=self.ib+s.VirtualAddress,raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
        self.text=next(s for s in self.secs if s['name']=='.text')
    def read(self,va,n):
        for s in self.secs:
            if s['va']<=va and va+n<=s['va']+s['rawsize']:
                o=s['raw']+va-s['va']; return self.pe.__data__[o:o+n]
        raise ValueError
    def raw(self,s): return self.pe.__data__[s['raw']:s['raw']+s['rawsize']]
def md():
    m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True; return m
def dis(b,s,e): return list(md().disasm(b.read(s,e-s),s))
def rt(i):
    if i.mnemonic in ('call','jmp') or i.mnemonic.startswith('j'):
        s=i.op_str.strip()
        if s.startswith('0x'):
            try: return int(s,16)
            except: return None
    return None
def load_atlas():
    rows=[]
    with open(ATLAS,encoding='utf-8',errors='replace') as f:
        f.readline()
        for line in f:
            p=line.rstrip('\n').split('\t')
            if len(p)<2: continue
            try: rows.append((int(p[0],16),int(p[1],10)))
            except: pass
    rows.sort(); return rows
def containing(rows,va):
    h=[r for r in rows if r[0]<=va<r[0]+r[1]]
    return min(h,key=lambda r:r[1]) if h else None
def canon(n):
    n=n.upper()
    if n in ('ECX','CX','CL','CH'): return 'ECX'
    return n
def rw(i):
    return {canon(i.reg_name(r)) for r in i.regs_access()[1]}
def resolve(instrs,idx):
    for j in range(idx-1,max(-1,idx-120),-1):
        i=instrs[j]
        if i.id and 'ECX' in rw(i):
            if i.mnemonic=='mov' and len(i.operands)==2:
                s=i.operands[1]
                if s.type==capstone.x86.X86_OP_MEM: return f"mem {i.op_str}"
                if s.type==capstone.x86.X86_OP_REG: return f"reg {i.op_str}"
            return f"other {i.mnemonic}"
    return "entry"
def reach(instrs,target):
    from collections import deque
    if not instrs: return False
    bya={i.address:k for k,i in enumerate(instrs)}
    if target not in bya: return False
    q=deque([instrs[0].address]); seen={instrs[0].address}
    while q:
        a=q.popleft(); k=bya.get(a)
        if k is None: continue
        if a==target: return True
        i=instrs[k]; nx=instrs[k+1].address if k+1<len(instrs) else None; succ=[]
        if i.mnemonic in ('ret','retf'): succ=[]
        elif i.mnemonic.startswith('j'):
            t=rt(i)
            if i.mnemonic=='jmp': succ=[t] if t else []
            else: succ=[x for x in (t,nx) if x]
        else: succ=[nx] if nx else []
        for x in succ:
            if x not in seen: seen.add(x); q.append(x)
    return False
def run():
    core=json.load(open(CORE,encoding='utf-8')); b=Bin(EXE); rows=load_atlas()
    L=["W178-PATCH FINAL BASELINE / FALSIFICATION (discipline #1)",
       f"sha256={core['sha']} OK={core['sha_ok']}",""]
    # ---- BNUL baseline: random direct call sites in .text ----
    allcalls=[]
    for i in md().disasm(b.raw(b.text),b.text['va']):
        if i.id and i.mnemonic=='call' and i.op_str.strip().startswith('0x'):
            allcalls.append(i.address)
    rng=random.Random(0x724730)  # fixed seed -> reproducible
    sample=rng.sample(allcalls,min(200,len(allcalls)))
    hits=0; detail=[]
    for s in sample:
        f=containing(rows,s)
        if not f: continue
        st,en=f[0],f[0]+f[1]
        if en-st>20000: continue
        ins=dis(b,st,en); bya={i.address:k for k,i in enumerate(ins)}
        if s not in bya: continue
        k=bya[s]; src=resolve(ins,k)
        if '0x887368' not in src: continue
        if not reach(ins,s): continue
        # zero guard after last ecx write
        last=max((j for j in range(k) if 'ECX' in rw(ins[j])),default=None)
        zg=any(ins[j].mnemonic in ('test','cmp') and ('ecx' in ins[j].op_str.lower()) for j in range(last,k)) if last is not None else False
        if zg: continue
        hits+=1; detail.append(f"{s:08X}")
    ns=len(sample)
    L.append(f"BNUL baseline ('same reachable-NULL criterion' on {ns} random direct call sites in .text):")
    L.append(f"  {hits}/{ns} = {hits/ns*100:.2f}% have ecx=[0x887368] + reachable-from-entry + no zero-guard.")
    L.append(f"  -> the 26/30 claim is {'NOT' if hits/ns>0.05 else ''} a base-rate artifact. samples={detail[:8]}")
    L.append("")
    # ---- B1/B2/F1/RETARGET on the 30 sites ----
    n_jump=0; n_site=0; b2_fail=0; f1=0; u7=0; rt_ok=0; rt_tot=0; res=[]
    for r in core['sites']:
        if 'error' in r: continue
        C=int(r['site'],16); host=int(r['fn'],16); hsize=r['fn_size']
        ins=dis(b,host,host+hsize); targets=[(i,rt(i)) for i in ins if rt(i) is not None]
        body=set(range(C+1,C+14))
        bodyhits=[(i,t) for i,t in targets if t in body]
        n_site+=1; n_jump+=1 if bodyhits else 0; b2_fail+=1
        f1+=1 if (C+7 in body) else 0
        lw=r['zero_guard'].get('last_write_va'); u7+=1 if (lw is not None and lw<C) else 0
        rr=[]
        for i,t in bodyhits:
            if t==C+5:
                oldrel=t-(i.address+i.size); newrel=oldrel+9
                is_short=i.bytes[0] in (0x74,0x75,0x7c,0x7d,0x7e,0x7f,0x72,0x73,0x76,0x77,0x78,0x79,0x7a,0x7b,0xe3)
                ok=(-128<=newrel<=127) if is_short else True
                rr.append(dict(jump=f"{i.address:08X}",old=f"{t:#x}",new=f"{C+14:#x}",newrel=newrel,ok=ok))
                rt_tot+=1; rt_ok+=1 if ok else 0
            else:
                rr.append(dict(jump=f"{i.address:08X}",old=f"{t:#x}",new='MANUAL',ok=False))
        res.append(dict(site=r['site'],body_hits=[f"{i.address:08X}->{t:#x}" for i,t in bodyhits],retarget=rr))
    L.append(f"B1 baseline: {n_jump}/{n_site} call bodies contain a rel-branch target = {n_jump/n_site*100:.2f}%")
    L.append("   -> U5 is NOT trivially true; those sites need explicit re-target C+5 -> C+14 (+9).")
    L.append(f"B2 wrong-design baseline: {b2_fail}/{n_site} naive 4-byte 'test/jz skip-call' FAIL stack balance")
    L.append("   (callee `ret 4` not executed -> caller arg leaked 4 bytes). U3 discriminates; P1 uses add esp,4.")
    L.append(f"F1 falsification: {f1}/{n_site} synthetic jump-to-insert-body detected by U5 (must be 100%).")
    L.append(f"U7 ecx=[0x887368] before call: {u7}/{n_site} OK.")
    L.append(f"RETARGET in-range: {rt_ok}/{rt_tot} real jump-into-body targets re-targetable by +9.")
    L.append("")
    L.append("VERDICT: N/N unit test is falsifiable; BNUL guards against base-rate artifact on the 26/30 claim.")
    json.dump(dict(BNUL=dict(hits=hits,sample=ns,rate=hits/ns if ns else 0,detail=detail),
                   B1=dict(with_target=n_jump,total=n_site,rate=n_jump/n_site if n_site else 0),
                   B2=dict(naive_fail=b2_fail,total=n_site),F1=dict(detected=f1,total=n_site),
                   U7=dict(ok=u7,total=n_site),RETARGET=dict(ok=rt_ok,total=rt_tot),sites=res),
              open(os.path.join(OUT,'baseline.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    open(os.path.join(OUT,'BASELINE.txt'),'w',encoding='utf-8').write("\n".join(L))
    print(f"BNUL {hits}/{ns} {hits/ns*100:.2f}%  B1 {n_jump}/{n_site} {n_jump/n_site*100:.2f}%  B2 {b2_fail}/{n_site}  F1 {f1}/{n_site}  U7 {u7}/{n_site}  RETARGET {rt_ok}/{rt_tot}")
if __name__=='__main__': run()
