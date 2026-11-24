"""Final: enumerate direct call targets in House::Update (0x4F8440, atlas hole) and main tick 0x55E160."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import s08lib as L
b=L.Bin(); rows=L.load_atlas(); m=L.md(True,True)
def calltargets(start, end):
    data=b.read(start,end-start); out=[]
    for ins in m.disasm(data,start):
        if ins.id==0: continue
        if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
            out.append((ins.address,int(ins.op_str,16)))
    return out
print('## House::Update-ish 0x4F8440..0x4F8600 calls:')
for site,tgt in calltargets(0x4F8440,0x4F8600):
    e=L.atlas_find(rows,tgt)
    nm=('%08X'%(e['entry'])) if e else 'NOATLAS'
    print('  %08X -> %08X (%s)'%(site,tgt,nm))
print()
print('## main tick 0x55E160..0x55E400 calls (first 60):')
for i,(site,tgt) in enumerate(calltargets(0x55E160,0x55E400)):
    if i>=60: break
    e=L.atlas_find(rows,tgt)
    nm=('%08X'%(e['entry'])) if e else 'NOATLAS'
    print('  %08X -> %08X (%s)'%(site,tgt,nm))
print()
print('## 0x508DF0 (before UpdateSpySat in House::Update):')
e=L.atlas_find(rows,0x508DF0)
print('  who',('%08X sz=%d'%(e['entry'],e['size'])) if e else 'NOATLAS')
print(L.dump(b,0x508DF0,0x40))
