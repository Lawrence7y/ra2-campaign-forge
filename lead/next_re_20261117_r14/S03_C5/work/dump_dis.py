"""Self-written function extent (CFG-based, NOT depending on function_atlas.tsv)
and disassembly dumper with entry-relative offsets. capstone skipdata=True.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import common as C

ENTRIES = [
 "00431F10","00431F70","00432050","004322A0","004325C0","00473AE0","00473B10",
 "00473C00","00473CE0","00473FC0","0047AAB0","0047AE10","0047AF10","0055C7C0",
 "00631D30","0065CB50","0065CCA0","0065CCE0","0065CDD0","0065CF00","0065D0D0",
 "0065D190","0065D1F0","0065D240",
]

# atlas_size from classification.tsv as a cap ceiling; extent computed by CFG linear sweep until ret chain
ATLAS_SIZE = {
 "00431F10":0x1c0,"00431F70":0x60,"00432050":0x50,"004322A0":0x60,"004325C0":0x1d0,
 "00473AE0":0x130,"00473B10":0x2b0,"00473C00":0x200,"00473CE0":0x360,"00473FC0":0x90,
 "0047AAB0":0x40,"0047AE10":0x100,"0047AF10":0x1b0,"0055C7C0":0x110,"00631D30":0xb0,
 "0065CB50":0x1d0,"0065CCA0":0x90,"0065CCE0":0x1a0,"0065CDD0":0x140,"0065CF00":0x220,
 "0065D0D0":0x60,"0065D190":0x1c0,"0065D1F0":0x30,"0065D240":0x30,
}

def linear_extent(entry, cap_bytes):
    """Disassemble linearly from entry; end at first `ret` (or ret imm) after which a nop/int3/other function prologue follows.
       Simplified: use last ret before cap where next insn alignment/prologue suggests boundary. We keep the maximal run of
       instructions up to cap_bytes, recording ret positions; extent = last ret position end within cap that is followed by padding/prologue.
    """
    insns = []
    last_ret_end = None
    for insn in C.disasm_va(entry, cap_bytes):
        insns.append(insn)
        if insn.mnemonic in ("ret","retf") or insn.mnemonic.startswith("ret "):
            # look ahead: if next bytes are padding (00/CC) or far — accept as candidate end
            last_ret_end = insn.address + insn.size
        if insn.address + insn.size - entry >= cap_bytes:
            break
    return insns, last_ret_end

os.makedirs(os.path.join(os.path.dirname(__file__), "..", "EVIDENCE", "dis"), exist_ok=True)
meta = {}
for e in ENTRIES:
    entry = int(e,16)
    cap = ATLAS_SIZE[e]
    insns, last_ret_end = linear_extent(entry, cap)
    # dump with entry-relative offset
    lines = []
    for insn in insns:
        off = insn.address - entry
        b = insn.bytes.hex()
        lines.append("+%04X  %08X  %-10s %-40s  ; %s" % (off, insn.address, insn.mnemonic, insn.op_str, b))
    txt = "\n".join(lines)
    with open(os.path.join(os.path.dirname(__file__),"..","EVIDENCE","dis",e+".txt"),"w",encoding="utf-8") as f:
        f.write("; entry %s  cap=0x%x  insn_count=%d  last_ret_end=%s\n" % (
            e, cap, len(insns), ("0x%x"%last_ret_end) if last_ret_end else None))
        f.write(txt+"\n")
    # count jcc / calls / rets / switch markers
    jcc = sum(1 for i in insns if i.mnemonic.startswith("j") and i.mnemonic!="jmp")
    jmp = sum(1 for i in insns if i.mnemonic=="jmp")
    calls = sum(1 for i in insns if i.mnemonic=="call")
    rets = sum(1 for i in insns if i.mnemonic.startswith("ret"))
    meta[e] = {"insn_count":len(insns),"jcc":jcc,"jmp":jmp,"calls":calls,"rets":rets,
               "last_off":(insns[-1].address-entry) if insns else None}

with open(os.path.join(os.path.dirname(__file__),"..","EVIDENCE","dis","_meta.json"),"w",encoding="utf-8") as f:
    json.dump(meta,f,indent=2)
print("entry insn jcc jmp call ret last_off")
for e in ENTRIES:
    m=meta[e]
    print("%s %4d %3d %3d %3d %3d 0x%X"%(e,m["insn_count"],m["jcc"],m["jmp"],m["calls"],m["rets"],m["last_off"]))
