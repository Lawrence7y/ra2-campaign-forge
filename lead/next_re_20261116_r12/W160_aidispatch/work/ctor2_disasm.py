import os
EV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE"
lines=open(os.path.join(EV,'W160_whole_text_disasm.tsv'),encoding='utf-8').read().splitlines()
with open(os.path.join(EV,'W160_ctor2_disasm.txt'),'w',encoding='utf-8') as f:
    for lo,hi in [(0x4E7FA0,0x4E8030),(0x55B500,0x55B5A5),(0x55B510,0x55B5A5)]:
        f.write(f'\n--- {lo:08X}..{hi:08X} ---\n')
        for l in lines:
            a=int(l.split('\t')[0],16)
            if lo<=a<hi: f.write(l+'\n')
print(open(os.path.join(EV,'W160_ctor2_disasm.txt'),encoding='utf-8').read())
