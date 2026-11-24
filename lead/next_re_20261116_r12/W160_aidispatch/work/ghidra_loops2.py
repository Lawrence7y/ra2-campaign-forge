p=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE\W160_ghidra_extract.stdout.txt"
t=open(p,encoding='utf-8',errors='replace').read()
s=t.find('=== DECOMP 0055AFB0'); e=t.find('=== DECOMP 0055B8F0')
lines=t[s:e].splitlines()
for i,l in enumerate(lines):
    if '0x5c' in l.lower() or 'LAB_0055b5' in l or 'LAB_0055b6' in l:
        print(f'{i}: ' + '\n'.join(lines[max(0,i-2):min(len(lines),i+4)]))
        print('---')
