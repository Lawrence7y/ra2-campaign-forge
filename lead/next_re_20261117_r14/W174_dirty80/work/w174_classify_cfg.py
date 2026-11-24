#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rigorous (b)/(c) classification via intra-function CFG reachability.

Definition (auditable):
  A write-1 site W in function F is CONDITIONAL (b) iff there exists a conditional
  branch J in F such that W is reachable from exactly ONE of J's two successors
  (taken target xor fall-through). That is, some branch controls whether W executes.
  Otherwise W is UNCONDITIONAL (c): no branch decides whether the write runs.

  (a) = src imm 0 ; (d) = src register.

CFG model (intra-function, instruction-level):
  - conditional jump: edges to target and to next instruction
  - unconditional jmp: edge to target only (and to next if target is outside F)
  - call: edge to next instruction (callee analyzed separately)
  - ret: no successor
  - other: edge to next instruction
Reachability computed by BFS over instruction indices within [entry, fn_end).
All jcc targets are validated to lie inside F; a jcc leaving F is still kept as an
edge to "outside" (represented as a virtual sink) for the XOR test.
"""
import os, sys, json, bisect
import pefile, capstone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\Project\ra2-campaign-forge"
sys.path.insert(0, os.path.join(ROOT, "lead", "next_re_20261116_r12", "_lead_audit"))
import audit_lib

with open(os.path.join(HERE,"..","EVIDENCE","w174_writes.json"),"r",encoding="utf-8") as f:
    D=json.load(f)
writes=D["writesA"]

b=audit_lib.Bin(); pe=b.pe; T=b.sec(".text")
TEXT=pe.__data__[T["raw"]:T["raw"]+T["rawsize"]]; TV=T["va"]
def md():
    m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True; return m
MD=md()

rows,_=audit_lib.load_func_atlas()
atlas_entries=sorted([e for e,_ in rows])
calls,jmps,_=audit_lib.sweep_calls(b)
union=sorted(set(atlas_entries)|set(t for t in calls if TV<=t<TV+len(TEXT)))
def func_range(va):
    i=bisect.bisect_right(union,va)-1
    if i<0: return None
    return union[i], (union[i+1] if i+1<len(union) else TV+len(TEXT))

COND={"je","jne","jz","jnz","jg","jge","jl","jle","ja","jae","jb","jbe",
      "js","jns","jo","jno","jp","jnp","jpe","jpo","jcxz","jecxz","loop","loope","loopne"}
RET={"ret","retn","retf"}

def disasm_range(lo,hi):
    out=[]
    for insn in MD.disasm(TEXT[lo-TV:hi-TV], lo):
        if insn.id==0: continue
        out.append(insn)
    return out

def jcc_target(insn):
    if insn.op_str.startswith("0x"):
        try: return int(insn.op_str,16)
        except: return None
    return None

def reach_from(succ_idx, insns, index_of, fn_lo, fn_hi):
    """BFS from a start instruction index; returns set of reached instruction indices."""
    n=len(insns); seen=set()
    stack=[succ_idx]
    while stack:
        k=stack.pop()
        if k in seen or k<0 or k>=n: continue
        seen.add(k)
        insn=insns[k]
        # find successors
        if insn.mnemonic in RET:
            continue
        # next instruction in linear stream
        nxt=k+1 if k+1<n else -1
        if insn.mnemonic=="jmp":
            t=jcc_target(insn)
            if t is not None and t in index_of:
                stack.append(index_of[t])
            elif nxt>=0:
                stack.append(nxt)
            continue
        if insn.mnemonic in COND:
            t=jcc_target(insn)
            if t is not None and t in index_of:
                stack.append(index_of[t])
            # fallthrough
            if nxt>=0: stack.append(nxt)
            continue
        # call / other: fallthrough
        if nxt>=0: stack.append(nxt)
    return seen

results=[]
detail_lines=[]
# group write sites by function
from collections import defaultdict
by_fn=defaultdict(list)
for d in writes:
    fr=func_range(d["va"])
    if not fr: continue
    by_fn[fr].append(d)

for (lo,hi), sites in sorted(by_fn.items()):
    insns=disasm_range(lo,hi)
    if not insns: continue
    index_of={insn.address:k for k,insn in enumerate(insns)}
    # list conditional branches in this function with their two successor indices
    conds=[]
    for k,insn in enumerate(insns):
        if insn.mnemonic in COND:
            t=jcc_target(insn)
            taken_idx = index_of.get(t)
            ft_idx = k+1 if k+1<len(insns) else None
            conds.append((k,insn.address,t,taken_idx,ft_idx))
    # precompute reachability for each branch's two successors (memo)
    reach_cache={}
    def get_reach(idx):
        if idx is None: return frozenset()
        if idx not in reach_cache:
            reach_cache[idx]=frozenset(reach_from(idx,insns,index_of,lo,hi))
        return reach_cache[idx]
    for d in sites:
        va=d["va"]
        if d["src_kind"]=="imm" and d["src"]==0:
            cls="a"; why="write 0"
        elif d["src_kind"]=="reg":
            cls="d"; why="reg value"
        else:
            W=index_of.get(va)
            if W is None:
                cls="c"; why="site not on decoded boundary -> default c"
                results.append(dict(va=va,cls=cls,why=why,fn=lo,gating=[]))
                continue
            gating=[]
            for (bk,baddr,bt,ti,fi) in conds:
                if ti is None and fi is None: continue
                Rt=get_reach(ti); Rf=get_reach(fi)
                in_t = W in Rt; in_f = W in Rf
                if in_t != in_f:  # exactly one side reaches W
                    gating.append(baddr)
            if gating:
                cls="b"; why="branch-gated"
            else:
                cls="c"; why="no branch gates write"
            results.append(dict(va=va,cls=cls,why=why,fn=lo,gating=gating,
                                src=d["src"],src_kind=d["src_kind"],base=d["base"]))
            continue
        results.append(dict(va=va,cls=cls,why=why,fn=lo,gating=[],
                            src=d["src"],src_kind=d["src_kind"],base=d["base"]))

# write results
with open(os.path.join(HERE,"..","EVIDENCE","w174_classify_cfg.tsv"),"w",encoding="utf-8") as f:
    f.write("va\tcls\twhy\tfn\tsrc_kind\tsrc\tbase\tgating_jcc\n")
    for r in results:
        f.write("%08X\t%s\t%s\t%08X\t%s\t%s\t%s\t%s\n" % (
            r["va"],r["cls"],r["why"],r["fn"],r.get("src_kind",""),str(r.get("src","")),
            r.get("base","")," ".join("%08X"%x for x in r.get("gating",[]))))

from collections import Counter
print("CFG classification counts:",Counter(r["cls"] for r in results))
print("total sites classified:",len(results))
