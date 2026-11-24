"""Focused per-function view: loop contexts, jump tables, error constants, prologue/epilogue."""
import os, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout.reconfigure(encoding="utf-8")

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
COVERAGE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
EVDIR = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_SLOTS\EVIDENCE"
WINDOW = 0x1000

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True
with open(EXE,"rb") as f: blob=f.read()
def off(va): return pe.get_offset_from_rva(va-IB)

def loadrows():
    with open(COVERAGE,encoding="utf-8") as f:
        f.readline()
        return [p for p in (l.rstrip("\n").split("\t") for l in f)
                if len(p)==8 and "槽语义未证" in p[3] and p[4]=="[已证]" and p[1]!="S22"]

def fmt(ins, va): return f"+0x{ins.address-va:04X} {ins.mnemonic:<7} {ins.op_str}"

def analyze(p):
    va=int(p[0],16); o=off(va); data=blob[o:o+WINDOW]
    insns=list(md.disasm(data,va))
    rets=[i for i,x in enumerate(insns) if x.mnemonic in ("ret","retf")]
    if rets:
        endi=rets[0]
        for r in rets:
            if r-endi<=8: endi=r
            else: break
        endi=min(endi+1,len(insns))
    else: endi=min(120,len(insns))
    body=insns[:endi]
    out=[f"=== {p[0]} {p[1]} {p[2]} | oldsem: {p[3]}"]
    out.append(f"    body {len(body)} insns span 0x{body[-1].address-va if body else 0:X}")
    # prologue
    out.append("  PROLOGUE:")
    for ins in body[:6]: out.append("    "+fmt(ins,va))
    # find loops (backward jcc/jmp), jump tables (indirect jmp), error constants
    loops=[]; jtabs=[]; errs=[]
    for i,ins in enumerate(body):
        if ins.mnemonic.startswith("j") and ins.op_str.startswith("0x"):
            try:
                tgt=int(ins.op_str,16)
                if tgt<ins.address: loops.append(i)
            except: pass
        if ins.mnemonic=="jmp" and not ins.op_str.startswith("0x"):
            jtabs.append(i)
        # notable constants
        for c in ("0x80004002","0x80004003","0x80070057","-1","-2","0x46","0x48","0x121","0x1cb0"):
            if c in ins.op_str and ins.mnemonic in ("cmp","mov","test"):
                errs.append(i); break
    for tag, idcs, ctxb, ctxa in (("LOOP", loops, 12, 3), ("JUMP-TABLE", jtabs, 6, 3), ("CONST", errs, 3, 2)):
        seen=set()
        for i in idcs:
            if i in seen: continue
            # merge nearby indices
            lo=max(0,i-ctxb); hi=min(len(body),i+ctxa+1)
            chunk=[]
            for j in range(lo,hi):
                if j in seen: continue
                seen.add(j); chunk.append("    "+fmt(body[j],va))
            out.append(f"  {tag} @ +0x{body[i].address-va:X}:")
            out.extend(chunk)
    # epilogue
    out.append("  EPILOGUE:")
    for ins in body[-8:]: out.append("    "+fmt(ins,va))
    out.append("")
    return "\n".join(out)

def main():
    rows=loadrows()
    txt="\n".join(analyze(p) for p in rows)
    with open(os.path.join(EVDIR,"FOCUS.txt"),"w",encoding="utf-8") as f: f.write(txt)
    print(f"wrote FOCUS.txt {len(txt.splitlines())} lines")

if __name__=="__main__": main()
