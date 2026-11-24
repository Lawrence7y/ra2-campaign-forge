"""Find SidebarClass global singleton: callers of sidebar ctor 0x6A4E60 and frame-loop setup."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import s08lib as L
b=L.Bin(); rows=L.load_atlas(); sw=L.load_sweep(os.path.join(os.path.dirname(__file__),'sweep.json'))
def callers(va): return [hex(x) for x in sw['calls'].get(va,[])]
print('callers 0x6A4E60 (sidebar ctor):',callers(0x6A4E60))
for c in sw['calls'].get(0x6A4E60,[]):
    site=int(c,16) if isinstance(c,str) else c
    print('--- context of call site %08X ---'%site)
    print(L.dump(b,site-0x18,0x30))
# search attribute refs to common sidebar globals from docs: 0x87xxxx near radar
# scan for absolute refs of candidate 0x87F000..0x880000 in radar Draw 0x653100
print('## absolute globals referenced in 0x653100 body:')
import capstone
m=L.md(True,True)
data=b.read(0x653100,1588)
seen={}
for ins in m.disasm(data,0x653100):
    for op in ins.operands:
        if op.type==capstone.x86.X86_OP_MEM and op.mem.base==0 and op.mem.index==0:
            d=op.mem.disp&0xFFFFFFFF
            if 0x810000<=d<=0xB80000:
                seen[d]=seen.get(d,0)+1
for k in sorted(seen): print('  %08X x%d'%(k,seen[k]))
