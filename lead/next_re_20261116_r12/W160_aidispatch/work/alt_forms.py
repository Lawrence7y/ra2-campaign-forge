"""W160 Q1: alternative AI-call forms. Source: whole .text linear sweep (skipdata=True)."""
import os, json, re
EV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE"
D={}
for l in open(os.path.join(EV,'W160_whole_text_disasm.tsv'),encoding='utf-8'):
    p=l.rstrip('\n').split('\t'); D[int(p[0],16)]=(p[1],p[2],p[3])
S=sorted(D)
def near(a,b): return S[__import__('bisect').bisect_left(S,a):S[__import__('bisect').bisect_left(S,b)]]
# 1) every 'add REG,0x5c' followed within 8 instructions by call dword ptr [same REG]
adds=[]
for a,(mn,ops,raw) in D.items():
    m=re.fullmatch(r'add (e?[a-z]{2}), 0x5c',ops)
    if not m: continue
    reg=m.group(1)
    seq=near(a,a+40)
    calls=[(x,D[x][1],D[x][2]) for x in seq if D[x][0]=='call' and re.fullmatch(r'dword ptr \['+reg+r'\]',D[x][1].replace('  ',' '))]
    if calls: adds.append((hex(a),ops,calls))
print('add-reg-0x5c followed by call [reg] count:',len(adds))
for x in adds[:20]: print(x)
# 2) all call dword ptr [reg + reg*scale + disp] with scale 2/4/8 (dispatch tables)
idx=[]
for a,(mn,ops,raw) in D.items():
    if mn!='call': continue
    m=re.search(r'dword ptr \[(\w+) \+ (\w+)\*(2|4|8)(?: \+ (0x[0-9a-f]+|\d+))?\]',ops)
    if m: idx.append((a,ops))
print('\ncall [base+index*scale+disp] count:',len(idx))
for a,ops in idx[:30]: print(hex(a),ops)
# 3) raw FF /2 SIB with index != none (modrm=0x54/0x94 etc.) all disp values
# 4) all instruction lines containing 0x5c in memory operand (any instr) count by mnemonic
from collections import Counter
c=Counter()
for a,(mn,ops,raw) in D.items():
    if re.search(r'\+ 0x5c\]',ops): c[mn]+=1
print('\nall instructions with +0x5c] mem operand:',c)
