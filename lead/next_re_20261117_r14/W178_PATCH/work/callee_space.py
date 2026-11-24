"""W178-PATCH: verify callee 0x724730 stack cleanup + per-site padding/space analysis."""
from __future__ import annotations
import os, json, struct
import capstone, pefile

ROOT=r"D:\Project\ra2-campaign-forge"
EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
ATLAS=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","W178_PATCH","EVIDENCE")
TARGET=0x724730

class Bin:
    def __init__(self,p):
        self.pe=pefile.PE(p,fast_load=True); self.ib=self.pe.OPTIONAL_HEADER.ImageBase
        self.secs=[]
        for s in self.pe.sections:
            n=s.Name.decode('utf-8','replace').rstrip('\x00')
            self.secs.append(dict(name=n,va=self.ib+s.VirtualAddress,raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
    def read(self,va,n):
        for s in self.secs:
            if s['va']<=va and va+n<=s['va']+s['rawsize']:
                return self.pe.__data__[s['raw']+(va-s['va']):s['raw']+(va-s['va'])+n]
        raise ValueError(f"{va:#x}+{n}")
    def raw(self,s): return self.pe.__data__[s['raw']:s['raw']+s['rawsize']]
def md(skipdata=True,detail=True):
    m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.skipdata=skipdata; m.detail=detail; return m
def itext(i): return f"{i.address:08X}  {i.bytes.hex(' '):<24}  {i.mnemonic} {i.op_str}".rstrip()
def load_atlas():
    rows=[]
    with open(ATLAS,encoding='utf-8',errors='replace') as f:
        h=f.readline().rstrip('\n').split('\t')
        for line in f:
            p=line.rstrip('\n').split('\t')
            if len(p)<2: continue
            try: e=int(p[0],16); z=int(p[1],10)
            except: continue
            rows.append(dict(entry=e,size=z))
    rows.sort(key=lambda r:r['entry']); return rows
def containing(rows,va):
    hits=[r for r in rows if r['entry']<=va<r['entry']+r['size']]
    return min(hits,key=lambda r:r['size']) if hits else None
def disasm(b,s,e): return list(md().disasm(b.read(s,e-s),s))
def sites_of(b):
    sw=sorted([i.address for i in md().disasm(b.raw(next(s for s in b.secs if s['name']=='.text')),b.ib+0x1000)
               if i.mnemonic=='call' and i.op_str.strip()==hex(TARGET)])
    return sw

def main():
    b=Bin(EXE); rows=load_atlas(); sites=sites_of(b)
    lines=[]
    # --- callee full ret scan ---
    fn=containing(rows,TARGET); end=fn['entry']+fn['size']
    ins=disasm(b,TARGET,end)
    rets=[i for i in ins if i.mnemonic in ('ret','retf')]
    lines.append(f"=== CALLEE 0x{TARGET:X} host={fn['entry']:08X} size={fn['size']} ===")
    lines.append(f"total insns={len(ins)} rets={len(rets)}")
    for i in rets: lines.append("  RET "+itext(i))
    lines.append("first 6 insns:")
    for i in ins[:6]: lines.append("  "+itext(i))
    lines.append("last 12 insns:")
    for i in ins[-12:]: lines.append("  "+itext(i))
    # --- per-site padding & push analysis ---
    lines.append("\n=== PER-SITE: 12 insns before / 4 after, padding runs, push count ===")
    per=[]
    for s in sites:
        f=containing(rows,s)
        if f is None:
            lines.append(f"\n--- {s:08X} NO ATLAS CONTAINING INTERVAL ---")
            per.append(dict(site=f"{s:08X}",host=None,runs=[],pushes=[],note='no atlas interval'))
            continue
        st,en=f['entry'],f['entry']+f['size']
        ins=disasm(b,st,en); bya={insn.address:idx for idx,insn in enumerate(ins)}; k=bya.get(s)
        if k is None: lines.append(f"{s:08X} NOT BOUNDARY in host {st:08X}"); continue
        pre=ins[max(0,k-12):k+5]
        win=b.read(s-16,16+16)
        # nop/int3 runs in [s-16,s+16]
        runs=[]; i=0
        while i<len(win):
            if win[i] in (0x90,0xcc):
                j=i
                while j<len(win) and win[j] in (0x90,0xcc): j+=1
                runs.append((s-16+i,j-i,hex(win[i]))); i=j
            else: i+=1
        pushes=[itext(i) for i in ins[max(0,k-8):k] if i.mnemonic=='push']
        lines.append(f"\n--- {s:08X} host {st:08X} ---")
        for i in pre:
            lines.append((">> " if i.address==s else "   ")+itext(i))
        lines.append(f"  raw[-16..+16]={win.hex(' ')}")
        lines.append(f"  nop/int3 runs (va,len,byte): {[(hex(a),n,bt) for a,n,bt in runs]}")
        lines.append(f"  pushes in 8 insns before call: {pushes}")
        per.append(dict(site=f"{s:08X}",host=f"{st:08X}",runs=[[hex(a),n,bt] for a,n,bt in runs],pushes=pushes))
    with open(os.path.join(OUT,'CalleeAndSpace.txt'),'w',encoding='utf-8') as f: f.write("\n".join(lines))
    with open(os.path.join(OUT,'space.json'),'w',encoding='utf-8') as f:
        json.dump(dict(rets=[itext(i) for i in rets],per=per),f,ensure_ascii=False,indent=2)
    print(f"rets={[ (hex(i.address),i.mnemonic,i.op_str) for i in rets]}")
    print(f"sites with any nop/int3 run in [-16,+16]: {sum(1 for p in per if p['runs'])}/{len(per)}")
    print(f"sites with push before call: {sum(1 for p in per if p['pushes'])}/{len(per)}")

if __name__=='__main__': main()
