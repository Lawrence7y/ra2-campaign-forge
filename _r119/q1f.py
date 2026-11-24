import sys, json
sys.path.insert(0, "/home/t628/projects/ra2-campaign-forge/_r119")
from _pe119 import *
TI = 0x7f9594
r = json.load(open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q1.json"))
det = r["q1"]["e"]["detail"]
# variant interpretations for the card's "+0x10 is a name" clause
v_bytes = [x for x in det if x["plus0x10_name"] is None]  # placeholder
for x in det:
    va = int(x["guid_va"], 16); op = PE_.va2off(va+0x10)
    x["plus0x10_first2bytes"] = BUF[op:op+2].hex(" ")
    x["plus0x10_bytes_start_with_dot_qA"] = BUF[op:op+2] == b".?"
    x["plus0x10_is_type_info_then_name_at_plus0x18"] = (u32(op) == TI and BUF[op+8:op+10] == b".?")
r["q1"]["e"]["interpretation_A_bytes_at_plus0x10_start_with_dot_qA"] = sum(1 for x in det if x["plus0x10_bytes_start_with_dot_qA"])
r["q1"]["e"]["interpretation_B_type_info_object_at_plus0x10_with_dot_qA_name_at_plus0x18"] = sum(1 for x in det if x["plus0x10_is_type_info_then_name_at_plus0x18"])
r["q1"]["e"]["note"] = ("In this image none of the 5 COM-shaped constants is followed at +0x10 by a raw name; 3 of them are followed at +0x10 by a type_info object whose decorated name sits at +0x18. Both numbers reported.")
# also: is 0x817bc0's +0x10 a name at all? no, it's 'FSGRYSMK1'
json.dump(r, open("/home/t628/projects/ra2-campaign-forge/_r119/x119exec_q1.json","w"), indent=1)
print("A:", r["q1"]["e"]["interpretation_A_bytes_at_plus0x10_start_with_dot_qA"],
      "B:", r["q1"]["e"]["interpretation_B_type_info_object_at_plus0x10_with_dot_qA_name_at_plus0x18"])
for x in det: print(x["guid_va"], x["plus0x10_dword"], x["plus0x10_first2bytes"], x["plus0x10_name"])
