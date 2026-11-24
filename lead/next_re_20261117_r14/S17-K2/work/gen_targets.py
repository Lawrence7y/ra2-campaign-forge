#!/usr/bin/env python3
"""S17-K2: regenerate TARGETS.tsv with evidence approach/result filled in.
Columns: entry | 现 name | 现 grade | 现语义 | 缺什么 | 我打算怎么取证（本卡实际取证结果）
"""
import csv, re, os, json

CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-K2"
with open(os.path.join(CARD,"work","s17_rows.json"),encoding="utf-8") as f: rows=json.load(f)

def is_named(n):
    n=(n or "").strip()
    if not n: return False
    if re.fullmatch(r"sub_[0-9A-Fa-f]{8}(?:_\d+)?",n): return False
    if n.lower().startswith("sub_") and re.fullmatch(r"sub_[0-9a-fA-F]{8}.*",n): return False
    return True

# evidence approach per target entry (from actual work)
EV = {
 "0041D6E0":"vtable slot13=Save slot (RTTI AirstrikeClass vt 7E29A8) + body call AbstractClass::Save@410410 -> named AirstrikeClass::Save / [已证]",
 "0043A5D0":"vtable slot13=Save slot (RTTI NeuronClass vt 7E3DF0) + body call AbstractClass::Save@410410 -> named NeuronClass::Save / [已证]",
 "004B6BB0":"body loop call Here_I_Am@6CF240 on &[this+0x14+4i] -> named Swizzle_RegisterPointerArray / [已证]",
 "0067C690":"IAT ole32!OleLoadFromStream@7E15F8 + IStream::Read u32 count -> named Load_COM_ObjectVector / [已证]",
 "0055AAC0":"IStream::Read + Here_I_Am3@6CF2C0 + Here_I_Am@6CF240 in body -> named Load_SwizzledObject / [静态推断]",
 "00539AE0":"repeated IStream::Read via [vptr+0xC] to 0xA9FAB4/0x827FC0/0x827FC4 -> named Load_StreamFields / [静态推断]",
 "00431B80":"RTTI BufferIOFileClass vptr 7E3A2C set + free [+0x30] -> named BufferIOFileClass::~BufferIOFileClass / [静态推断]",
 "004068E0":"bytes c3 90.. = 1-instr ret stub; no S17 semantics evidence -> keep sub_ [静态推断]; explicitly NOT renamed (no fabricated name)",
 "0040E340":"body = generic doubly-linked list node insert; no S17-specific evidence -> keep sub_ [静态推断]",
 "00427940":"body reads ObjectClass fields [+0x35e]/[+0x22c] over global list; no S17 primitive -> keep sub_ [静态推断]",
 "0042E410":"body = 4-dword struct constructor ret 0x10; no S17 evidence -> keep sub_ [静态推断]",
 "00431B80":"RTTI BufferIOFileClass dtor (see above)",
 "00433CF0":"body parses word array from [ecx+0x1c]; no IStream/Ole/HereIAm -> keep sub_ [静态推断]",
 "004355B0":"body = 3-byte setter ret 0xC; no S17 evidence -> keep sub_ [静态推断]",
 "0043AE50":"body = free [+0] + zero 3 fields; no S17-specific evidence -> keep sub_ [静态推断]",
 "0049F740":"strings COPYPROTECTION + MapViewOfFileEx; misclassified S17 -> keep sub_ [未证]; see DISAGREE",
 "0049F8B0":"strings COPYPROTECTION/Shutdown + UnmapViewOfFile/RegOpenKeyExA(WChat\\SysID); misclassified S17 -> keep sub_ [未证]; see DISAGREE",
 "004B6BB0":"done",
 "00539AE0":"done",
 "0055AAC0":"done",
 "0067C690":"done",
 "00773450":"RTTI WebBrowser ctor + 'Instantiating embedded WebBrowser'; misclassified S17 -> keep sub_ [未证]; see DISAGREE",
}

out=os.path.join(CARD,"TARGETS.tsv")
with open(out,"w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["entry","in_atlas","现name","现grade","现语义","named?","缺什么","我打算怎么取证（本卡实际取证结果）"])
    # atlas first then outside, sorted
    rows_sorted=sorted([r for r in rows if r["in_atlas"]],key=lambda x:x["entry"])+sorted([r for r in rows if not r["in_atlas"]],key=lambda x:x["entry"])
    for r in rows_sorted:
        e=r["entry"].strip().upper()
        nm=is_named(r["name"])
        gap=[]
        if not nm: gap.append("name")
        if r["grade"]!="[已证]": gap.append("proof:"+r["grade"])
        if not r["sem"]: gap.append("sem")
        approach=EV.get(e,"已有名+已证，本卡复核一致（无需改动）") if (nm and r["grade"]=="[已证]") else EV.get(e,"弱信号/已有名：本卡未改；见 UNKNOWNS")
        w.writerow([e,"Y" if r["in_atlas"] else "N",r["name"],r["grade"],r["sem"],"Y" if nm else "N",
                    ";".join(gap) if gap else "OK",approach])
print("wrote TARGETS.tsv rows=",len(rows))
