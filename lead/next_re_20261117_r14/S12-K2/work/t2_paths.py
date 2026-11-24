"""T2: exhaust all paths that chain an object into a cell's +0xE4/+0xE8 lists.
Byte-channel sweep (capstone skipdata=True), independent of atlas.
Outputs: direct callers of worker/wrappers, every v73 [reg+0x124] call/jmp site
with preceding push-mode context, data-segment pointers to key funcs, full
disassembly of slot-73 implementations, and direct +0xE4/+0xE8 writers.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import capstone
from re_helper import Bin, disasm_range, fmt_insn, md, load_atlas, sweep_calls, EVID

b = Bin()
L = []
calls, jmps, stat = sweep_calls(b)
L.append("byte-sweep stat: %s" % stat)

def callers(t):
    return sorted(calls.get(t, []))

for t in (0x47E8A0, 0x47EA90, 0x5683C0, 0x5687F0, 0x43F180, 0x4D3780, 0x6F4A70, 0x71BFB0, 0x4151E0):
    cs = callers(t)
    L.append("CALLERS of %08X: n=%d  %s" % (t, len(cs), " ".join(hex(x) for x in cs)))

# v73 dispatch: call/jmp [reg+0x124]
L.append(""); L.append("="*88)
L.append("ALL call/jmp dword ptr [reg+0x124]  (vtable slot 73 = Building::SetOccupation)")
L.append("="*88)
m = md(skipdata=True)
t = b.sec(".text")
data = b.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
v73 = []
for ins in m.disasm(data, t["va"]):
    if ins.id == 0: continue
    if ins.mnemonic not in ("call","jmp"): continue
    for op in ins.operands:
        if op.type == capstone.x86.X86_OP_MEM and op.mem.disp == 0x124 and op.mem.base != 0:
            v73.append(ins.address)
            break
L.append("count=%d" % len(v73))
# show 12 insns before each, looking for push imm (mode)
for a in v73:
    L.append("-"*70)
    ctx = list(m.disasm(b.read(a-0x30,0x30), a-0x30))
    for ins in ctx:
        if ins.id: L.append(fmt_insn(ins))
    L.append(fmt_insn(next(i for i in m.disasm(b.read(a,8),a) if i.address==a)))

# data-segment pointers to key funcs
L.append(""); L.append("="*88); L.append("DATA-SEGMENT pointers to key funcs (4-byte LE)"); L.append("="*88)
targets = [0x47E8A0,0x47EA90,0x5683C0,0x5687F0,0x43F180,0x4D3780,0x7014A0]
for s in b.sections:
    if s["name"] not in (".rdata",".data"): continue
    buf = b.pe.__data__[s["raw"]:s["raw"]+s["rawsize"]]
    for tgt in targets:
        pat = tgt.to_bytes(4,"little")
        off = 0
        hits=[]
        while True:
            i = buf.find(pat, off)
            if i<0: break
            hits.append(s["va"]+i); off=i+1
        if hits: L.append("%s ptr->%08X at %s" % (s["name"],tgt," ".join(hex(x) for x in hits[:30])))

# full slot-73 implementations
for a,n,name in [(0x7014A0,1014,"TechnoClass::SetOwner slot73"),
                 (0x4D3780,138,"Unit/Inf/Aircraft slot73"),
                 (0x6F4A70,51,"TechnoClass base slot73")]:
    L.append(""); L.append("="*88); L.append("%s @ %08X size=%d"%(name,a,n)); L.append("="*88)
    for ins in disasm_range(b,a,a+n,skipdata=True): L.append(fmt_insn(ins))

# wrapper 0x5683C0: show only around its call to 0x47E8A0 plus entry
L.append(""); L.append("="*88); L.append("0x5683C0 wrapper: region around call 0x47E8A0"); L.append("="*88)
ins568 = disasm_range(b,0x5683C0,0x5683C0+1068,skipdata=True)
for idx,ins in enumerate(ins568):
    if ins.id and ins.mnemonic=="call" and ins.op_str.lower().endswith("0x47e8a0"):
        for x in ins568[max(0,idx-14):min(len(ins568),idx+8)]: L.append(fmt_insn(x))
        L.append("(call site %08X)"%ins.address)
        break

out = os.path.join(EVID,"t2_all_attach_paths.txt")
with open(out,"w",encoding="utf-8") as f: f.write("\n".join(L)+"\n")
print("wrote",out,"lines",len(L),"v73_count",len(v73))
