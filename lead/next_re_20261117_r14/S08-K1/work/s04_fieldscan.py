"""Scan all .text instructions that write/read cell fog fields +0x120/+0x121/+0x12C/+0x130/+0x134/+0x13C/+0x140.
Attribute each site to atlas function (interval containment, NOT entry_at_or_before)."""
import sys, os, collections
sys.path.insert(0, os.path.dirname(__file__))
import s08lib as L
import capstone
b=L.Bin(); rows=L.load_atlas(); m=L.md(True,True)
t=b.sec('.text'); data=b.secbuf('.text')
FIELDS={0x120,0x121,0x12c,0x130,0x134,0x13c,0x140}
hits=[]
for ins in m.disasm(data,t['va']):
    if ins.id==0: continue
    for oi,op in enumerate(ins.operands):
        if op.type==capstone.x86.X86_OP_MEM and op.mem.disp in FIELDS:
            if op.mem.base==0: continue
            hits.append(dict(va=ins.address, field=op.mem.disp, opidx=oi,
                mnem=ins.mnemonic, ops=ins.op_str, bytes=ins.bytes.hex()))
            break
WRITEMN={'mov','or','and','add','sub','inc','dec','xor','shl','shr','not','movzx','movsx','bsf','bsr','neg'}
for h in hits:
    h['role']='write' if (h['opidx']==0 and h['mnem'] in WRITEMN) else 'read'
    e=L.atlas_find(rows,h['va'])
    h['fn']=('%08X'%e['entry']) if e else 'NOATLAS'
    h['fn_size']=e['size'] if e else 0
byfield=collections.defaultdict(list)
for h in hits: byfield[h['field']].append(h)
for f in sorted(FIELDS):
    hs=byfield[f]
    w=[h for h in hs if h['role']=='write']
    r=[h for h in hs if h['role']=='read']
    fns=collections.Counter(h['fn'] for h in w)
    print('='*90)
    print('FIELD +0x%X: %d total, %d writes in %d fns, %d reads'%(f,len(hs),len(w),len(fns),len(r)))
    print('  write fns:',dict(fns))
    for h in w:
        print('  W %08X fn=%s  %s %s | %s'%(h['va'],h['fn'],h['mnem'],h['ops'],h['bytes']))
