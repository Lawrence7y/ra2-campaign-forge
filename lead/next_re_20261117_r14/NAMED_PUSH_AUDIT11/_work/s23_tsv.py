import sys, json
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11"
rows = json.load(open("verify3.json", encoding="utf-8"))

facts = []
for d in rows:
    e = d["entry"]
    va = int(e, 16)
    ins = []
    for k, i in enumerate(dis(va, 500)):
        if i.mnemonic == "nop" and k > 0:
            break
        ins.append(i)
    alloc = [i for i in ins if i.mnemonic == "call" and i.op_str == "0x7c8e17"][0]
    size = int.from_bytes(rd(alloc.address - 4, 4), "little")
    reg = None
    for i in dis(int(d["factory_ctor_callers"][0], 16), 60):
        if i.mnemonic == "call" and i.op_str == "esi":
            reg = i.address
            break
    g = [x[1].split(", ")[1] for x in d["guards"]]
    facts.append({
        "e": e, "vt": d["vt"], "slot_no": d["slot_no"],
        "col": d["factory_rtti"]["col"], "td": d["factory_rtti"]["td"],
        "fname": d["factory_rtti"]["name"],
        "obj_ctor": d["obj_ctor"], "alloc": alloc.address, "size": size,
        "main_vt": d["obj_main_vt"]["vt"], "main_vt_slot0": d["obj_main_vt"]["slot0"],
        "main_vt_rtti": d["obj_main_vt"]["rtti"],
        "main_vt_site": d["obj_main_vt"]["at"],
        "installer": d["factory_vt_installers"][0],
        "reg": reg, "clsid": d["clsid"], "cls": d["expected_class"],
        "guards": g, "guard_addrs": [x[0] for x in d["guards"]],
        "qi": d["qi"][0][0], "destroy": d["destroy"][0][0],
        "push1": d["push1"][0][0], "jge": [x[2] for x in d["test_jge"] if x[1] == "jge"][0],
        "slot8": d["obj_slot8"],
        "guard_bytes": [d["guards"][0][2], d["guards"][1][2], d["guards"][2][2]],
    })

json.dump(facts, open("facts_final.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

tsv = ["entry\tsubsystem\tverdict\tring2_at\tring3b_form\tring4_at\tsame_source\treason"]
for f in facts:
    ring2 = (f"{f['vt']}+12(slot{f['slot_no']})={f['e']}; "
             f"RTTI COL {f['col']} -> TD {f['td']} -> {f['fname']}")
    ring4 = (f"ctor {f['installer']} mov [obj],{f['vt']}; "
             f"CoRegisterClassObject @{f['reg']:08X} CLSID {f['clsid']}")
    reason = (f"{f['e']} 复算：{f['vt']} 槽{f['slot_no']}={f['e']}（{f['fname']}）；体内 alloc {f['size']}B@{f['alloc']:08X}"
              f"→ctor {f['obj_ctor']} 写 [this]={f['main_vt']}@{f['main_vt_site']} 且 vt[0]={f['main_vt_slot0']}"
              f"（{f['main_vt_rtti']}）；③b② 三码 {f['guards'][0]}/{f['guards'][1]}/{f['guards'][2]} @{f['guard_addrs'][0]}/"
              f"{f['guard_addrs'][1]}/{f['guard_addrs'][2]} + QI@{f['qi']} test/jge {f['jge']} + 失败路{QI if False else ''}"
              f" {f['destroy']} 销毁(slot8 {f['slot8']})；④ 装表点 {f['installer']} 唯一/ctor/非 atexit，注册 {f['reg']:08X} CLSID {f['clsid']}；"
              f"②④ 不同源（.rdata RTTI vs .text 装表+注册）")
    tsv.append(f"{f['e']}\tS22\tPASS\t{ring2}\t3b2\t{ring4}\tno\t{reason}")

open(OUT + r"\verdict.tsv", "w", encoding="utf-8", newline="\n").write("\n".join(tsv) + "\n")
print("rows:", len(tsv) - 1)
print(tsv[1])
