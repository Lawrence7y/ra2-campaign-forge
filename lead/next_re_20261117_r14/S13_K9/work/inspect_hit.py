import json,sys
d=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\EVIDENCE\channelA_raw.json'))
print('the single hit:',d['hits'][0])
# examine context around it
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
from capstone import *
site=d['hits'][0]['call_site']
md=Cs(CS_ARCH_X86,CS_MODE_32)
for i in md.disasm(rd(site-24,48),site-24):
    print(hex(i.address),i.mnemonic,i.op_str)
