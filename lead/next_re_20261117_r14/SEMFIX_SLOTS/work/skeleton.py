"""Compact control-flow skeleton per function, trimmed at the first 'ret cluster'.

A 'ret cluster' = the first ret plus any further ret within 0x20 bytes after it
(typical two-exit MSVC thiscall). This approximates the function body end for
these tightly-packed vtable-slot functions (no int3 padding in this binary).

Also reports all ret offsets in the wider window for transparency.
"""
import os, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout.reconfigure(encoding="utf-8")

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
COVERAGE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_SLOTS"
EVDIR = os.path.join(BASE, "EVIDENCE")
WINDOW = 0x1000

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True
with open(EXE, "rb") as f: blob = f.read()
def off(va): return pe.get_offset_from_rva(va - IB)

BRANCH = {"je","jne","jz","jnz","jg","jge","jl","jle","ja","jae","jb","jbe",
          "js","jns","jo","jno","jp","jnp","jecxz","loop","loope","loopne",
          "call","ret","retf","jmp"}
INTEREST = BRANCH | {"cmp","test","inc","dec","add","sub","imul","xor","and","or"}

def loadrows():
    with open(COVERAGE, encoding="utf-8") as f:
        f.readline()
        return [p for p in (l.rstrip("\n").split("\t") for l in f)
                if len(p)==8 and "槽语义未证" in p[3] and p[4]=="[已证]" and p[1]!="S22"]

def analyze(p):
    va = int(p[0],16); o = off(va); data = blob[o:o+WINDOW]
    insns = list(md.disasm(data, va))
    rets = [i for i,ins in enumerate(insns) if ins.mnemonic in ("ret","retf")]
    if not rets:
        endi = min(len(insns), 120)
    else:
        endi = rets[0]
        for r in rets:
            if r - endi <= 8: endi = r
            else: break
        endi = min(endi+1, len(insns))
    body = insns[:endi]
    out = []
    out.append(f"=== {p[0]} {p[1]} {p[2]} ===")
    out.append(f"oldsem: {p[3]}")
    out.append(f"body: {len(body)} insns, span 0x{body[-1].address-va if body else 0:X}; "
               f"all_rets@" + ",".join(f"+0x{insns[i].address-va:X}" for i in rets[:8]))
    # prologue (first 4)
    for ins in body[:4]:
        out.append(f"  +0x{ins.address-va:04X} {ins.mnemonic:<7} {ins.op_str}")
    out.append("  ... ctrl-flow:")
    for ins in body:
        if ins.mnemonic in BRANCH or ins.mnemonic in ("cmp","test"):
            marker = ""
            # detect backward jump (loop)
            if ins.mnemonic.startswith("j") and ins.op_str.startswith("0x"):
                try:
                    tgt = int(ins.op_str,16)
                    if tgt < ins.address: marker = "  <BACK/LOOP>"
                except: pass
            out.append(f"  +0x{ins.address-va:04X} {ins.mnemonic:<7} {ins.op_str}{marker}")
    return "\n".join(out)

def main():
    rows = loadrows()
    skels = [analyze(p) for p in rows]
    full = "\n\n".join(skels) + "\n"
    with open(os.path.join(EVDIR, "SKELETONS.txt"), "w", encoding="utf-8") as f:
        f.write(full)
    print(f"wrote SKELETONS.txt ({len(rows)} funcs, {len(full.splitlines())} lines)")

if __name__=="__main__": main()
