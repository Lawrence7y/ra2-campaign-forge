"""S06-K3 corrected coverage_delta.tsv.
Only genuine evidence-backed rows. Entry names preserved (no self-invented names).
- 00485020 already [已证]: emit a semantics-refinement row (keeps true name).
- 00721A50 currently S06 [静态推断]: UPGRADE to [已证] (Value/Power INI load, byte-level).
  Keep coverage's class-attribution name 'TiberiumClass::slot25'; do not invent a class name.
"""
import os
COV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K3\coverage_delta.tsv"
cur={}
with open(COV,encoding='utf-8') as f:
    next(f)
    for ln in f:
        q=ln.rstrip('\n').split('\t')
        if len(q)>=5: cur[q[0].upper()]=(q[1],q[2],q[3],q[4])

rows=[]
def add(entry,name,sem,grade,ev):
    rows.append("\t".join([entry,'S06',name,sem,grade,ev]))

# 1) 0x485020 - true name preserved; already [已证]; semantics refinement only.
c=cur['00485020']
add('00485020', c[1],
    '[已证] cell ore value = [TiberiumClass+0xB8 Value from rules Value=] * (cell+0x11E density+1); 20 direct call sites / 7 caller funcs (k3 T4)',
    '[已证]', 'EVIDENCE/k3_t4_ore_calls.txt;EVIDENCE/k3_t4_final.txt;EVIDENCE/k3_t4_rtti_full.txt')

# 2) 0x721A50 - UPGRADE [静态推断] -> [已证]. Atlas strings prove Resource-type rule fields;
#    disasm proves Value->+0xB8 via CCINIClass::ReadInteger(key 0x8448EC='Value').
c=cur['00721A50']
assert c[0]=='S06', c
add('00721A50', c[1],
    '[已证] ore-type rule loader: reads INI [Resource]Type keys Spread/Growth/Value/Power/Color/Debris/Image; Value->+0xB8 via CCINIClass::ReadInteger at 0x721B0C (key 0x8448EC="Value")',
    '[已证]', 'EVIDENCE/k3_t4_final.txt#00721B0C;EVIDENCE/k3_t4_rtti_full.txt;EVIDENCE/k3_t4_ore_table.txt')

with open(OUT,'w',encoding='utf-8',newline='\n') as f:
    f.write('\n'.join(rows)+'\n')
print("wrote",OUT,"rows=",len(rows))
for r in rows:
    print(r.encode('ascii','replace').decode())
