p=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE\W160_ghidra_extract.stdout.txt"
t=open(p,encoding='utf-8',errors='replace').read()
# decompiled function ends at next '=== DECOMP 0055B8F0'
s=t.find('=== DECOMP 0055AFB0')
e=t.find('=== DECOMP 0055B8F0')
d=t[s:e]
lines=d.splitlines()
print('lines',len(lines))
for i,l in enumerate(lines):
    if any(k in l for k in ['0x5c','0x87f778','DAT_0087f778','FUN_0055bb40','puVar8','local_18','0x8a020c','0xa83e','0xa802','LAB_0055b6']):
        print('\n'.join(lines[max(0,i-4):min(len(lines),i+6)]))
        print('---')
