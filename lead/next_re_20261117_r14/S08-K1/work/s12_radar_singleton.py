"""Find RadarClass/SidebarClass global instance address + radar surface format evidence."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import s08lib as L
b=L.Bin(); rows=L.load_atlas(); sw=L.load_sweep(os.path.join(os.path.dirname(__file__),'sweep.json'))
def callers(va): return [hex(x) for x in sw['calls'].get(va,[])]
print('callers 0x63F6B0 (radar ctor wrapper):',callers(0x63F6B0))
print('callers 0x652960 (radar ctor):',callers(0x652960))
# who calls Sidebar ctor region: dump caller site of 0x63F6B0
for c in sw['calls'].get(0x63F6B0,[]):
    site=int(c,16) if isinstance(c,str) else c
    print('--- context of call site %08X ---'%site)
    print(L.dump(b,site-0x20,0x40))
# scan for mov ecx,<imm> near radar Draw call 0x653100 chain, and SidebarClass global
# look for pattern: mov ecx, 0xXXXXXXXX before call 0x63F6B0
print()
print('## search .text for mov ecx,<imm32> immediately before call 0x63f6b0')
import capstone
m=L.md(True,True); data=b.secbuf('.text'); t=b.sec('.text')
ins=list(m.disasm(data,t['va']))
for i,x in enumerate(ins):
    if x.mnemonic=='call' and x.op_str=='0x63f6b0':
        for y in ins[max(0,i-6):i]:
            print('   %08X %s %s'%(y.address,y.mnemonic,y.op_str))
