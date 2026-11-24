"""W178-PATCH exploratory analysis (read-only against gamemd.exe).

Finds all `call 0x724730` sites, host functions (atlas interval containment),
callee head, and byte/disasm context around each site for P1 space analysis.
All outputs under W178_PATCH/EVIDENCE.
"""
from __future__ import annotations
import hashlib, json, os, struct
import capstone, pefile

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT = os.path.join(ROOT, "lead", "next_re_20261117_r14", "W178_PATCH", "EVIDENCE")
EXPECTED_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
IB = 0x400000
TARGET = 0x724730
S6 = 0x6CD8CD

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest().upper()

class Bin:
    def __init__(self,p):
        self.pe=pefile.PE(p,fast_load=True)
        self.ib=self.pe.OPTIONAL_HEADER.ImageBase
        self.secs=[]
        for s in self.pe.sections:
            n=s.Name.decode('utf-8','replace').rstrip('\x00')
            self.secs.append(dict(name=n, va=self.ib+s.VirtualAddress, vsize=s.Misc_VirtualSize,
                                  raw=s.PointerToRawData, rawsize=s.SizeOfRawData))
        self.text=next(s for s in self.secs if s['name']=='.text')
    def read(self,va,n):
        for s in self.secs:
            if s['va']<=va and va+n<=s['va']+s['rawsize']:
                off=s['raw']+(va-s['va'])
                return self.pe.__data__[off:off+n]
        raise ValueError(f"VA {va:#x}+{n} not in raw range")
    def raw(self,s): return self.pe.__data__[s['raw']:s['raw']+s['rawsize']]

def md(skipdata=True,detail=True):
    m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    m.skipdata=skipdata; m.detail=detail
    return m

def itext(i): return f"{i.address:08X}  {i.bytes.hex(' '):<24}  {i.mnemonic} {i.op_str}".rstrip()

def parse_tgt(s):
    s=s.strip()
    if s.startswith('0x'):
        try: return int(s,16)
        except: return None
    return None

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
    rows.sort(key=lambda r:r['entry'])
    return rows

def containing(rows,va):
    hits=[r for r in rows if r['entry']<=va<r['entry']+r['size']]
    return min(hits,key=lambda r:r['size']) if hits else None

def disasm(b,start,end):
    return list(md().disasm(b.read(start,end-start),start))

def sweep(b):
    m=md(); data=b.raw(b.text)
    starts=set(); calls={}; jmps={}; n=0; nskip=0; ff15=[]
    for i in m.disasm(data,b.text['va']):
        if i.id==0: nskip+=1; continue
        n+=1; starts.add(i.address)
        if i.mnemonic=='call':
            t=parse_tgt(i.op_str)
            if t is not None: calls.setdefault(t,[]).append(i.address)
        elif i.mnemonic=='jmp':
            t=parse_tgt(i.op_str)
            if t is not None: jmps.setdefault(t,[]).append(i.address)
    return dict(starts=starts,calls=calls,jmps=jmps,n=n,nskip=nskip)

def main():
    os.makedirs(OUT,exist_ok=True)
    dig=sha256(EXE); b=Bin(EXE); rows=load_atlas(); sw=sweep(b)
    sites=sorted(sw['calls'].get(TARGET,[]))
    out=[]
    out.append(f"SHA256={dig} OK={dig==EXPECTED_SHA} IB={b.ib:#x}")
    out.append(f".text va={b.text['va']:#x} rawsize={b.text['rawsize']:#x}")
    out.append(f"FULL SWEEP insns={sw['n']} skipdata={sw['nskip']}")
    out.append(f"call->724730 count={len(sites)}")
    out.append("SITES: "+" ".join(f"{s:08X}" for s in sites))
    out.append("\n=== CALLEE HEAD 0x724730 (first 32 bytes, 12 insns) ===")
    for i in disasm(b,TARGET,TARGET+32)[:12]:
        out.append("  "+itext(i))
    out.append("\n=== ALL call/jmp targets == to 724730 (indirect check) ===")
    out.append(f"direct call sites={len(sites)}; jmp targets={len(sw['jmps'].get(TARGET,[]))}")
    # byte scan for 0x724730 as dword anywhere (vtable check)
    pat=struct.pack('<I',TARGET); refs=[]
    for s in b.secs:
        d=b.raw(s); p=0
        while True:
            k=d.find(pat,p)
            if k<0: break
            refs.append((s['name'],f"{s['va']+k:08X}")); p=k+1
    out.append(f"dword refs to 724730 anywhere: {len(refs)} {refs[:8]}")

    out.append("\n\n=== PER-SITE CONTEXT (host, ecx, bytes before/after) ===")
    per=[]
    for s in sites:
        fn=containing(rows,s)
        src='atlas'
        if fn is None:
            per.append(dict(site=s,error='no atlas interval')); continue
        start,end=fn['entry'],fn['entry']+fn['size']
        ins=disasm(b,start,end)
        bya={i.address:i for i in ins}
        ctx=[i for i in ins if s-0x40<=i.address<=s+0x20]
        out.append(f"\n--- site {s:08X} host {start:08X}({fn['size']}B) src={src} ---")
        for i in ctx:
            mark='>>' if i.address==s else '  '
            out.append(f"{mark} {itext(i)}")
        # raw bytes window
        win=b.read(s-16,16+16)
        out.append(f"    bytes[-16..+16] @{s-16:08X}: {win.hex(' ')}")
        per.append(dict(site=f"{s:08X}",host=f"{start:08X}",size=fn['size'],
                        insns=[itext(i) for i in ctx]))
    with open(os.path.join(OUT,'EXPLORE.txt'),'w',encoding='utf-8') as f:
        f.write("\n".join(out))
    with open(os.path.join(OUT,'explore.json'),'w',encoding='utf-8') as f:
        json.dump(dict(sha=dig,sha_ok=dig==EXPECTED_SHA,sites=[f"{s:08X}" for s in sites],
                       sweep_insns=sw['n'],sites_per=per),f,ensure_ascii=False,indent=2)
    print(f"sites={len(sites)} sha_ok={dig==EXPECTED_SHA}")
    print("  "+" ".join(f"{s:08X}" for s in sites))

if __name__=='__main__': main()
