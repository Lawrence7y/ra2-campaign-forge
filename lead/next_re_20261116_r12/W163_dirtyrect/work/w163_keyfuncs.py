"""W163: disasm key dirty-rect functions with loop/backedge detection and call list.
Independent of atlas for callee discovery (full byte sweep).
"""
import sys, os, json, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w163_lib as w
import capstone

FUNCS = [0x6D1810, 0x6D2790, 0x6D2B60, 0x6D2DE0, 0x6D3040, 0x6D3290,
         0x6D3470, 0x6D3660, 0x6D3870, 0x6D3AC0, 0x6D3D10, 0x6DA980]

JCC = {"jmp","je","jne","jz","jnz","ja","jae","jb","jbe","jg","jge","jl","jle",
       "jc","jnc","jo","jno","js","jns","jp","jnp","loop","loope","loopne"}

def main():
    b = w.Bin()
    rows,hdr = w.load_atlas()
    atlas = {va:rec for va,rec in rows}
    m = w.md32(skipdata=True)
    # full-byte call map
    calls, jmps, stats = w.sweep_full_text(b)
    entries = [va for va,_ in rows]
    report = {}
    for f in FUNCS:
        rec = atlas.get(f)
        if rec is None:
            print("FUNC %08X NOT_IN_ATLAS" % f); continue
        size = int(rec["size"],10)
        data = b.read(f, size)
        insns = list(m.disasm(data, f))
        back = []
        calls_here = []
        memops = []
        for insn in insns:
            if insn.id==0: continue
            if insn.mnemonic in JCC:
                for op in insn.operands:
                    if op.type==capstone.x86.X86_OP_IMM and op.imm <= insn.address:
                        back.append((insn.address, op.imm, insn.mnemonic))
            if insn.mnemonic=="call":
                for op in insn.operands:
                    if op.type==capstone.x86.X86_OP_IMM:
                        calls_here.append((insn.address, op.imm))
            for op in insn.operands:
                if op.type==capstone.x86.X86_OP_MEM and (op.mem.disp & 0xFFFFFFFF) in (0xB0CE78,0xB0CE7C,0xB0CE80,0xB0CE84,0xB0CE85,0xB0CE88,0xB0CE8C):
                    memops.append((insn.address, "%s %s"%(insn.mnemonic,insn.op_str)))
        real = [i for i in insns if i.id!=0]
        print("=== FUNC %08X size=%d insns=%d backedges=%d calls=%d container_refs=%d ===" %
              (f,size,len(real),len(back),len(calls_here),len(memops)))
        print("  backedges:", [(hex(a),hex(t),mn) for a,t,mn in back])
        print("  calls:", [(hex(a),hex(t)) for a,t in calls_here])
        report["%08X"%f] = dict(size=size, n_insn=len(real),
                                backedges=back, calls=calls_here,
                                container_refs=memops)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","EVIDENCE","keyfuncs_summary.json"),"w",encoding="utf-8") as fo:
        json.dump(report,fo,indent=1)

if __name__=="__main__":
    main()
