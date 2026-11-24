import os
EV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE"
txt=open(os.path.join(EV,'W160_bss_writer_scan.stdout.txt'),encoding='utf-8').read()
print(txt[txt.find('0x887324'):txt.find('0x8B40CC')])
print(txt[txt.find('0x8B40CC'):])
