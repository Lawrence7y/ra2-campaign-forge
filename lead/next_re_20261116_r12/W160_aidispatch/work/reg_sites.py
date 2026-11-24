import os
EV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE"
lines=open(os.path.join(EV,'W160_whole_text_disasm.tsv'),encoding='utf-8').read().splitlines()
for lo,hi in [(0x482C10,0x482CA0),(0x4F9C70,0x4F9D50),(0x64DD90,0x64DDE0),(0x64EEA0,0x64EED0)]:
    print(f'\n--- {lo:08X}..{hi:08X} ---')
    for l in lines:
        a=int(l.split('\t')[0],16)
        if lo<=a<hi: print(l)
