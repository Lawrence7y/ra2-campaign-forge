
import sys, re, struct
sys.stdout.reconfigure(encoding='utf-8')
import k5_lib as K
atl=K.atl_map()
targets=[0x7C060,0x480CB0,0x4818E0,0x71C730,0x722440,0x722F00,0x4839F0]
ANCH={0x5FDD20:'typelookup',0x487190:'IncreaseTib',0x4838E0:'canSpread',0x483710:'grow1',0x483780:'grow3',0x65C7E0:'mapget',0x5657A0:'cellget',0x7C8E17:'new'}
for va in targets:
    a=atl.get('%08X'%va); sz=int(a['size']) if a else 512
    ins=K.dis(va,sz)
    calls=[]
    for i in ins:
        if i.mnemonic=='call' and i.op_str.startswith('0x'):
            t=int(i.op_str,16)
            if t in ANCH: calls.append((hex(i.address),ANCH[t]))
    consts=[hex(i.address) for i in ins if '0x7e3810' in i.op_str.lower()]
    fields=sorted(set('0x'+hx for i in ins for hx in re.findall(r'\[[^]]+0x([0-9a-f]+)\]',i.op_str.lower()) if int(hx,16) in (0x44,0x11c,0x11e,0xa0,0xb0,0xe4)))
    print("FUNC 0x%08X sz=%d calls=%s const7E3810=%s fields=%s"%(va,sz,calls,consts,fields))
    # print disasm around any grow call
    for i in ins:
        if i.mnemonic=='call' and i.op_str.startswith('0x') and int(i.op_str,16) in (0x483710,0x483780,0x4838E0,0x487190):
            idx=ins.index(i)
            print("  --- around call @%s ---"%hex(i.address))
            for j in ins[max(0,idx-6):idx+4]: print("   ",K.fmt(j))
    print()
