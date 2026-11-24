import os
EV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE"
lines=open(os.path.join(EV,'W160_whole_text_disasm.tsv'),encoding='utf-8').read().splitlines()
for lo,hi in [(0x55B880,0x55B8F0),(0x55BAA0,0x55BAE0),(0x55BAE0,0x55BB20),(0x55BB40,0x55BBA0)]:
    print(f'\n--- {lo:08X}..{hi:08X} ---')
    for l in lines:
        a=int(l.split('\t')[0],16)
        if lo<=a<hi: print(l)
