import sys, json
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

rows = json.load(open("verify3.json", encoding="utf-8"))
print("### alloc -> ctor wiring per row")
for d in rows:
    va = int(d["entry"], 16)
    ins = []
    for k, i in enumerate(dis(va, 500)):
        if i.mnemonic == "nop" and k > 0:
            break
        ins.append(i)
    # find alloc call (0x7c8e17) and ctor call
    alloc = [i for i in ins if i.mnemonic == "call" and i.op_str == "0x7c8e17"]
    ctor = [i for i in ins if i.mnemonic == "call" and i.op_str.startswith("0x")
            and i.op_str != "0x7c8e17"][:1]
    a = alloc[0].address if alloc else None
    c = ctor[0].address if ctor else None
    seg = [i for i in ins if a is not None and a <= i.address <= (c or 0)]
    print(f"  {d['entry']} alloc@{a:08X} size_bytes={hexs(a-5,5)} ctor@{c:08X} "
          f"chain={[ (i.mnemonic+' '+i.op_str) for i in seg ]}")
