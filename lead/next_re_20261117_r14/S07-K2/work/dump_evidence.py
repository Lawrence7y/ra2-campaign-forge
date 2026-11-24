"""Dump key function disassemblies to EVIDENCE/*.txt with func-entry tags."""
import sys, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
from audit_lib import Bin, md32, load_func_atlas
import bisect

ROOT = r"D:\Project\ra2-campaign-forge"
OUTDIR = os.path.join(ROOT, r"lead\next_re_20261117_r14\S07-K2\EVIDENCE")
b = Bin(); t = b.text
data = b.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
m = md32(skipdata=True)
atlas_rows,_ = load_func_atlas()
atlas_entries=[va for va,_ in atlas_rows]; atlas_map={va:r for va,r in atlas_rows}
def func_of(va):
    i=bisect.bisect_right(atlas_entries,va)-1
    if i<0: return None
    e=atlas_entries[i]; rec=atlas_map[e]
    try: sz=int(rec.get("size","0"))
    except: sz=0
    return (e,sz) if (sz and va<e+sz) else None

DUMPS = {
 "ev_layer_ctor_4A8630.txt": (0x4A8630, 0x50),
 "ev_layer_bound_4A8900.txt": (0x4A8900, 0x24),
 "ev_setlayer_4A9720.txt": (0x4A9720, 0x50),
 "ev_removefromlayer_4A9770.txt": (0x4A9770, 0x70),
 "ev_sort_551A30.txt": (0x551A30, 0x58),
 "ev_sortcaller_55DBC3.txt": (0x55DB90, 0x42),
 "ev_trav_rev_6D97D0.txt": (0x6D97D0, 0x145),
 "ev_trav_fwd_6D9920.txt": (0x6D9920, 0x130),
 "ev_trav_slice_6D9A50.txt": (0x6D9A50, 0xF5),
 "ev_slot65_43CEA0.txt": (0x43CEA0, 0x184),
 "ev_filters_482850.txt": (0x482850, 0x120),
 "ev_438BF0_set1.txt": (0x438BF0, 0x260),
}
for fn,(va,n) in DUMPS.items():
    out=[]
    out.append("; DISASM %s from %08X for 0x%X bytes; ImageBase 0x400000; capstone skipdata=True"%(fn,va,n))
    dd = b.read(va,n)
    for insn in m.disasm(dd,va):
        fr=func_of(insn.address)
        tag=""
        if fr and fr[0]==insn.address: tag="  <== FUNC entry size=%d"%fr[1]
        out.append("%08X  %-20s %-6s %s%s"%(insn.address,insn.bytes.hex(),insn.mnemonic,insn.op_str,tag))
    with open(os.path.join(OUTDIR,fn),"w",encoding="utf-8") as f:
        f.write("\n".join(out)+"\n")
    print("wrote",fn,len(out)-1,"insns")
