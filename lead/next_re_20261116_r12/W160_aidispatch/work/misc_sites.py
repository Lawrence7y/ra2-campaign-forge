import os, re
EV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE"
lines=open(os.path.join(EV,'W160_whole_text_disasm.tsv'),encoding='utf-8').read().splitlines()
D={int(l.split('\t')[0],16):l for l in lines}
for rng in [(0x55B660,0x55B670),(0x617630,0x617650),(0x61CC50,0x61CC65),(0x785120,0x785140),(0x55D840,0x55D850),(0x55E260,0x55E275),(0x6485C0,0x6485D2),(0x7E18FC,0x7E1938)]:
    print(f'--- {rng[0]:08X}..{rng[1]:08X} ---')
    for a in sorted(k for k in D if rng[0]<=k<rng[1]): print(D[a])
