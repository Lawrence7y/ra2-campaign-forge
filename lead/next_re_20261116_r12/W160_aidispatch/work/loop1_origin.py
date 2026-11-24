import os
EV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE"
lines=open(os.path.join(EV,'W160_whole_text_disasm.tsv'),encoding='utf-8').read().splitlines()
D={int(l.split('\t')[0],16):l for l in lines}
for a in range(0x55B470,0x55B510):
    if a in D: print(D[a])
