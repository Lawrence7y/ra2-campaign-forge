# -*- coding: utf-8 -*-
import sys, re, struct
sys.path.insert(0, __file__.rsplit('\\',1)[0])
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
TARGETS=['006D0F00','006D6070','006E1830','006E4790','006E47C0','006E6310','006EA3E0','006F1920','0070F120','00721270','00727AA0','0072DDB0','0072DEF0','00751590','00752460','00763610','00763690']
out=[]
print('SHA256',p.sha256())
print('=== S1 scalar delete destructor bounded scan ===')
print('entry\tfirst_ret\tbytes_to_ret\ttest_byte_esp8_1\tdelete_call\tret4\tverdict\tnote')
for hx in TARGETS:
    va=int(hx,16); ins=p.dis(va, 0x1000, True)
    txt='\n'.join(s for a,bb,s,i in ins)
    first=p.dis(va,0x1000,True)[-1][0] if ins else va
    nbytes=(first-va)+ (len(bytes.fromhex(ins[-1][1])) if ins else 0)
    tb=any(re.search(r'test byte ptr \[esp \+ 8\], 1',s) for a,bb,s,i in ins)
    dc=re.findall(r'call (0x[0-9a-f]+)',txt)
    # likely delete targets from import/CRT observed in binary; identify any call whose target function contains _delete pattern? initially broad call count
    ret4=any(s.split()[0] in ('ret','retn') and '4' in s for a,bb,s,i in ins)
    verdict='TRUE' if tb and ret4 and dc else 'FALSE'
    note=';'.join(dc[-4:])
    print(f'{hx}\t{first:08X}\t{nbytes}\t{tb}\t{dc}\t{ret4}\t{verdict}\t{note}')
    out.append((hx,ins))

print('\n=== bounded bodies (entry->first ret only) ===')
for hx,ins in out:
    print(f'---- {hx} ----')
    for a,bb,s,i in ins:
        print(f'{a:08X}  {bb:<20s} {s}')
