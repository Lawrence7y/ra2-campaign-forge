import json
hits=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\EVIDENCE\channelA_exact2.json'))
FAMG={'0x87f5d8':'F1', '0x89c668':'F1', '0x8874c0':'F2', '0x887568':'F3', '0x89de18':'F4', '0xa8ed40':'F4', '0xac4910':'F5', '0xb04bd0':'F6'}
print('=== exact call sites on container-family globals ===')
for h in hits:
    if h['g'] in FAMG:
        print(FAMG[h['g']],hex(h['call_site']),'slot',h['slot_div4'],'global',h['g'],'vptr_load',hex(h['vptr_load']),'ecx_load',hex(h['ecx_load']))
