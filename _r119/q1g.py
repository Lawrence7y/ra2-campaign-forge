import sys, json
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
ds = PE_.sec_by_name(".data")
o, end = ds["raw"], ds["raw"]+ds["rawsize"]
card, true_ = [], []
while o+16 <= end:
    d = [u32(o+4*i) for i in range(4)]
    if d[1]==0 and (d[2] & 0xFFFF)==0xC000 and d[3]==0x46000000: card.append(ds["va"]+(o-ds["raw"]))
    if d[1]==0 and d[2]==0x000000C0 and d[3]==0x46000000: true_.append(ds["va"]+(o-ds["raw"]))
    o += 4
r = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q1.json"))
r["q1"]["e"]["card_literal_variant_count_in_data"] = len(card)
r["q1"]["e"]["card_literal_variant_addrs"] = [hex(v) for v in card]
r["q1"]["e"]["true_shape_count_in_data"] = len(true_)
json.dump(r, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q1.json","w"), indent=1)
print("card-literal in .data:", len(card), [hex(v) for v in card])
print("true shape in .data:", len(true_), [hex(v) for v in true_])
