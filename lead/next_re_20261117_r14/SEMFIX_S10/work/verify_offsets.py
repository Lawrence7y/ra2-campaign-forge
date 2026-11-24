import json, re, os
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_S10\EVIDENCE"
D = json.load(open(os.path.join(OUT,"DISASM_25.json"),encoding="utf-8"))

# tokens I intend to cite for each entry (absolute addresses + struct offsets)
tokens = {
"0045A560":["0x45A5AE","0x7c8e17","0x7c8b3d","0x4","0x8","0xc","0xd","0x10"],
"0045A610":["0x45A623","0x45A62F","0x10","0x4"],
"004D4200":["0x4D4217","0x4D422A","0x4D4231","0x4D4242","0x5a4","0x674","0xb4","0x484"],
"004D4280":["0x4D42B4","0x4D42BD","0x4D4B04","0x4D451B","0x4D477A"],
"004D4B20":["0x4D4B38","0x4D4B52","0x70d0d0","0x65c7e0","0x2c","0x2b4","0x480","0x484"],
"004D4CB0":["0x4D4CC8","0x4D4CE2","0x4D4D0D","0x4D4D26","0x4D4D39","0x4D4D86"],
"004D4DC0":["0x390","0x1c8","0x703590","0x5657a0","0x480","0x68e"],
"004D5070":["0x4D5118"],
"004D5350":["0x6d4","0x39c","0x2c","0xec3"],
"004D6AA0":["0x4D6F7A"],
"004D9290":["0x4D93B9"],
"004DA2C0":["0x4DA2FF","0x4DA2E6","0xbc"],
"004DA530":["0x5c"],
"004DDF90":["0x4DDFDB","0x4DDFA9","0x53c","0x1e8","0x1ec","0xbc"],
"0051F3E0":["0x6c0","0xec2","0x70d0d0","0x2b4","0x2c","0x520","0x1577","0x1701","0x480"],
"005B2FD0":["0x5B2FE9","0x5B302A","0xac","0xb4","0xb8","0xbc","0xc0","0xc4","0xc8","0xcc","0xd0"],
"005B3060":["0x5B34E8"],
"005B3570":["0x5B35CC","0xa8ed84","0xb4","0xac","0xc8","0xcc","0xd0"],
"005B35E0":["0x200","0x1ec","0xb4","0xb8"],
"005B3650":["0xb4","0xb0","0xac"],
"005B36B0":["0xb0","0xac","0xb8"],
"006B1850":["0x6B189E"],
"006B1900":["0x6B191F","0x10"],
"006B8660":["0x6B86AE"],
"006B8710":["0x6B872F","0x10"],
}

def body_text(entry):
    ins = D.get(entry,[])
    return "\n".join((i["a"]+" "+i["b"]+" "+i["m"]+" "+i["o"]) for i in ins)

def has_hex(text, tok):
    # match tok hex value not followed by another hex digit
    v = tok.lower().lstrip("0x")
    # strip leading zeros keep at least 1
    v = v or "0"
    # normalize: remove leading zeros but keep last char
    v2 = v.lstrip("0") or "0"
    pat = re.compile(r"0x0*"+re.escape(v2)+r"(?![0-9a-f])", re.I)
    return bool(pat.search(text))

hits=miss=0
misses=[]
for entry, toks in tokens.items():
    txt = body_text(entry)
    for t in toks:
        if has_hex(txt,t): hits+=1
        else: miss+=1; misses.append((entry,t))
print("TOTAL hits",hits,"miss",miss)
for e,t in misses: print("MISS",e,t)

# compact key-instruction dump for remaining complex functions
focus = ["004D4DC0","004D5070","004D5350","004D6AA0","004D9290","004DA2C0","004DA530","004DDF90","0051F3E0","005B2FD0","005B3060","005B3570","005B35E0","005B3650","005B36B0"]
for e in focus:
    ins=D.get(e,[])
    print("\n##### "+e+" ins="+str(len(ins)))
    for i in ins:
        m=i["m"]; o=i["o"]
        if m.startswith("j") or m in ("cmp","test","call","ret","sub","dec","inc") or "0x" in o:
            print(i["a"], m, o)
