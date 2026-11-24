import json,re
CFG=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\cfg_features.json"))
x=CFG['006F8DF0']; body=x['body']
# find all object-field writes (non-stack, non-esp) and sentinel cmp (0xffff/-1)
print("OBJECT-WRITES (write to [reg+disp] where reg != esp):")
for o,m,op,hx in body:
    if 'ptr [' in op and ',' in op:
        dst=op.split(',')[0].strip()
        if m in ('mov','or','and','add','sub','xor','inc','dec') and 'esp' not in dst:
            print(f"  {o:>9} {m:<6} {op}")
print("\nSENTINEL cmps (-1/0xffff/0xffffffff):")
for o,m,op,hx in body:
    if m=='cmp' and ('-1' in op or '0xffff' in op):
        print(f"  {o:>9} {m:<6} {op}")
