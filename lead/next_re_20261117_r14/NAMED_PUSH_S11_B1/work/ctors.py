import os,sys,json,pickle
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from core import *

CALLS={}
for i in INSNS:
    if i.id==X86_INS_CALL and i.operands and i.operands[0].type==X86_OP_IMM:
        CALLS.setdefault(i.operands[0].imm & 0xFFFFFFFF,[]).append(i.address)
pickle.dump(CALLS, open('calls.pkl','wb'))
print('call targets:', len(CALLS))

for ea,name in ((0x004AF540,'Drive ctor'),(0x004B5AB0,'DropPod ctor'),(0x0054AC40,'Jumpjet ctor')):
    cs=CALLS.get(ea,[])
    print('\n%s %s direct_callers(%d): %s  atexit=%s' % (name,hx(ea),len(cs),[hx(c) for c in cs[:8]], is_atexit_registered(ea)))
    for c in cs[:2]:
        print('   ctx around %s' % hx(c))
        for i in dis(c-24, read_va(c-24, 36)):
            if c-24 <= i.address <= c+4:
                print('     %s %-14s %s' % (hx(i.address), i.bytes.hex(), i.mnemonic+' '+i.op_str))

print('\n== 4 entries direct callers ==')
for ea in (0x004AF720,0x004B62C0,0x004B6470,0x0054DC60):
    cs=CALLS.get(ea,[])
    print('  %s -> %d %s | atexit=%s' % (hx(ea),len(cs),[hx(c) for c in cs], is_atexit_registered(ea)))
